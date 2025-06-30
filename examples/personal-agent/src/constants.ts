// ⚠️ Do NOT change the fallback port (80). It's required by the system for proper operation.
// Use environment variable PORT to override during development.
export const PORT = process.env.PORT || 80;
export const NODE_ENV = process.env.NODE_ENV || "development";

export const LLM_API_KEY = process.env.LLM_API_KEY || "sk-proj-unknown";
export const LLM_BASE_URL =
  process.env.LLM_BASE_URL || "http://localhost:65534";
export const MODEL = process.env.MODEL || "model-name";

export const SYSTEM_PROMPT = process.env.SYSTEM_PROMPT || "";
