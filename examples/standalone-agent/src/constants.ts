export const PORT = process.env.PORT || 80;
export const NODE_ENV = process.env.NODE_ENV || "development";

export const LLM_API_KEY = process.env.LLM_API_KEY || "sk-proj-unknown";
export const LLM_BASE_URL = process.env.LLM_BASE_URL || "http://localhost:65534";
export const MODEL =
  process.env.MODEL || process.env.LLM_MODEL_ID || "local-model";

export const EXPOSED_PORT = 8080; // This is the port that will be exposed to the user for the chat UI, make sure to change it in the Dockerfile if you change it here
