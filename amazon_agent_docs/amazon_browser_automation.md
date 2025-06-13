## Core Functionality - Browser Automation (`server.py`, Playwright)

The `amazon-agent`'s ability to interact with e-commerce websites like Amazon hinges on its browser automation capabilities. This is primarily managed within `server.py` through the `browser_use` library, which appears to be a wrapper or utility layer around Playwright. The setup also includes a VNC environment to allow visibility into the browser's operations.

### Playwright Integration (via `browser_use` library)

The core of the browser automation is handled by initializing and configuring a browser session and context using the `browser_use` library. This setup occurs within the `lifespan` asynchronous context manager in `server.py`, ensuring the browser is ready before the agent starts processing requests and is cleaned up on shutdown.

1.  **Initialization**:
    *   A `BrowserSession` is created, which likely represents the main browser instance.
    *   From this session, a `BrowserContext` is established. This context is what the agent's tools will use to interact with web pages.
        ```python
        # In server.py lifespan
        browser = BrowserSession(
            config=BrowserConfig(...)
        )
        ctx = await browser.new_context()
        _GLOBALS['browser'] = browser
        _GLOBALS['browser_context'] = ctx
        await _GLOBALS['browser_context'].__aenter__()
        ```
    *   The created browser context is stored in a global dictionary `_GLOBALS['browser_context']`, making it accessible to other parts of the application, particularly the tool implementations in `app/tool_impl.py` which perform the actual browser actions.

2.  **Browser Configuration (`BrowserConfig`)**:
    The `BrowserSession` is configured using `BrowserConfig`, which specifies:
    *   `headless=False`: The browser runs in a headed mode, meaning it has a visible UI (though this UI is within the virtual Xvfb display). This is essential for VNC viewing.
    *   `user_data_dir=BROWSER_PROFILE_DIR`: Specifies a directory for storing browser profile data (cookies, local storage, etc.), allowing for session persistence if needed.
    *   `window_size`: Sets the dimensions of the browser window (e.g., width and height from environment variables `BROWSER_WINDOW_SIZE_WIDTH`, `BROWSER_WINDOW_SIZE_HEIGHT`).

3.  **Context Configuration (`BrowserContextConfig`)**:
    The `BrowserContext` is further tailored with `BrowserContextConfig`:
    *   `allowed_domains=["*"]`: Potentially allows interaction with any domain, though this could be narrowed for security.
    *   `cookies_file=None`: Indicates cookie management might be handled differently or not persisted via a single file in this config.
    *   `maximum_wait_page_load_time`: Sets a timeout for page loads.
    *   `disable_security=False`: Keeps standard web security features enabled.
    *   `user_agent`: A specific user agent string is set (e.g., "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."), which can influence how websites respond to the agent.

### Purpose of VNC (Virtual Network Computing) Setup

A significant part of `server.py`'s `lifespan` manager is dedicated to setting up a VNC environment. This is crucial because the browser, while automated, runs in a "headed" mode within the Docker container's virtual display.

*   **Xvfb (X Virtual Framebuffer)**: Creates the necessary virtual display on the server, allowing the Chrome browser to run as if it had a physical screen.
*   **Openbox**: A lightweight window manager that runs within the Xvfb session, providing basic window management for the browser.
*   **x11vnc**: This program acts as a VNC server for the X11 session managed by Xvfb. It makes the virtual screen's content available over the VNC protocol.
*   **noVNC**: A web-based VNC client is also started (via `novnc_proxy`). Users can connect to this client through their own web browser (the URL for which is provided by the `/processing-url` endpoint).

This VNC setup serves several important purposes:
1.  **Monitoring**: Allows developers and users to visually monitor the agent's actions in real-time as it navigates and interacts with websites.
2.  **Debugging**: When the agent encounters errors or unexpected behavior, viewing the browser directly via VNC is an invaluable debugging tool to understand what went wrong on the web page.
3.  **Manual Intervention**: For complex scenarios that the agent might not be programmed to handle (e.g., sophisticated CAPTCHAs, unusual website pop-ups, or significant layout changes), the VNC interface provides a means for a human to manually take control of the browser session, complete the problematic step, and then let the agent resume.

### CAPTCHA Handling

The `server.py` includes a basic attempt at CAPTCHA detection during the initial page load within the `lifespan` manager:

```python
# In server.py lifespan, after navigating to AMAZON_URL
if await is_showing_captcha(ctx):
    await current_page.reload()
```
The `is_showing_captcha` function (from `app/utils.py`) likely checks for common CAPTCHA elements on the page. If a CAPTCHA is detected, the page is reloaded as a simple first attempt to bypass it.

While this is a proactive step, web CAPTCHAs can be highly complex. For robust, unattended automation, more sophisticated CAPTCHA-solving services or techniques might be necessary. However, the VNC access serves as a practical fallback, enabling manual user intervention when automated CAPTCHA handling fails.

In summary, the `amazon-agent` uses Playwright (via `browser_use`) for its core browser interactions, configured to run within a virtual display that can be accessed via VNC for monitoring and manual intervention, with basic provisions for automated CAPTCHA detection.
