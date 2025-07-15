# Prompt Based Agent

This is not ChatGPT, this is a simple example to demonstrate how to write a **CryptoAgent** with local LLM, tool-calls supported, smart like ChatGPT by OpenAI :D.

## Components

There are three key components in this source code.

### The agent gateway

Every CryptoAgent is deployed an run as a http server with endpoint `/prompt` exposed (for the most basic prompt-based agent). The body to execute `/prompt` follows the standard of v1 chat completions by [OpenAI](https://platform.openai.com/docs/api-reference/chat/create).

### Main logic of the /prompt

The flow to process a request to generate an answer starts from the function `app.apis.handle_request`. However, the current implementation follows the best practice by the EternalAI team. Contributing to this part is still welcome, but if you want to rapidly deploy an agent yourself, we recommend focus on building tool calls for the agent!

### Tool-calls

To quickly define a tool call that can be executed by LLM, focus on the file `app.tools`. Every tool call here is defined with MCP (model context protocol) standard, uses [MCP-Python SDK](https://github.com/modelcontextprotocol/python-sdk). From here, to customize your agent, just follow the current implementations, write new tools, and remove the un-nessessaries.

This is an example:

```python
import ast
from fastmcp import FastMCP 

python_toolkit = FastMCP(name="Python-Toolkit")
web_toolkit = FastMCP(name="Web-Toolkit")

def limit_resource(memory_limit: int, cpu_limit: int):
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
    resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))

@python_toolkit.tool(
    name="run",
    description="Run Python code. Return the result of the code and all declared variables. Use this toolcall for complex tasks like math solving, data analysis, etc.",
    annotations={
        "code": "The Python code to execute",
    }
)
async def python_interpreter(code: str) -> str:
    variables = []
    tree = ast.parse(code)

    current_interpreter = sys.executable

    result = await asyncio.to_thread(
        subprocess.check_output, 
        [current_interpreter, "-c", code],
        preexec_fn=lambda: limit_resource(100 * 1024 * 1024, 10),
        timeout=30
    )

    return result.decode("utf-8")

@web_toolkit.tool(
    name="search",
    description="Search the web for a given query. Return real-time related information.",
    annotations={
        "query": "The query to search the web for",
        "lang": "The language code of the query",
    }
)
async def search_web(query: str, lang: str = "en") -> list[AdvanceSearchResult | SearchResult]:
    results = list(search(
        query, 
        sleep_interval=5, 
        advanced=True, 
        lang=lang, 
        num_results=10,
    ))
    
    return results

# at the end, to include your tool-calls to be visible with the LLM, just register it
compose = FastMCP(name="Compose")
compose.mount("python", python_toolkit)
compose.mount("web", web_toolkit)

# the `compose` MCP will be imported and used in the apis.py, in the main workflow  
```

### Other Stuff

To customize the agent system prompt or personality, just modify the `system_prompt.txt` file. The current system prompt instructs the agent to:
- Use the bio tool to remember user information
- Execute Python code for mathematical problems
- Use web tools for real-time information
- Be honest when tools can't help

**Note:**
- The `greeting.txt` file is shown to users the first time they start a new conversation. You can customize this file to change the initial greeting message.

## Debugging

Python 3.10+ is recommended.

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration**
   Create a `.env` file or set environment variables:
   ```bash
   LLM_API_KEY=your-api-key
   LLM_BASE_URL=http://your-llm-endpoint/v1
   LLM_MODEL_ID=your-model-name
   HOST=0.0.0.0
   PORT=80
   APP_ENV=development
   ```

3. **Test Individual Components**
   - Use `debug.py` to test Python code parsing and AST analysis
   - Use `test.py` to test streaming responses and concurrent requests
   - Check tool functionality by importing and calling tools directly

4. **Monitor Logs**
   The application logs important events including:
   - Request processing times (TTFT, TPS)
   - Tool call executions and results
   - Memory/bio operations
   - API payload information

## Deployment

To package your agent for deployment, simply run:

```bash
bash pack.sh
````

After the script finishes, a file named `package.zip` will be created in the current folder.

Next, visit [eternalai.org](https://eternalai.org/your-agents), connect your wallet, and create a GigaBrain agent.