## Core Functionality - LLM Interaction

The heart of the personal-agent lies in its ability to communicate effectively with a Large Language Model (LLM). This interaction is primarily managed within the `src/prompt/index.ts` file, which handles everything from client initialization to processing the LLM's responses.

### OpenAI Client Initialization

To communicate with the LLM, an OpenAI client is initialized. This client is configured with credentials and connection parameters sourced from constants, which are typically set via environment variables:

```typescript
import OpenAI from "openai";
import { MODEL, LLM_API_KEY, LLM_BASE_URL, SYSTEM_PROMPT } from "../constants";

const openAI = new OpenAI({
  apiKey: LLM_API_KEY,
  baseURL: LLM_BASE_URL,
  maxRetries: 3,
});
```

*   `LLM_API_KEY`: The API key for authenticating with the LLM provider.
*   `LLM_BASE_URL`: The base URL of the LLM service. This allows flexibility in using different OpenAI-compatible API providers or self-hosted models.
*   `maxRetries`: Configures the client to automatically retry requests up to 3 times in case of transient network issues.

### System Prompt Loading and Role

The system prompt plays a crucial role in guiding the LLM's behavior, defining its personality, task focus, and the desired style of its responses. The agent loads the system prompt using the following logic:

```typescript
const systemPrompt =
  SYSTEM_PROMPT || // Prioritizes environment variable
  fs.readFileSync(path.join(__dirname, "../system-prompt.txt"), "utf8"); // Fallback to file
```

1.  It first checks if a `SYSTEM_PROMPT` environment variable is set. If so, its value is used.
2.  If the environment variable is not found, it falls back to reading the content of the `src/system-prompt.txt` file.

This dual approach allows for easy customization of the agent's core instructions without modifying the code, simply by changing an environment variable or the text file.

### The `prompt` Function

The main logic for LLM communication resides in the asynchronous `prompt` function:

```typescript
export const prompt = async (
  payload: PromptPayload
): Promise<string | ReadableStream<Uint8Array>> => {
  // ...
};
```

1.  **Message Construction**: The function receives a `payload` containing the user's messages (and potentially other parameters). It then constructs a `messages` array to be sent to the LLM. This array always begins with the loaded `systemPrompt` (assigned the "system" role), followed by the messages from the `payload` (which could be from the user or previous assistant responses).

    ```typescript
    const messages: Array<OpenAI.ChatCompletionMessageParam> = [
      {
        role: "system",
        content: systemPrompt,
      },
      ...(payload.messages as Array<OpenAI.ChatCompletionMessageParam>),
    ];
    ```

2.  **Sending the Request to LLM**: The constructed message list is then sent to the LLM using the `openAI.chat.completions.create` method.

    ```typescript
    const completion = await openAI.chat.completions.create({
      model: MODEL || "unknown", // Model name from constants
      messages,
      temperature: 0,
      stream: true,
      seed: 42,
    });
    ```

    Key parameters used here include:
    *   `model`: Specifies which LLM model to use (e.g., "gpt-3.5-turbo", "gpt-4", or a custom model name defined in constants).
    *   `messages`: The array of system and user/assistant messages.
    *   `stream: true`: This is a crucial parameter that requests the LLM to send its response as a stream of events (Server-Sent Events). This allows the agent to process and forward parts of the response as they become available, rather than waiting for the entire response to complete. This is essential for providing a responsive, real-time experience to the user.
    *   `temperature: 0`: Setting the temperature to 0 aims for more deterministic and less random responses. The LLM will be more likely to choose the highest probability words.
    *   `seed: 42`: When used in conjunction with a low temperature, providing a seed value can help in obtaining reproducible outputs from the LLM, which is beneficial for testing and scenarios requiring consistent responses. (Note: Reproducibility with LLMs can still be challenging and might depend on the specific model and provider.)

3.  **Streaming Response**: The function is designed to return a `ReadableStream<Uint8Array>`. It processes the incoming stream from the `completion` object, encodes each chunk, and forwards it through the controller of the `ReadableStream`. This enables the `/prompt` endpoint in `src/index.ts` to pipe the LLM's response directly to the client in real-time.

This careful orchestration of client setup, prompt management, and request parameters allows the personal-agent to effectively leverage the power of LLMs for various tasks.
