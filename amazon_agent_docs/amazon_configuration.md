## Configuration

The `amazon-agent` is configured through a combination of environment variables (for runtime and service connections) and dedicated Python configuration files (for application-specific constants).

### Environment Variables

Environment variables are the primary method for configuring the agent's operational parameters, especially those related to external services, network settings, and the browser's virtual display environment.

1.  **Loading via `dotenv`**:
    *   In `server.py`, the `dotenv` library is used to load environment variables from a `.env` file located in the agent's root directory.
        ```python
        # In server.py
        from dotenv import load_dotenv
        if not load_dotenv():
            logger.warning("amazon-agent, .env not found")
        ```
    *   This allows users to easily set up their local environment without hardcoding values into the source or Docker image. If a `.env` file is not found, the agent will rely on variables already present in the environment (e.g., set in the Docker container or system-wide).

2.  **`.env.example` File**:
    *   The project includes an `.env.example` file. This file serves as a template, listing the environment variables that the application recognizes and often providing default or example values. Users should copy this to a `.env` file and customize it with their specific settings (e.g., API keys, preferred ports).

3.  **Key Environment Variables**:
    Many environment variables are defined in the `Dockerfile` (setting defaults for the container) and used within `server.py` or `app/agent.py`. Key variables include:

    *   **LLM Connection**:
        *   `LLM_BASE_URL`: The base URL for the OpenAI-compatible LLM API. (Default: `http://localmodel:65534/v1`)
        *   `LLM_API_KEY`: The API key for authenticating with the LLM. (Default: `no-need` or `unknown`)
        *   `LLM_MODEL_ID`: The specific model identifier to be used for chat completions. (Default: `model-name` or `unknown`)

    *   **X11 Display Settings (for Xvfb and browser UI within container)**:
        *   `DISPLAY`: The X11 display number. (Default: `:99`)
        *   `XDG_SESSION_TYPE`: Typically set to `x11`.
        *   `GDK_SCALE`, `GDK_DPI_SCALE`: For UI scaling within the X11 environment.
        *   `BROWSER_WINDOW_SIZE_WIDTH`, `BROWSER_WINDOW_SIZE_HEIGHT`: Define the virtual screen resolution for Xvfb and the browser window. (Defaults e.g., `1440x1080` or `1440x1440`)
        *   `SCREEN_COLOR_DEPTH_BITS`: Color depth for the Xvfb screen. (Default: `24`)

    *   **Network Ports**:
        *   `NO_VNC_PORT`: The port on which the noVNC web client proxy will listen, providing browser-based VNC access. (Default: `6080`)
        *   `CHROME_DEBUG_PORT`: Port for Chrome's debugging protocol, if enabled. (Default: `9222`)
        *   `PORT`: The port on which the FastAPI server for the agent will listen. (Default: `80` inside container, often mapped to `8000` on host)
        *   `HOST`: The host address the FastAPI server binds to. (Default: `0.0.0.0`)

    *   **VNC Access URL**:
        *   `HTTP_DISPLAY_URL`: The full URL (including scheme, host, port, and path) that users can access to view the browser via noVNC. This is returned by the `/processing-url` endpoint. (Default: `http://localhost:6080/vnc.html?autoconnect=true...`)

    *   **Miscellaneous**:
        *   `IN_DOCKER`: A flag indicating the agent is running inside Docker, which might enable/disable certain behaviors. (Default: `1`)

### Application Configuration (`app/config.py`)

For constants that are more intrinsic to the application's domain logic and less frequently changed than runtime environment variables, the `amazon-agent` uses `app/config.py`.

*   **Purpose**: This file defines variables like target URLs for websites the agent interacts with.
    ```python
    # In app/config.py
    AMAZON_URL = "https://www.amazon.com"
    GOOGLE_URL = "https://google.com"
    ```
*   **Usage**: These constants are imported and used by various parts of the application, for instance, in `server.py` to navigate the browser to the initial Amazon page, or potentially by tool implementations in `app/tool_impl.py` to ensure they are operating on the correct domain.

This dual approach to configuration provides flexibility: environment variables for runtime adaptability and Python constants for stable, application-specific settings.
