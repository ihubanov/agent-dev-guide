## Directory Structure

The `examples/amazon-agent/` directory is structured to separate concerns, with distinct areas for server logic, core agent functionality, browser automation specifics, and supporting utilities.

*   **`server.py`**: This is the main entry point of the `amazon-agent`. It sets up the FastAPI web application, which provides the API endpoints (like `/prompt`) for interacting with the agent. Critically, `server.py` also manages the lifecycle of the browser instance (using the `browser_use` library, likely a Playwright wrapper) and orchestrates the X11, Xvfb, and VNC processes necessary for running a headed browser in a headless environment and allowing remote viewing.

*   **`app/`**: This directory contains the core application logic for the agent.
    *   **`__init__.py`**: An empty file that makes the `app` directory a Python package.
    *   **`agent.py`**: Houses the primary agent logic. This includes interacting with the Large Language Model (LLM) via the OpenAI library, managing the multi-turn conversation flow, determining which tools to call based on LLM responses, and executing those tools. It differentiates between "shopping_browsing" tools and "purchase_management" tools.
    *   **`callbacks.py`**: Defines callback functions like `on_task_start` and `on_task_completed`. These are likely used as hooks by the `browser_use.Agent` (seen in `app/utils.py`) for specific browser automation tasks, allowing custom logic to be executed at different stages of an automated task.
    *   **`config.py`**: Contains application-level configuration constants, such as the `AMAZON_URL`.
    *   **`controllers.py`**: Configures and provides a `Controller` instance from the `browser_use` library. This controller likely defines or filters the set of built-in browser interaction actions (e.g., 'click', 'type', 'scroll') available to the `browser_use.Agent`.
    *   **`models/`**: This sub-directory contains Pydantic data models.
        *   **`__init__.py`**: Makes `models` a Python package.
        *   **`browser_use_custom_models.py`**: Defines custom models like `RunningStatus` and `FinalAgentResult`, likely used by the `browser_use.Agent` to structure its final output or report status.
        *   **`oai_compatible_models.py`**: A comprehensive set of Pydantic models ensuring compatibility with the OpenAI API spec. This includes structures for chat completion requests, responses, streaming chunks, tool calls, error messages, and usage information. These models are vital for robust communication with the LLM.
    *   **`tool_impl.py`**: Contains the actual Python implementations of the custom tools that the agent can use (e.g., `search_products`, `add_to_cart`, `check_out`). These functions typically involve direct browser manipulation using the Playwright context.
    *   **`tools.py`**: Defines the schemas (name, description, parameters) of all tools available to the LLM. This structured definition allows the LLM to understand when and how to request the execution of a specific tool.
    *   **`utils.py`**: A collection of utility functions used across the application. This includes functions for refining chat history, formatting messages for streaming, handling file uploads, checking browser states (like CAPTCHAs or login prompts), and a `browse` function that seems to employ a higher-level `browser_use.Agent` for certain tasks.

*   **`scripts/`**: This directory holds shell scripts.
    *   **`x11-setup.sh`**: A script used to configure the X11 environment within the Docker container, ensuring the graphical components for browser display can run correctly. It's invoked during the startup sequence in `server.py`.

*   **`system_prompt.txt`**: A text file containing the default system prompt used to instruct the LLM on its role, capabilities, and expected behavior as an Amazon shopping assistant.

*   **`Dockerfile`**: Provides the instructions to build the Docker image for the `amazon-agent`. It details the setup of the Python environment, installation of system packages (like Xvfb, x11vnc, Openbox), Playwright with its browser dependencies, Python package dependencies, and configures the container's runtime environment (environment variables, entrypoint).

*   **`requirements.txt`**: Lists the main Python dependencies required for the agent to run (e.g., `fastapi`, `uvicorn`, `openai`, `playwright`, `python-dotenv`).
*   **`requirements.base.txt`**: Likely contains a base set of dependencies, possibly for the core browser automation setup or other foundational libraries. Playwright browser installation is also triggered based on this.

*   **`.env.example`**: An example file showing the environment variables that can be set to configure the agent (e.g., `LLM_BASE_URL`, `LLM_API_KEY`, `DISPLAY`, VNC ports).

*   **`README.md`**: The primary documentation file for the `amazon-agent`, offering guidance on setup, prerequisites, building and running the Docker container, and testing the agent.

This structure separates the web server, agent core, tool definitions, browser interaction logic, and configuration, aiming for a modular and maintainable codebase.
