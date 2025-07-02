import "dotenv/config";
import express from "express";
import { PORT, LLM_BASE_URL, MODEL, EXPOSED_PORT } from "./constants.js";
import path from "path";
import { fileURLToPath } from "url";

const app = express();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

app.use(express.json());
app.use(express.static(path.join(__dirname, "../public")));

// SSE streaming endpoint
app.get("/api/chat/stream", async (req, res) => {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");

  // Express query params are string | string[] | undefined, so normalize to string
  const query: any = req.query;
  let historyStr: string;
  if (typeof query.history === "string") {
    historyStr = query.history;
  } else if (Array.isArray(query.history)) {
    historyStr = (query.history[0] as string | undefined) ?? "[]";
  } else {
    historyStr = "[]";
  }
  const history = JSON.parse(historyStr);

  // Proxy to LLM_BASE_URL (assume OpenAI-compatible streaming API)
  try {
    const response = await fetch(`${LLM_BASE_URL}/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: MODEL,
        messages: history,
        stream: true,
      }),
    });
    if (!response.ok || !response.body) throw new Error("LLM error");
    const reader = response.body.getReader();
    let decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let lines = buffer.split("\n");
      buffer = lines.pop() as any;
      for (const line of lines) {
        if (line.startsWith("data:")) {
          const data = line.slice(5).trim();
          if (data === "[DONE]") {
            res.write("event: end\ndata: \n\n");
            res.end();
            return;
          }
          try {
            const json = JSON.parse(data);
            const token = json.choices?.[0]?.delta?.content || "";
            if (token) {
              res.write(`data: ${token}\n\n`);
            }
          } catch {}
        }
      }
    }
    res.write("event: end\ndata: \n\n");
    res.end();
  } catch (e) {
    res.write("event: end\ndata: \n\n");
    res.end();
  }
});

app.listen(EXPOSED_PORT, () => {
  console.log(`Chat server running: http://localhost:${EXPOSED_PORT}`);
});

// --- Second server setup ---
const secondApp = express();

secondApp.get("/processing-url", (req: any, res: any) => {
  res.json({
    url: `http://localhost:${EXPOSED_PORT}`,
    status: "ready",
  });
});

secondApp.get("/health", (req, res) => {
  res.json({ status: "healthy" });
});

secondApp.listen(PORT, () => {
  console.log(`Second server running: http://localhost:${PORT}`);
});

export default app;
