# cryptoagent-proxy

A simple Crypto Agent proxy and modern streaming chat UI for local development.

## Features

- **Crypto Agent Proxy:** Forwards all requests (except `/chat`) to your backend, bypassing CORS restrictions for local development.
- **Modern Chat UI:**
  - Streams responses from your backend in real time (OpenAI/ChatGPT style).
  - Live Markdown rendering: lists, code blocks, bold, and more are formatted as the bot types.
  - Collapsible "Reasoning" bubbles: special `<think>...</think>` sections are shown as expandable/collapsible blocks.
  - Clean, dark-themed interface.
- **Easy configuration** via `.env` file.

## Quick Start
1. **Install dependencies:**
   ```sh
   npm install
   ```

2. **Configure the proxy:**
   ```sh
   cp .env.example .env
   # Edit .env to set your PROXY_TARGET, PROXY_HOST, and PROXY_PORT
   ```

3. **Start the server:**
   ```sh
   npm start
   ```

4. **Open the chat UI:**
   Visit `http://localhost:3080/chat` (or your configured host/port) in your browser.

## Usage

- **Chat with your backend:** Type a message and press Enter. The bot's response will stream in real time, with proper Markdown formatting.
- **Reasoning bubbles:** If the backend includes `<think>...</think>` in its response, the content will appear in a collapsible "Reasoning" bubble. Click to expand/collapse.
- **Markdown support:** Lists, bold, italics, inline and block code, and other Markdown features are supported in bot output.
- **User messages:** User messages are shown as plain text (not Markdown-rendered).

## Configuration

Edit the `.env` file to set:
- `PROXY_TARGET` — The backend server to proxy requests to (e.g., `http://127.0.0.1:8000`)
- `PROXY_HOST` — The host to listen on (default: `localhost`)
- `PROXY_PORT` — The port to listen on (default: `3080`)

## Notes
- All requests except `/chat` are proxied to the backend target; `/chat` serves the chat UI.
- All static files (including `chat.html`) are served from the project directory.
- The UI is intended for local development and is not production-hardened.
- Make sure your `.env` file does **not** include quotes around variable names, and only use quotes for values if needed (e.g., for spaces). 