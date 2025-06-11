import asyncio
import base64
import datetime
import json
import logging
import os
import time
import uuid
from typing import Any, AsyncGenerator
from urllib.parse import urlparse

from browser_use import Agent
from browser_use.browser.context import BrowserContext
from json_repair import repair_json
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from .callbacks import on_task_completed, on_task_start
from .controllers import get_controller
from .models.oai_compatible_models import ChatCompletionStreamResponse

logger = logging.getLogger()

class IncrementID(object):
    def __init__(self, start: int = 1):
        self._it = start - 1
    
    def __call__(self, *args, **kwds):
        self._it += 1
        return self._it

def get_system_prompt(file_name: str = 'system_prompt.txt') -> str:
    import os

    if os.path.exists(file_name):
        with open(file_name, 'r') as fp:
            return fp.read()

    return ''

def repair_json_no_except(json_str: str) -> str:
    try:
        return repair_json(json_str)
    except:
        logger.info(f"failed to repair json string {json_str}")
        return json_str



async def preserve_upload_file(file_data_uri: str, file_name: str) -> str:
    os.makedirs(os.path.join(os.getcwd(), 'uploads'), exist_ok=True)

    file_data_base64 = file_data_uri.split(',')[-1]
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    try:
        file_data = base64.b64decode(file_data_base64)
        file_path = os.path.join(os.getcwd(), 'uploads', f"{timestamp}_{file_name}")
        
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        return file_path
    except Exception as e:
        logger.error(f"Failed to preserve upload file: {e}")
        return None


async def refine_chat_history(messages: list[dict[str, str]], system_prompt: str) -> list[dict[str, str]]:
    refined_messages = []

    has_system_prompt = False
    for message in messages:
        message: dict[str, str]

        if isinstance(message, dict) and message.get('role', 'undefined') == 'system':
            message['content'] += f'\n{system_prompt}'
            has_system_prompt = True
            refined_messages.append(message)
            continue
    
        if isinstance(message, dict) \
            and message.get('role', 'undefined') == 'user' \
            and isinstance(message.get('content'), list):

            content = message['content']
            text_input = ''
            attachments = []

            for item in content:
                if item.get('type', 'undefined') == 'text':
                    text_input += item.get('text') or ''

                elif item.get('type', 'undefined') == 'file':
                    file_item = item.get('file', {})
                    if 'file_data' in file_item and 'filename' in file_item:
                        file_path = await preserve_upload_file(
                            file_item.get('file_data', ''),
                            file_item.get('filename', '')
                        )

                        if file_path:
                            attachments.append(file_path)

            if attachments:
                text_input += '\nAttachments:\n'

                for attachment in attachments:
                    text_input += f'- {attachment}\n'

            refined_messages.append({
                "role": "user",
                "content": text_input
            })

        else:
            refined_messages.append(message)

    if not has_system_prompt and system_prompt != "":
        refined_messages.insert(0, {
            "role": "system",
            "content": system_prompt
        })

    if isinstance(refined_messages[-1], str):
        refined_messages[-1] = {
            "role": "user",
            "content": refined_messages[-1]
        }

    return refined_messages


async def refine_assistant_message(
    assistant_message: dict[str, str]
) -> dict[str, str]:

    if 'content' in assistant_message:
        assistant_message['content'] = assistant_message['content'] or ""

    return assistant_message

def random_uuid() -> str:
    return str(uuid.uuid4())

async def wrap_chunk(uuid: str, raw: str, role="assistant") -> ChatCompletionStreamResponse:
    return ChatCompletionStreamResponse(
        id=uuid,
        object='chat.completion.chunk',
        created=int(time.time()),
        model='unspecified',
        choices=[
            dict(
                index=0,
                delta=dict(
                    content=raw,
                    role=role
                )
            )
        ]
    )

async def to_chunk_data(chunk: ChatCompletionStreamResponse) -> bytes:
    return ("data: " + json.dumps(chunk.model_dump()) + "\n\n").encode()

async def check_authentication_required_email_or_username(ctx: BrowserContext):
    page = await ctx.get_current_page()
    current_url = page.url
    logger.info(f"current_url: {current_url}")

    if 'amazon.com/ap/signin' in current_url:
        input_element = await page.query_selector('#ap_email_login')
        logger.info(f"input_element: {input_element}")

        if input_element:
            value = await input_element.input_value()
            logger.info(f"Condition: {not value.strip()}")
            if not value.strip():
                # raise Exception("Unauthorized access: Email or username is required.")
                raise Exception("Login is required to continue.")
        else:
            # raise Exception("Unauthorized access: Email or username input not found.")
            raise Exception("Login is required to continue.")

async def check_authentication_required_password(ctx: BrowserContext):
    page = await ctx.get_current_page()
    current_url = page.url

    if 'amazon.com/ax/claim' in current_url or 'amazon.com/ap/signin' in current_url:
        input_element = await page.query_selector('#ap_password')
        if input_element:
            value = await input_element.input_value()
            if not value.strip():
                # raise Exception("Unauthorized access: Password is required.")
                raise Exception("Login is required to continue.")
        else:
            # raise Exception("Unauthorized access: Password input not found.")
            raise Exception("Login is required to continue.")
  
async def check_authentication_by_pass_captcha(ctx: BrowserContext):
  page = await ctx.get_current_page()
  if await page.query_selector('#captchacharacters') is not None:
      raise Exception("CAPTCHA challenge detected, manual intervention required.")
  
async def review_checkout_card_empty_delivery(ctx: BrowserContext):
    page = await ctx.get_current_page()
    await asyncio.sleep(2)
    logger.info(f"Review checkout card empty delivery: {page.url}")
    # check if place order button is present and not disabled
    
    # try catch time out, continue if timeout

    # await page.wait_for_selector('#placeOrder', timeout=10000)

    place_order_button = await page.query_selector('#placeOrder')

    logger.info(f"Place order button: {place_order_button}")

    if place_order_button:
        is_disabled = await place_order_button.get_attribute('disabled')
        if not is_disabled:
            await place_order_button.click()
            return
    # Ensure we are on the secure checkout page
    if "amazon.com/checkout" in page.url or "amazon.com/gp/buy" in page.url:
      # Check for delivery address
      address_element = await page.query_selector('#address-book-entry-0, .displayAddressDiv')
      if not address_element:
          # raise Exception("Delivery address is empty.")
          raise Exception("Checkout cannot proceed. Please complete your delivery address and payment details.")

      address_text = await address_element.inner_text()
      if not address_text.strip():
          # raise Exception("Delivery address is empty.")
          raise Exception("Checkout cannot proceed. Please complete your delivery address and payment details.")

      # Check for payment method
      payment_element = await page.query_selector('.payment-information, #payment-information')
      if not payment_element:
          # raise Exception("Payment method is empty.")
          raise Exception("Checkout cannot proceed. Please complete your delivery address and payment details.")

      payment_text = await payment_element.inner_text()
      if not payment_text.strip():
          # raise Exception("Payment method is empty.")
          raise Exception("Checkout cannot proceed. Please complete your delivery address and payment details.")

async def check_browser_current_state(ctx: BrowserContext):
  logger.info(f"Check browser current state start")

  try:
    await check_authentication_required_email_or_username(ctx)

    await check_authentication_required_password(ctx)

    await check_authentication_by_pass_captcha(ctx)

    # await review_checkout_card_empty_delivery(ctx)

  except Exception as e:
    logger.info(f"Check browser current state error: {e}")
    raise e

  logger.info(f"Check browser current state end")


async def is_showing_captcha(ctx: BrowserContext) -> bool:
    try:
        logger.info(f"Check captcha start")
        page = await ctx.get_current_page()
        logger.info(f"Check captcha page: {page.url}")
        if await page.query_selector('#captchacharacters') is not None:
            logger.info(f"Check captcha end: True")
            return True
        else:
            logger.info(f"Check captcha end: False")
            return False
    except Exception as e:
        logger.info(f"Check captcha error: {e}")
        return False

async def browse(task_query: str, ctx: BrowserContext, max_steps: int = 10) -> AsyncGenerator[str, None]:

    controller = get_controller()

    model = ChatOpenAI(
        model=os.getenv("LLM_MODEL_ID", 'local-llm'),
        openai_api_base=os.getenv("LLM_BASE_URL", 'http://localhost:65534/v1'),
        openai_api_key=os.getenv("LLM_API_KEY", 'no-need'),
        temperature=0.0,
    )

    current_agent = Agent(
        task=task_query,
        llm=model,
        browser_profile=ctx.browser_profile,
        browser_session=ctx,
        controller=controller
    )

    res = await current_agent.run(
        max_steps=max_steps,
        on_step_start=on_task_start, 
        on_step_end=on_task_completed
    )

    return res.final_result()

def refine_mcp_response(something: Any) -> str:
    if isinstance(something, dict):
        return {
            k: refine_mcp_response(v)
            for k, v in something.items()
        }

    elif isinstance(something, (list, tuple)):
        return [
            refine_mcp_response(v)
            for v in something
        ]

    elif isinstance(something, BaseModel):
        return something.model_dump()

    return something


def wrap_toolcall_request(uuid: str, fn_name: str, args: dict[str, Any]) -> ChatCompletionStreamResponse:
    args_str = json.dumps(args, indent=2)

    template = f'''
Executing <b>{fn_name}</b>

<details>
<summary>
Arguments:
</summary>

```json
{args_str}
```

</details>
'''

    return ChatCompletionStreamResponse(
        id=uuid,
        object='chat.completion.chunk',
        created=int(time.time()),
        model='unspecified',
        choices=[
            dict(
                index=0,
                delta=dict(
                    content=template,
                    role='tool'
                ),
            )
        ]
    )
    

def wrap_toolcall_response(
    uuid: str,
    fn_name: str,
    args: dict[str, Any],
    result: dict[str, Any]
) -> ChatCompletionStreamResponse:

    data = refine_mcp_response(result)

    try:
        data = json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Failed to JOSN serialize tool call response: {e}")
        data = str(data)


    result = f'''
<details>
<summary>
Response:
</summary>

{data}

</details>
<br>

'''

    return ChatCompletionStreamResponse(
        id=uuid,
        object='chat.completion.chunk',
        created=int(time.time()),
        model='unspecified',
        choices=[
            dict(
                index=0,
                delta=dict(
                    content=result,
                    role='tool'
                ),
            )
        ]
    )
    
    
    
def ensure_page_url(link: str):
    import functools
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(ctx: BrowserContext, **args):
            page = await ctx.get_current_page()
            current_url = page.url
            logger.info(f"Current URL: {current_url}")
            logger.info(f"Link: {link}")
            if current_url != link:
                await page.goto(link)
                await page.wait_for_load_state('domcontentloaded')
            result = func(ctx, **args)
            if hasattr(result, "__aiter__"):
                async for item in result:
                    yield item
            else:
                await result  # just await, do not return a value
        return wrapper
    return decorator

def normalize_url(url):
    parsed = urlparse(url)
    # Only keep scheme, netloc, and path (ignore query and fragment)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
