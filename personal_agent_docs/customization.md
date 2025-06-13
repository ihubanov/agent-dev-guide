## Customization

The personal-agent is designed to be adaptable, allowing users to tailor its behavior and configuration to their specific needs and preferences. Customizations range from altering the agent's core personality and instructions to changing the underlying Large Language Model (LLM) and its parameters.

### 1. Modifying Agent Behavior (System Prompt)

The primary method for customizing how the agent responds and behaves is by modifying its system prompt. The system prompt provides the LLM with context and high-level instructions, guiding its personality, tone, and the focus of its replies. There are two ways to change the system prompt:

*   **Editing `src/system-prompt.txt`**:
    *   Users can directly edit the content of the `examples/personal-agent/src/system-prompt.txt` file. This file contains the default instructions for the agent. Any changes saved here will be loaded by the agent upon startup, unless overridden by the environment variable.
    *   The `README.md` for the personal-agent highlights this as a way to customize the agent, providing examples of how to craft these instructions.

*   **Setting the `SYSTEM_PROMPT` Environment Variable**:
    *   As defined in `src/constants.ts` and used in `src/prompt/index.ts`, the `SYSTEM_PROMPT` environment variable takes precedence over the `system-prompt.txt` file.
    *   If this environment variable is set, its value will be used as the system prompt, ignoring the content of the text file. This method is useful for making quick changes without altering project files, or for deploying the agent with different personalities in various environments.

### 2. LLM and Connection Parameters

Users can also customize which LLM is used and how the agent interacts with it:

*   **Changing the LLM Model (`MODEL`)**:
    *   The `MODEL` environment variable (defined in `src/constants.ts`) allows users to specify which LLM model the agent should use (e.g., `gpt-4`, `gpt-3.5-turbo`, or a custom model identifier). This is passed to the LLM API when creating chat completions.

*   **Using a Different LLM Provider/Instance**:
    *   The `LLM_BASE_URL` and `LLM_API_KEY` environment variables enable users to connect to different LLM providers or self-hosted instances. `LLM_BASE_URL` specifies the API endpoint, and `LLM_API_KEY` provides the necessary authentication.

*   **Adjusting LLM Parameters (Advanced)**:
    *   In `src/prompt/index.ts`, parameters like `temperature` and `seed` are passed to the LLM:
        ```typescript
        const completion = await openAI.chat.completions.create({
          // ...
          temperature: 0,
          stream: true,
          seed: 42,
        });
        ```
    *   Currently, `temperature` is hardcoded to `0` and `seed` to `42` to promote deterministic and consistent responses.
    *   Advanced users could modify these values directly in the code if more response variability (`temperature` > 0) or different consistent response sets (different `seed` values) are desired. However, exposing these via environment variables would be a further enhancement for easier configuration if needed.

### 3. Other Configurations

As detailed in the "Configuration" section, other environment variables like `PORT` and `NODE_ENV` can also be adjusted to suit different deployment or development setups.

By leveraging these customization options, users can significantly alter the personal-agent's functionality, making it a versatile tool for a wide range of AI-assisted tasks.
