## Configuration

The personal-agent is configured primarily through environment variables, allowing for flexibility in different deployment environments (development, production) and easy customization of key parameters without modifying the source code.

### Environment Variables and `.env`

The agent utilizes the `dotenv` package to manage environment variables. This is evident from the import statement at the very beginning of the main application file:

```typescript
// src/index.ts
import "dotenv/config";
```

This line ensures that when the application starts, `dotenv` will look for a file named `.env` in the root directory of the agent (alongside `package.json`). If this file exists, `dotenv` loads any variables defined within it into `process.env`, making them accessible throughout the application.

### `.env.example` File

To guide users on the required and optional environment variables, the project includes an `.env.example` file. This file serves as a template, listing the variables that the application recognizes. Users are expected to:

1.  Copy `examples/personal-agent/.env.example` to a new file named `examples/personal-agent/.env`.
2.  Edit the `.env` file to provide their specific values (e.g., API keys, port numbers).

The `.env` file itself should typically not be committed to version control, especially if it contains sensitive information like API keys.

### Key Configuration Variables

The following environment variables are defined and used in `src/constants.ts`, playing crucial roles in the agent's operation:

*   **`PORT`**:
    *   **Role**: Specifies the network port on which the agent's Express server will listen for incoming HTTP requests.
    *   **Default**: `80` (as seen in `src/constants.ts`, though the `dev` script in `package.json` often sets it to `4000` for development).

*   **`NODE_ENV`**:
    *   **Role**: Defines the Node.js environment mode. Common values are `development` or `production`. This can be used by the application to enable or disable certain features, like detailed error stacks in development.
    *   **Default**: `development`.

*   **`LLM_API_KEY`**:
    *   **Role**: Your API key for the Large Language Model provider (e.g., OpenAI). This is essential for authenticating requests to the LLM.
    *   **Default**: `sk-proj-unknown` (a placeholder). **Users must replace this with a valid API key.**

*   **`LLM_BASE_URL`**:
    *   **Role**: The base URL for the LLM API. This allows using OpenAI or compatible third-party/self-hosted LLM providers.
    *   **Default**: `http://localhost:65534` (often a port used by local LLM servers like LM Studio or Ollama).

*   **`MODEL`**:
    *   **Role**: Specifies the identifier of the LLM model to be used for chat completions (e.g., `gpt-4`, `gpt-3.5-turbo`, or a custom model name).
    *   **Default**: `model-name` (a placeholder). **Users should set this to their desired model.**

*   **`SYSTEM_PROMPT`**:
    *   **Role**: Allows overriding the default system prompt (read from `src/system-prompt.txt`) directly via an environment variable. This provides a quick way to change the agent's core instructions without editing files.
    *   **Default**: `""` (empty string), which means the agent will fall back to using `src/system-prompt.txt` by default.

By modifying these variables in their `.env` file, users can tailor the agent's behavior, connectivity, and deployment settings to their specific requirements.
