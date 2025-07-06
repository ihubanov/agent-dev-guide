# TheTroubleMaker Agent

This is a specialized agent based on the prompt-based-agent example that includes additional functionality for searching data leaks using an OSINT search service. The agent can search for emails, names, phone numbers, and other personal information in leaked databases.

## Components

There are four key components in this source code.

### The agent gateway

Every CryptoAgent is deployed an run as a http server with endpoint `/prompt` exposed (for the most basic prompt-based agent). The body to execute `/prompt` follows the standard of v1 chat completions by [OpenAI](https://platform.openai.com/docs/api-reference/chat/create).

### Main logic of the /prompt

The flow to process a request to generate an answer starts from the function `app.apis.handle_request`. However, the current implementation follows the best practice by the EternalAI team. Contributing to this part is still welcome, but if you want to rapidly deploy an agent yourself, we recommend focus on building tool calls for the agent!

### Tool-calls

To quickly define a tool call that can be executed by LLM, focus on the file `app.tools`. Every tool call here is defined with MCP (model context protocol) standard, uses [MCP-Python SDK](https://github.com/modelcontextprotocol/python-sdk). From here, to customize your agent, just follow the current implementations, write new tools, and remove the un-nessessaries.

This agent includes the following toolkits:

1. **Python-Toolkit**: For executing Python code and mathematical calculations
2. **Web-Toolkit**: For web searching and scraping
3. **Bio-Toolkit**: For managing user information and memory
4. **Leakosint-Toolkit**: For searching data leaks (NEW!)

### OSINT Search Service Integration

The agent includes specialized tools for searching data leaks:

#### `leakosint_search_leak`
- Search for emails, names, phone numbers, and other personal information
- Parameters: request, limit (100-10000), lang, type
- Returns structured data about found leaks

#### `leakosint_batch_search_leak`
- Perform multiple searches in a single API request
- Parameters: requests (list), limit, lang, type
- Efficient for searching multiple items

### API Cost Calculation

The OSINT search service uses the following pricing formula:
```
Cost = (5 + sqrt(Limit * Complexity)) / 5000 USD
```

Where:
- **Limit**: Search limit (100-10000)
- **Complexity**: Based on word count:
  - 1 word: Complexity = 1
  - 2 words: Complexity = 5
  - 3 words: Complexity = 16
  - 4+ words: Complexity = 40

**Note**: Dates, lines shorter than 4 characters, and numbers shorter than 6 characters are excluded from complexity calculation.

### Other Stuff

To customize the agent system prompt or personality, just modify the `system_prompt.txt` file. The current system prompt instructs the agent to:
- Use the bio tool to remember user information
- Execute Python code for mathematical problems
- Use web tools for real-time information
- Use OSINT search tools for data leak searches
- Be honest when tools can't help

## Debugging

Python 3.10+ is recommended.

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration**
   Create a `.env` file or set environment variables:
   ```bash
   # LLM Configuration
   LLM_API_KEY=your-llm-api-key
   LLM_BASE_URL=http://your-llm-endpoint/v1
   LLM_MODEL_ID=your-model-name
   
   # OSINT Search Service Configuration (REQUIRED)
   LEAKOSINT_API_KEY=your-osint-service-token
   
   # Server Configuration
   HOST=0.0.0.0
   PORT=80
   APP_ENV=development
   ```

   **Note**: The `LEAKOSINT_API_KEY` is **REQUIRED** for the OSINT search functionality. Users do not need to provide any API keys - the service is configured transparently by the administrator.

3. **Test Individual Components**
   - Use `debug.py` to test Python code parsing and AST analysis
   - Use `test.py` to test streaming responses and concurrent requests
   - Use `test_leakosint.py` to test OSINT search functionality
   - Check tool functionality by importing and calling tools directly

4. **Monitor Logs**
   The application logs important events including:
   - Request processing times (TTFT, TPS)
   - Tool call executions and results
   - Memory/bio operations
   - API payload information

## Deployment

Just zip your source code, including the Dockerfile. Go to [eternalai.org](https://eternalai.org/your-agents), connect your wallet and create an GigaBrain agent. 

## Usage Examples

### Basic Data Leak Search
```
User: "Search for leaks related to john.doe@example.com"
Agent: [Uses leakosint_search_leak tool to search for the email]
```
### Batch Search
```
User: "Search for these emails: user1@example.com, user2@example.com, user3@example.com"
Agent: [Uses leakosint_batch_search_leak to search all emails at once]
```

### Administrator Setup
The OSINT search service requires administrator configuration:

```bash
# Set the required API key for the OSINT search service
export LEAKOSINT_API_KEY="your-osint-service-token"

# Or add to .env file
echo "LEAKOSINT_API_KEY=your-osint-service-token" >> .env
```

Users can then search for data leaks without any knowledge of the underlying API or service.

