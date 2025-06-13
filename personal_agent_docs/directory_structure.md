## Directory Structure

The `examples/personal-agent/` directory is organized to provide a clear and maintainable structure for the agent's codebase. Key files and directories include:

*   **`src/`**: This is the main directory containing all the TypeScript source code for the agent.
    *   **`index.ts`**: The primary entry point of the application. It initializes and configures the Express.js server, sets up middleware, and defines API endpoints like `/health` and `/prompt`.
    *   **`constants.ts`**: Defines application-wide constants, such as environment variables for port numbers, API base URLs (e.g., `LLM_BASE_URL`), model names, and the system prompt if provided via environment variables.
    *   **`prompt/`**: This sub-directory encapsulates the logic related to interacting with the Large Language Model (LLM).
        *   **`index.ts`**: Contains the core functionality for LLM communication. This includes initializing the OpenAI API client, loading the system prompt (either from `system-prompt.txt` or an environment variable), constructing the messages payload, and handling the streaming of responses from the LLM.
        *   **`types.ts`**: Provides TypeScript type definitions for structures used in LLM interactions, such as `PromptPayload`, `Message`, `MessageRole`, and `ContentPart`, ensuring type safety and clarity in the codebase.
    *   **`__tests__/`**: This directory houses the test files for the agent.
        *   **`index.test.ts`**: An example test file (likely using a framework like Jest, as suggested by `jest.config.js`) for testing the agent's API endpoints or core functionalities.

*   **`system-prompt.txt`**: A plain text file containing the default system prompt that guides the AI's behavior, personality, and response style. This prompt is loaded by the `prompt/index.ts` logic if not overridden by an environment variable.

*   **`Dockerfile`**: Contains the instructions to build a Docker image for the personal-agent, specifying the base Node.js image, working directory, dependency installation, and the command to run the agent.

*   **`package.json`**: The standard Node.js project manifest file. It lists project metadata, dependencies (like `express`, `openai`, `typescript`), and devDependencies. It also defines useful scripts for running, developing, and testing the agent (e.g., `start`, `dev`, `test`).

*   **`.env.example`**: An example file demonstrating the required environment variables for the agent, such as `PORT`, `LLM_BASE_URL`, `LLM_API_KEY`, and `MODEL`. Users should copy this to a `.env` file and populate it with their specific configurations.

*   **`README.md`**: Provides documentation specific to the `personal-agent` example, including setup instructions, usage guidelines, and customization tips.
