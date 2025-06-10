import "dotenv/config";
import cors from "cors";
import express, { Request, Response } from "express";
import helmet from "helmet";

import { prompt } from "./prompt/index";
import type { PromptPayload } from "./prompt/types";
import { PORT, NODE_ENV } from "./constants";

const app = express();
const port = PORT;

// Security middleware
app.use(helmet());
app.use(cors());
app.use(express.json({ limit: "50mb" }));

// Basic health check
app.get("/health", (req: Request, res: Response) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

type ExtendedPromptPayload = PromptPayload & {
  ping?: boolean;
  stream?: boolean;
};

interface StreamResponse extends Response {
  flush?: () => void;
}

const handlePrompt = async (req: Request, res: StreamResponse) => {
  const payload: ExtendedPromptPayload = req.body;
  try {
    if (!!payload.ping) {
      res.send("online");
    } else {
      if (payload.stream) {
        // Set headers for SSE
        res.setHeader("Content-Type", "text/event-stream");
        res.setHeader("Cache-Control", "no-cache");
        res.setHeader("Connection", "keep-alive");

        // Stream the response
        try {
          console.log("Starting streaming response");
          const result = await prompt(payload);

          if (result && typeof result === "object" && "getReader" in result) {
            console.log("Got readable stream, starting to read");
            const reader = (result as ReadableStream).getReader();

            try {
              while (true) {
                const { done, value } = await reader.read();
                if (done) {
                  console.log("Stream complete");
                  res.write("data: [DONE]\n\n");
                  break;
                }
                // Forward the chunk directly
                res.write(value);
                // Flush the response
                if (typeof res.flush === "function") {
                  res.flush();
                }
              }
            } catch (error) {
              console.error("Stream reading error:", error);
              res.write(
                `data: ${JSON.stringify({
                  type: "error",
                  error:
                    error instanceof Error ? error.message : "Unknown error",
                })}\n\n`
              );
            } finally {
              reader.releaseLock();
              res.end();
            }
          } else {
            console.log("Got non-stream response:", result);
            // For non-stream responses in streaming mode, format as SSE
            res.write(
              `data: ${JSON.stringify({
                type: "complete",
                content: result,
              })}\n\n`
            );
            res.write("data: [DONE]\n\n");
            res.end();
          }
        } catch (error) {
          console.error("Stream processing error:", error);
          res.write(
            `data: ${JSON.stringify({
              type: "error",
              error: error instanceof Error ? error.message : "Unknown error",
            })}\n\n`
          );
          res.end();
        }
      } else {
        // Non-streaming response
        const result = await prompt(payload);
        console.log("result: ", result);
        res.json(result);
      }
    }
  } catch (error) {
    console.log("prompt: error", error);
    res.status(500).json({ error: (error as Error).message });
  }
};

app.post("/prompt", handlePrompt);

// Global error handler
app.use((err: Error, req: Request, res: Response) => {
  console.error("Unhandled error:", err);
  res.status(500).json({
    error: err.message,
    stack: NODE_ENV === "production" ? undefined : err.stack,
  });
});

// Start the server
app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
  console.log(`Environment: ${NODE_ENV || "development"}`);
});
