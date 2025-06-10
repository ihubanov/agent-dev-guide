import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";
import OpenAI from "openai";
import { ChatCompletionChunk } from "openai/resources/chat";

import { PromptPayload } from "./types";
import { MODEL, LLM_API_KEY, LLM_BASE_URL } from "../constants";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Initialize OpenAI client with retry configuration
const openAI = new OpenAI({
  apiKey: LLM_API_KEY,
  baseURL: LLM_BASE_URL,
  maxRetries: 3,
});

const systemPrompt = fs.readFileSync(
  path.join(__dirname, "../system-prompt.txt"),
  "utf8"
);

const enqueueMessage = (
  stop: boolean,
  content: string
): ChatCompletionChunk => {
  return {
    id: `chatcmpl-${new Date().valueOf()}`,
    object: "chat.completion.chunk",
    created: new Date().getTime(),
    model: MODEL || "unknown",
    choices: [
      {
        index: 0,
        delta: {
          content: content,
        },
        logprobs: null,
        finish_reason: stop ? "stop" : null,
      },
    ],
  };
};

export const prompt = async (
  payload: PromptPayload
): Promise<string | ReadableStream<Uint8Array>> => {
  console.log("Starting prompt with payload:", payload);

  if (!payload.messages?.length) {
    throw new Error("No messages provided in payload");
  }

  try {
    // Initialize messages with system message and user payload
    return new ReadableStream({
      async start(controller) {
        const messages: Array<OpenAI.ChatCompletionMessageParam> = [
          {
            role: "system",
            content: systemPrompt,
          },
          ...(payload.messages as Array<OpenAI.ChatCompletionMessageParam>),
        ];
        console.log("Messages: ", messages);
        const completion = await openAI.chat.completions.create({
          model: MODEL || "unknown",
          messages,
          temperature: 0,
          stream: true,
          seed: 42,
        });

        let streamContent = "";
        controller.enqueue(
          new TextEncoder().encode(
            `data: ${JSON.stringify(enqueueMessage(false, streamContent))}\n\n`
          )
        );

        for await (const chunk of completion) {
          if (chunk) {
            const content = (chunk as ChatCompletionChunk).choices[0].delta
              .content;
            if (content) {
              streamContent += content;
            }
            controller.enqueue(
              new TextEncoder().encode(`data: ${JSON.stringify(chunk)}\n\n`)
            );
          }
        }

        controller.close();
      },
    });
  } catch (error) {
    console.error("Error in prompt execution:", error);
    throw new Error(
      `Failed to execute prompt: ${
        error instanceof Error ? error.cause || error.message : "Unknown error"
      }`
    );
  }
};
