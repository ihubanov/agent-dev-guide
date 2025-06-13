## Packaging and Deployment (`Dockerfile`)

The `amazon-agent` is designed to be deployed as a Docker container, which encapsulates all its dependencies, including the Python runtime, browser, virtual display environment, and the agent's code. The `examples/amazon-agent/Dockerfile` provides the blueprint for building this container image.

Let's break down the key stages and instructions in the `Dockerfile`:

1.  **Base Image**:
    ```dockerfile
    FROM python:3.12-slim
    ```
    The image starts with `python:3.12-slim`, a lightweight official Python image, providing the necessary Python runtime environment.

2.  **Environment Setup for Package Installation**:
    ```dockerfile
    ENV DEBIAN_FRONTEND=noninteractive
    ```
    This environment variable is set to prevent interactive dialogs during APT package installations, ensuring the build process can run unattended.

3.  **APT Package Installation**:
    ```dockerfile
    RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        xvfb \
        x11vnc \
        openbox \
        procps \
        xdg-utils \
        x11-xserver-utils \
        && rm -rf /var/lib/apt/lists/*
    ```
    This crucial step installs system-level packages required for:
    *   `git`: For cloning repositories (like noVNC).
    *   `xvfb`: X Virtual Framebuffer, to run a display server in memory.
    *   `x11vnc`: A VNC server to make the Xvfb session accessible.
    *   `openbox`: A lightweight window manager for the X11 session.
    *   Utilities like `procps` (for process management), `xdg-utils`, and `x11-xserver-utils`.

4.  **noVNC Setup**:
    ```dockerfile
    RUN git clone https://github.com/novnc/noVNC.git /opt/novnc && \
        git clone https://github.com/novnc/websockify /opt/novnc/utils/websockify && \
        chmod +x /opt/novnc/utils/novnc_proxy
    ```
    This section downloads and sets up noVNC, a web-based VNC client. It clones the `noVNC` repository and its `websockify` dependency (for WebSocket proxying) into `/opt/novnc`. This enables users to connect to the agent's VNC session from their web browser.

5.  **Python Dependencies Installation**:
    ```dockerfile
    COPY requirements.txt requirements.base.txt .
    ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
    ENV PIP_ROOT_USER_ACTION=ignore
    RUN pip install -r requirements.base.txt && patchright install chromium --no-shell --with-deps
    RUN pip install -r requirements.txt
    ```
    *   `requirements.txt` and `requirements.base.txt` are copied into the image.
    *   `PLAYWRIGHT_BROWSERS_PATH` is set to define where Playwright's browsers will be stored.
    *   `PIP_ROOT_USER_ACTION=ignore` avoids issues with pip running as root.
    *   `requirements.base.txt` is installed first. The command `patchright install chromium --no-shell --with-deps` (where `patchright` is often an alias or script related to Playwright) installs the Chromium browser and its necessary system dependencies for Playwright to use.
    *   Then, `requirements.txt` is installed, containing the agent's specific Python package dependencies (like `fastapi`, `openai`, `playwright`).

6.  **Application Code Setup**:
    ```dockerfile
    WORKDIR /workspace
    COPY app app
    COPY system_prompt.txt system_prompt.txt
    COPY server.py server.py
    COPY scripts scripts
    ```
    The working directory inside the container is set to `/workspace`. The agent's application code (the `app` directory, `system_prompt.txt`, `server.py`, and `scripts/`) is copied into this workspace.

7.  **Port Exposure**:
    ```dockerfile
    EXPOSE 6080
    EXPOSE 80
    ```
    *   Port `6080` is exposed for the noVNC web client access.
    *   Port `80` is exposed for the FastAPI application server.

8.  **Runtime Environment Variables**:
    A series of `ENV` instructions set up default environment variables crucial for the agent's runtime:
    *   X11/VNC related: `DISPLAY`, `XDG_SESSION_TYPE`, `GDK_SCALE`, `GDK_DPI_SCALE`, `BROWSER_WINDOW_SIZE_WIDTH`, `BROWSER_WINDOW_SIZE_HEIGHT`, `SCREEN_COLOR_DEPTH_BITS`, `NO_VNC_PORT`, `CHROME_DEBUG_PORT`. These configure the virtual display and VNC server.
    *   LLM Connection: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL_ID` provide default connection parameters for the Language Model.
    *   `IN_DOCKER=1`: A flag that can be used by the application to know it's running within a Docker container.

9.  **Entrypoint**:
    ```dockerfile
    ENTRYPOINT ["python", "-O", "server.py"]
    ```
    This defines the command that will run when the container starts. It executes `server.py` using `python -O` (which enables basic optimizations by removing assert statements and `__debug__` checks).

### Overall Complexity

The `Dockerfile` for the `amazon-agent` is notably more complex than typical Dockerfiles for stateless web services. This complexity arises from the need to create a full graphical environment (X11 server, window manager, VNC server, and a web browser running in headful mode) inside a container that is usually a headless environment. This setup is essential for Playwright to control the browser in a way that can be visually monitored and debugged via VNC, which is particularly useful for automation tasks that involve complex web interactions. This allows the agent to function as if it were a human user operating a browser.
