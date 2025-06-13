## Core Functionality - Server Setup and Request Handling (`server.py`)

The `server.py` file is the backbone of the `amazon-agent`, responsible for setting up the web server, managing the intricate lifecycle of the browser and its virtual display environment, and handling incoming user requests.

### FastAPI Application Initialization

The server uses FastAPI, a modern Python web framework, for building its API:

```python
import fastapi
# ...
api_app = fastapi.FastAPI(lifespan=lifespan)
```
The `lifespan` argument points to an asynchronous context manager that handles setup and teardown operations for the application.

### Key API Endpoints

1.  **`/prompt` (POST)**: This is the primary endpoint for users to interact with the agent.
    *   **Request Handling**: It accepts a JSON payload in the request body. This payload should contain a `messages` array (representing the conversation history) and can include other optional parameters.
        ```python
        @api_app.post("/prompt", response_model=None)
        async def post_prompt(body: dict) -> Union[StreamingResponse, PlainTextResponse, JSONResponse]:
            messages: list[dict[str, str]] = body.pop('messages', [])
        ```
    *   **Validation**: Basic validation is performed to ensure that the `messages` list is not empty.
    *   **Agent Interaction**: The endpoint then calls the `prompt` function (imported from `app.agent`) with the processed messages and the global browser context (`_GLOBALS["browser_context"]`). This `prompt` function from `app.agent` is responsible for the core agent logic, including LLM interaction and tool execution.
        ```python
        stream = app.prompt( # app here refers to the imported module
            messages,
            browser_context=_GLOBALS["browser_context"],
            **body
        )
        ```
    *   **Streaming Response**: The endpoint returns a `StreamingResponse`. A utility function `stream_reader` wraps the asynchronous generator returned by `app.prompt` to format the output as a stream of Server-Sent Events (SSE), suitable for real-time communication with the client.
        ```python
        return StreamingResponse(
            stream_reader(stream),
            media_type="text/event-stream"
        )
        ```

2.  **`/processing-url` (GET)**: This endpoint provides a way for users to find out where they can view the browser being automated by the agent.
    *   **Purpose**: It returns the URL for the noVNC interface, which allows viewing and interacting with the browser running inside the Docker container's virtual X11 display.
    *   **URL Construction**: The URL is typically sourced from an environment variable `HTTP_DISPLAY_URL`, with a default fallback.
        ```python
        @api_app.get("/processing-url")
        async def get_processing_url():
            http_display_url = os.getenv("HTTP_DISPLAY_URL", "http://localhost:6080/vnc.html?...")
            # ... returns JSONResponse with this URL
        ```

### Lifespan Management (`lifespan` context manager)

The `lifespan` asynchronous context manager is crucial for managing resources throughout the application's lifecycle. It ensures that necessary services are started before the application begins handling requests and are cleaned up properly upon shutdown.

*   **Setup Phase (before `yield`)**:
    *   **Directory Creation**: Ensures essential X11 socket directories (`/tmp/.X11-unix`, `/tmp/.ICE-unix`) and the browser profile directory (`BROWSER_PROFILE_DIR`) exist.
    *   **Background Processes**: It launches several background processes critical for the browser's graphical environment using the `observe_process` utility (which handles auto-restarting if needed):
        *   `Xvfb`: Starts the X Virtual Framebuffer to create a virtual display.
        *   `openbox`: Runs the Openbox window manager within Xvfb.
        *   `bash scripts/x11-setup.sh`: Executes a shell script for further X11 environment configuration.
        *   `x11vnc`: Starts the VNC server, making the Xvfb session accessible.
        *   `novnc_proxy`: Starts the noVNC proxy, allowing web browser access to the VNC session.
    *   **Browser Profile Cleanup**: Removes potentially problematic old browser profile files (like `SingletonLock`, `SingletonCookie`) to ensure a clean start.
    *   **Browser Initialization**:
        *   Initializes a `BrowserSession` and a `BrowserContext` from the `browser_use` library (a Playwright wrapper). These are stored in a global dictionary `_GLOBALS` for access by request handlers.
        *   The browser is configured with specific window sizes and user data directory.
        *   The initial page is navigated to `AMAZON_URL`, and there's logic to handle potential CAPTCHAs upon this initial load.
            ```python
            browser = BrowserSession(...)
            ctx = await browser.new_context()
            _GLOBALS['browser'] = browser
            _GLOBALS['browser_context'] = ctx
            await _GLOBALS['browser_context'].__aenter__()
            current_page = await ctx.get_current_page()
            await current_page.goto(AMAZON_URL)
            if await is_showing_captcha(ctx):
                await current_page.reload()
            ```
    *   The `yield` statement then allows the FastAPI application to run and handle requests.

*   **Teardown Phase (in `finally` block)**: This code executes when the application is shutting down.
    *   **Browser Context Closure**: The `BrowserContext` is properly closed.
    *   **Signal Stoppage**: An `app_signal` (an `asyncio.Event`) is set, signaling the `observe_process` tasks to terminate the background processes (Xvfb, VNC, etc.).
    *   **Process Cleanup**: Explicitly kills any remaining Chromium processes to ensure a clean shutdown.

### Middleware

`CORSMiddleware` is added to the FastAPI application to allow cross-origin requests, making the API accessible from web applications running on different domains.

```python
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # ... other CORS parameters
)
```

### Application Server (Uvicorn)

The `main()` function in `server.py` configures and runs the FastAPI application using `uvicorn`, an ASGI server suitable for production.

```python
if __name__ == '__main__':
    main() # which contains:
    # config = uvicorn.Config(...)
    # server = uvicorn.Server(config)
    # event_loop.run_until_complete(server.serve())
```

This comprehensive setup in `server.py` ensures that the `amazon-agent` not only serves its API but also robustly manages the complex environment required for browser automation within a container.
