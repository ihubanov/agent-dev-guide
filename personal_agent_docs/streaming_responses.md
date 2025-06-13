## Core Functionality - Streaming Responses

A key feature of the personal-agent is its ability to stream responses from the Large Language Model (LLM) back to the client. This provides a much more responsive and real-time user experience, as users don't have to wait for the entire LLM response to be generated before seeing output. This mechanism is orchestrated between `src/prompt/index.ts` (the stream producer) and `src/index.ts` (the stream consumer and forwarder).

### Producing the Stream (`src/prompt/index.ts`)

The `prompt` function in `src/prompt/index.ts` is responsible for initiating the LLM interaction and producing a stream of data.

1.  **Returning a `ReadableStream`**: The function is declared to return `Promise<string | ReadableStream<Uint8Array>>`. For streaming requests, it specifically returns a `ReadableStream`.

    ```typescript
    export const prompt = async (
      payload: PromptPayload
    ): Promise<string | ReadableStream<Uint8Array>> => {
      // ...
      return new ReadableStream({
        async start(controller) {
          // ... stream logic ...
        },
      });
    };
    ```

2.  **Initiating LLM Stream**: Inside the `ReadableStream`'s `start` method, the call to the OpenAI API is made with the `stream: true` parameter:

    ```typescript
    const completion = await openAI.chat.completions.create({
      // ... other parameters ...
      stream: true,
    });
    ```

3.  **Enqueuing LLM Chunks as SSE**: As the LLM generates a response, it sends back chunks of data. The code iterates through these chunks. Each `chunk` received from the `completion` stream (which is an `OpenAI.ChatCompletionChunk`) is then formatted as a Server-Sent Event (SSE) string and enqueued into the `ReadableStream` controller. The SSE format `data: {JSON_chunk}\n\n` is used, ensuring the client can easily parse these events.

    ```typescript
    // Initial empty message to start the stream
    controller.enqueue(
      new TextEncoder().encode(
        `data: ${JSON.stringify(enqueueMessage(false, ""))}\n\n`
      )
    );

    for await (const chunk of completion) {
      if (chunk) {
        // Forward the raw chunk, already formatted as SSE by OpenAI library (or similar structure)
        // The chunk itself is a ChatCompletionChunk, which needs to be stringified for the data field of SSE
        controller.enqueue(
          new TextEncoder().encode(`data: ${JSON.stringify(chunk)}\n\n`)
        );
      }
    }
    controller.close(); // Close the stream when LLM is done
    ```
    *(Self-correction: The `enqueueMessage` utility is used for an initial message, the actual chunks from OpenAI are directly stringified and sent)*. The critical part is that each piece of data is prefixed with `data: ` and suffixed with `\n\n`.

### Consuming and Forwarding the Stream (`src/index.ts`)

The `handlePrompt` function in `src/index.ts` consumes the `ReadableStream` provided by the `prompt` function and forwards the data to the client over HTTP.

1.  **Setting SSE Headers**: Before sending any data, the server sets appropriate HTTP headers to inform the client that it should expect a stream of events:

    ```typescript
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache"); // Prevents caching of the stream
    res.setHeader("Connection", "keep-alive"); // Keeps the connection open for the duration of the stream
    ```

2.  **Reading from the Stream**: The `handlePrompt` function calls `await prompt(payload)` to get the stream. It then obtains a reader from the stream:

    ```typescript
    const result = await prompt(payload); // result is the ReadableStream
    if (result && typeof result === "object" && "getReader" in result) {
      const reader = (result as ReadableStream).getReader();
      // ... read loop ...
    }
    ```

3.  **Writing SSE Chunks to HTTP Response**: The code enters a loop, reading chunks from the stream using `await reader.read()`. Each `value` (which is a `Uint8Array` already formatted as an SSE event by the producer) is written directly to the HTTP response:

    ```typescript
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        // Stream is complete
        res.write("data: [DONE]\n\n"); // Signal end of stream to client
        break;
      }
      res.write(value); // Write the SSE formatted chunk
      // Flush the response to ensure immediate delivery
      if (typeof res.flush === "function") {
        res.flush();
      }
    }
    ```

4.  **Flushing**: After writing each chunk, `res.flush()` is called if available. This attempts to send any buffered data immediately to the client, which is crucial for the real-time effect of streaming.

5.  **Signaling Stream End**: Once the `reader.read()` returns `{ done: true }`, it signifies that the LLM has finished generating its response and the stream from `src/prompt/index.ts` is closed. The `handlePrompt` function then writes a final SSE event, `data: [DONE]\n\n`, to explicitly inform the client that the stream has concluded. The HTTP connection is then ended.

This two-part mechanism—producing SSE-formatted chunks in `src/prompt/index.ts` and consuming/forwarding them in `src/index.ts`—enables the personal-agent to deliver information from the LLM progressively.
