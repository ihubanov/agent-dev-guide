export const PORT = process.env.PORT || 80;
export const NODE_ENV = process.env.NODE_ENV || "development";

export const LLM_API_KEY = "sk-proj-unknown";
export const LLM_BASE_URL =
  process.env.NODE_ENV === "production"
    ? process.env.LLM_BASE_URL || "http://localhost:65534"
    : "http://localhost:8000";
export const MODEL = "model-name";
export const SYSTEM_PROMPT = process.env.SYSTEM_PROMPT || "";