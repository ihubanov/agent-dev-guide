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

Start the agent:

   ```bash
   npm start
   # or
   yarn start
   ```

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
  ],
  "stream": true
}'
```

## Available Commands

* `npm run dev` — Start the agent in development mode
* `npm run start` — Start the agent in production mode

---

**Note:**

* Keep the `PORT` and `LLM_BASE_URL` environment variables — they are used by the platform.
* Replace placeholder values and add details based on your agent setup.
