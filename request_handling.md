## Core Functionality - Request Handling

The personal-agent's ability to receive and process user requests is managed by an Express.js server defined in `src/index.ts`. This file orchestrates how incoming HTTP requests are handled, routed, and responded to.

### Express Server Setup

The foundation of the request handling mechanism is the Express server instance:

```typescript
import express from "express";
const app = express();
```

This `app` object is then configured with middleware and route handlers to manage different aspects of incoming requests.

### Middleware

Before requests reach specific route handlers, they pass through several middleware functions that enhance security, enable cross-origin requests, and parse request bodies:

*   **`helmet()`**: This middleware helps secure the application by setting various HTTP headers. For instance, it can help protect against common web vulnerabilities like cross-site scripting (XSS) and clickjacking.
    ```typescript
    import helmet from "helmet";
    app.use(helmet());
    ```

*   **`cors()`**: Cross-Origin Resource Sharing (CORS) middleware allows the agent's API to be called from web applications running on different domains. This is essential for many modern web architectures.
    ```typescript
    import cors from "cors";
    app.use(cors());
    ```

*   **`express.json()`**: This built-in Express middleware parses incoming requests with JSON payloads (i.e., with a `Content-Type` of `application/json`). It makes the parsed JSON data available in `req.body`. A limit for the payload size is also configured.
    ```typescript
    app.use(express.json({ limit: "50mb" }));
    ```

### API Endpoints

The agent exposes specific endpoints to interact with it:

#### `/prompt` Endpoint

This is the primary endpoint for interacting with the LLM.

*   **Method and Path**: It handles `POST` requests to the `/prompt` path.
    ```typescript
    app.post("/prompt", handlePrompt);
    ```
*   **Request Payload**: The endpoint expects a JSON payload in the request body. A crucial part of this payload is a `messages` array, which typically contains the conversation history or the user's current query. This structure is defined in `src/prompt/types.ts`.
*   **Functionality**: When a request hits `/prompt`, the `handlePrompt` asynchronous function is invoked. This function takes the request and response objects, extracts the payload (especially the `messages`), and then calls the `prompt` function (imported from `src/prompt/index.ts`). The `prompt` function is responsible for the actual communication with the LLM, including sending the system prompt and user messages, and then streaming the LLM's response back to the client. The endpoint is designed to handle Server-Sent Events (SSE) for streaming.

#### `/health` Endpoint

This endpoint provides a basic health check for the server.

*   **Method and Path**: It handles `GET` requests to the `/health` path.
    ```typescript
    app.get("/health", (req: Request, res: Response) => {
      res.json({ status: "ok", timestamp: new Date().toISOString() });
    });
    ```
*   **Functionality**: When accessed, it returns a simple JSON response indicating that the server is running (`"status": "ok"`) along with the current server timestamp. This is useful for monitoring and uptime checks.

An unhandled error catching middleware is also present to provide a standardized error response.
```typescript
app.use((err: Error, req: Request, res: Response) => {
  console.error("Unhandled error:", err);
  res.status(500).json({
    error: err.message,
    stack: NODE_ENV === "production" ? undefined : err.stack,
  });
});
```
