# Personal AI Agent

This example shows how to set up and use a personal AI agent. You can customize and extend it for tasks like automation or productivity.

## Requirements

* [Node.js](https://nodejs.org/) (version 16 or higher)
* [npm](https://www.npmjs.com/) or [yarn](https://yarnpkg.com/)

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/eternalai-org/agent-dev-guide.git
   cd agent-dev-guide/examples/personal-agent
   ```

2. Install the dependencies:

   ```bash
   npm install
   # or
   yarn install
   ```

## How to Use

Develop the agent:

   ```bash
   npm run dev
   # or
   yarn dev
   ```
## Customizing the Agent

You can customize the agent's behavior by modifying the `system-prompt.txt` file. This file contains the instructions that define how your agent should behave and respond.

### Update System Prompt

1. Add your custom instructions to the file. Here's an example:

   ```text
   You are a helpful AI assistant focused on productivity and task management. Your responses should be:
   - Clear and concise
   - Action-oriented
   - Focused on helping users achieve their goals
   
   When responding to users:
   1. Understand their needs and goals
   2. Provide specific, actionable advice
   3. Break down complex tasks into manageable steps
   4. Follow up to ensure understanding
   ```

2. The agent will automatically use these instructions when processing requests.

You can also set the system prompt using the `SYSTEM_PROMPT` environment variable.


### Example API Call

You can also send a request like this:

```bash
curl --location 'http://localhost:4000/prompt' \
--header 'Content-Type: application/json' \
--data '{
  "messages": [
    {
      "role": "user",
      "content": "hello"
    }
  ]
}'
```

## Available Commands

* `npm run dev` — Start the agent in development mode
* `npm run start` — Start the agent in production mode

---

**Note:**

* Keep the `PORT` and `LLM_BASE_URL` environment variables — they are used by the platform.
* Replace placeholder values and add details based on your agent setup.
