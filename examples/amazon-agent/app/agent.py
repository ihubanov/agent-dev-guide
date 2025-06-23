import json
import logging
import os
import traceback
from typing import AsyncGenerator

import httpx
import openai
from browser_use.browser.context import BrowserContext

from .config import AMAZON_URL
from .models import oai_compatible_models
from .tool_impl import (add_to_cart, check_out, get_order_history,
                        get_product_detail, search_products, cancel_order, request_refund, go_to_cart, adjust_cart)
from .tools import get_functions
from .utils import (get_system_prompt, random_uuid,
                    refine_assistant_message, refine_chat_history,
                    to_chunk_data, wrap_toolcall_request, wrap_toolcall_response, refine_mcp_response)

logger = logging.getLogger()

# Shopping & Product Browsing Agent: Handles product exploration and cart management
shopping_browsing_tool_function_map = {
    "search_products": search_products,
    "get_product_detail": get_product_detail,
    "add_to_cart": add_to_cart,
    "go_to_cart": go_to_cart,
    "adjust_cart": adjust_cart,
    "check_out": check_out
}

# Purchase Management Agent: Handles checkout and post-purchase actions
purchase_management_tool_function_map = {
    "get_order_history": get_order_history,
    "cancel_order": cancel_order,
    "request_refund": request_refund,
}

# Helper to determine which agent should handle a tool call
def get_agent_for_tool(tool_name: str) -> str:
    if tool_name in shopping_browsing_tool_function_map:
        return "shopping_browsing"
    elif tool_name in purchase_management_tool_function_map:
        return "purchase_management"
    return "unknown"

async def execute_openai_compatible_toolcall(
    ctx: BrowserContext,
    name: str,
    args: dict[str, str],
    agent_type: str
) -> AsyncGenerator[str, None]:
    logger.info(f"Executing tool call: {name} with args: {args} for agent: {agent_type}")
    if agent_type == "shopping_browsing":
        tool_func = shopping_browsing_tool_function_map.get(name)
    elif agent_type == "purchase_management":
        tool_func = purchase_management_tool_function_map.get(name)
    else:
        tool_func = None
    if tool_func is not None:
        async for msg in tool_func(ctx, **args):
            yield msg
        return
    yield f"Unknown tool call: {name}; Available tools are: {list(shopping_browsing_tool_function_map.keys()) + list(purchase_management_tool_function_map.keys())}"

async def prompt(messages: list[dict[str, str]], browser_context: BrowserContext, **_) -> AsyncGenerator[str, None]:
    page = await browser_context.get_current_page()
    current_url = page.url
    
    if not current_url.startswith(AMAZON_URL):
        await page.goto(AMAZON_URL)
        await page.wait_for_load_state('load', timeout=10000)

    functions = get_functions()

    # Helper to clean environment variables (strip quotes and handle empty values)
    def clean_env_var(var, default):
        val = os.getenv(var)
        if val:
            return val.strip('"\'') or default
        return default

    llm = openai.AsyncClient(
        base_url=clean_env_var("LLM_BASE_URL", "http://localmodel:65534/v1"),
        api_key=clean_env_var("LLM_API_KEY", "no-need"),
        max_retries=3
    )

    messages = await refine_chat_history(messages, get_system_prompt())
    
    response_uuid = random_uuid()
    error_details = ''
    error_message = ''
    calls = 0
    previous_agent = None

    try:
        completion = await llm.chat.completions.create(
            model=clean_env_var("LLM_MODEL_ID", 'local-llm'),
            messages=messages,
            tools=functions,
            tool_choice="auto",
            seed=42,
            temperature=0.0
        )
        
        if completion.choices[0].message.content:
            yield completion.choices[0].message.content

        messages.append(await refine_assistant_message(completion.choices[0].message.model_dump()))

        while completion.choices[0].message.tool_calls is not None and len(completion.choices[0].message.tool_calls) > 0:
            calls += len(completion.choices[0].message.tool_calls)
            executed = set([])
            
            for call in completion.choices[0].message.tool_calls:
                _id, _name = call.id, call.function.name    
                _args = json.loads(call.function.arguments)
                agent_type = get_agent_for_tool(_name)
                result, has_exception = '', False

                # Handoff logic
                if previous_agent and agent_type != previous_agent and agent_type != "unknown":
                    if agent_type == "purchase_management":
                        messages.append({"role": "system", "content": "You are a purchase management agent. You are responsible for managing the purchase of a product. You are not allowed to search for products or add them to the cart."})
                    elif agent_type == "shopping_browsing":
                        messages.append({"role": "system", "content": "You are a shopping browsing agent. You are responsible for browsing the product and adding them to the cart."})
                previous_agent = agent_type

                identity = _name + call.function.arguments
                
                logger.info(f"messages: {messages}")
                logger.info(f"previous_agent: {previous_agent}")
                logger.info(f"agent_type: {agent_type}")
                logger.info(f"identity: {identity}")

                if identity in executed:
                    result = f"Tool call `{_name}` has been executed before with the same arguments: {_args}. Skipping"

                elif has_exception:
                    result = f"Exception raised. Skipping task...\n"

                else:
                    executed.add(identity)

                    yield await to_chunk_data(wrap_toolcall_request(
                        uuid=response_uuid,
                        fn_name=_name,
                        args=_args
                    )
                    )

                    try:
                        async for msg in execute_openai_compatible_toolcall(
                            ctx=browser_context, 
                            name=_name,
                            args=_args,
                            agent_type=agent_type
                        ):
                            yield await to_chunk_data(
                                wrap_toolcall_response(
                                    uuid=response_uuid,
                                    fn_name=_name,
                                    args=_args,
                                    result=msg
                                )
                            )
                           
                            if isinstance(msg, str):
                                result += msg + '\n'

                    except Exception as e:
                        logger.error(f"{e}", exc_info=True)
                        result = f"Something went wrong, {e}. After then, Re-execute {_name} with these arguments: {_args}" 

                        yield await to_chunk_data(
                            wrap_toolcall_response(
                                uuid=response_uuid,
                                fn_name=_name,
                                args=_args,
                                result=result
                        )
                        )
                        has_exception = True

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": _id,
                        "content": json.dumps(refine_mcp_response(result))
                    }
                )

                if has_exception:
                    break 

            need_toolcalls = calls < 10 and not has_exception

            completion = await llm.chat.completions.create(
                messages=messages,
                model=clean_env_var("LLM_MODEL_ID", 'local-llm'),
                tools=functions if need_toolcalls else openai._types.NOT_GIVEN,  # type: ignore
                tool_choice="auto" if need_toolcalls else openai._types.NOT_GIVEN,  # type: ignore
                seed=42,
                temperature=0.0
            )

            logger.info(f"Assistant: {completion.choices[0].message.content!r}")

            if completion.choices[0].message.content:
                yield completion.choices[0].message.content

            messages.append(await refine_assistant_message(completion.choices[0].message.model_dump()))
      
    except openai.APIConnectionError as e:
        error_message=f"Failed to connect to language model: {e}"
        error_details = traceback.format_exc(limit=-6)

    except openai.RateLimitError as e:
        error_message=f"Rate limit error: {e}"

    except openai.APIError as e:
        error_message=f"Language model returned an API Error: {e}"

    except httpx.HTTPStatusError as e:
        error_message=f"HTTP status error: {e}"
        
    except Exception as e:
        error_message=f"Unhandled error: {e}"
        error_details = traceback.format_exc(limit=-6)
        
    finally:
        if error_message:

            logger.error(f"Error occurred: {error_message}")
            logger.error(f"Error details: {error_details}")

            yield await to_chunk_data(
                oai_compatible_models.PromptErrorResponse(
                    message=error_message, 
                    details=error_details
                )
            )
