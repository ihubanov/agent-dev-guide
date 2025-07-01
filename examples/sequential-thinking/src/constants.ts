export const PORT = process.env.PORT || 80;
export const NODE_ENV = process.env.NODE_ENV || "development";

export const LLM_API_KEY = process.env.LLM_API_KEY || "sk-proj-unknown";
export const LLM_BASE_URL =
  process.env.LLM_BASE_URL || "http://localhost:65534";
export const MODEL =
  process.env.MODEL || process.env.LLM_MODEL_ID || "local-model";

// MCP configuration
export const CLIENT_NAME = "mcp-server-client";
export const CLIENT_VERSION = "1.0.0";
export const MCP_SERVER_URL =
  process.env.NODE_ENV === "production"
    ? "./dist/src/mcp-server/index.js"
    : "./src/mcp-server/index.ts";
