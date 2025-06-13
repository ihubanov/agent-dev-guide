## Technology Stack

The `amazon-agent` leverages a combination of technologies to enable its AI-driven browser automation capabilities, API server, and operational environment. The core components include:

*   **Python**: The primary programming language used for developing the agent's logic, server, and automation scripts. The project structure is predominantly based on Python files (`.py`).

*   **FastAPI**: A modern, high-performance Python web framework used to build the agent's API server. This is evident from `server.py`, which imports `fastapi` and uses it to define endpoints like `/prompt`. FastAPI handles incoming HTTP requests and routes them to the appropriate agent logic.

*   **Playwright**: A powerful Python library for browser automation. Playwright is used to control a web browser (Chromium in this case) programmatically. This allows the agent to navigate web pages, interact with elements (like clicking buttons or filling forms), and extract information from websites like Amazon. Its use is indicated by installations in the `Dockerfile` (e.g., `patchright install chromium`) and browser session management in `server.py` via the `browser_use` library, which is a wrapper around Playwright.

*   **OpenAI Python Library**: The official Python client library for interacting with OpenAI API compatible Large Language Models (LLMs). The agent uses this library (as seen in `app/agent.py` with `import openai`) to send requests to an LLM, which then determines the sequence of actions (tool calls) based on the user's prompt.

*   **Docker**: Used for containerization, Docker plays a crucial role in packaging the `amazon-agent` along with all its complex dependencies (Python, Playwright, browser, X11/VNC components, etc.) into a portable image. The `Dockerfile` defines the steps to build this image, ensuring a consistent runtime environment across different systems.

*   **X11 (Xvfb), Openbox, x11vnc, noVNC**: This suite of tools creates a virtual graphical environment within the Docker container, necessary for running a browser in a headless server environment while still allowing for visual inspection and debugging:
    *   **Xvfb (X Virtual Framebuffer)**: Provides an in-memory X server, allowing graphical applications (like a web browser) to run without a physical display. (Installed in `Dockerfile`, configured in `server.py`)
    *   **Openbox**: A lightweight window manager used within the Xvfb session. (Installed in `Dockerfile`, configured in `server.py`)
    *   **x11vnc**: A VNC server that makes the Xvfb display accessible over the network via the VNC protocol. (Installed in `Dockerfile`, configured in `server.py`)
    *   **noVNC**: A web-based VNC client that allows users to connect to the VNC server (and thus view/interact with the browser) from their own web browser. (Cloned and set up in `Dockerfile`, configured in `server.py`)

This stack enables the `amazon-agent` to receive user commands through an API, use an LLM to interpret these commands, and then execute them by automating a web browser within a controlled, virtualized environment.
