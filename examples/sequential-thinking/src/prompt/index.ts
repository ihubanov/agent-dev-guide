import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import fs from "fs";
import OpenAI from "openai";
import path from "path";
import { fileURLToPath } from "url";

import {
  CLIENT_NAME,
  CLIENT_VERSION,
  LLM_API_KEY,
  LLM_BASE_URL,
  MCP_SERVER_URL,
  MODEL,
  NODE_ENV,
} from "../constants.js";
import {
  convertMcpToolsToOpenAiFormat,
  ensureConnection,
  McpTool,
  processToolCalls,
  enqueueMessage,
  removeThink,
} from "../utils.js";
import { PromptPayload } from "./types.js";

// Initialize OpenAI client with retry configuration
const openAI = new OpenAI({
  apiKey: LLM_API_KEY,
  baseURL: LLM_BASE_URL,
  maxRetries: 3,
});

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SYSTEM_PROMPT = fs.readFileSync(
  path.join(__dirname, "../system-prompt.txt"),
  "utf8"
);

// Initialize MCP client
const mcpClient = new Client(
  {
    name: CLIENT_NAME,
    version: CLIENT_VERSION,
  },
  {
    capabilities: {},
  }
);

// Use Studio transport
const transport = new StdioClientTransport({
  command: NODE_ENV === "production" ? "node" : "tsx",
  env: {
    ...process.env,
    NODE_ENV,
  },
  args: [MCP_SERVER_URL],
});

mcpClient.connect(transport);

export const prompt = async (
  payload: PromptPayload
): Promise<string | ReadableStream<Uint8Array>> => {
  console.log("Starting prompt with payload:", payload);

  if (!payload.messages?.length) {
    throw new Error("No messages provided in payload");
  }

  try {
    await ensureConnection(mcpClient, transport);
    console.log("Connected to MCP server");

    const availableTools = await mcpClient.listTools();
    const openaiTools = convertMcpToolsToOpenAiFormat(
      availableTools as unknown as McpTool[]
    );

    // Add current time to the system prompt
    const currentTime = new Date().toLocaleString();

    const systemPrompt =
      SYSTEM_PROMPT +
      `\nThe current time is ${currentTime} (only use this information for time-aware responses, actions).`;

    // Initialize messages with system message and user payload
    return new ReadableStream({
      async start(controller) {
        let messages: Array<OpenAI.ChatCompletionMessageParam> = [
          {
            role: "system",
            content: systemPrompt,
          },
          ...(payload.messages as Array<OpenAI.ChatCompletionMessageParam>),
        ];

        let finished = false;
        const encoder = new TextEncoder();

        while (!finished) {
          const params = {
            model: MODEL,
            messages,
            temperature: 0,
            stream: true,
            seed: 42,
            tools: openaiTools,
          } as any;

          let streamContent = "";
          const stream = (await openAI.chat.completions.create(
            params
          )) as unknown as AsyncIterable<any>;

          let toolCallId: string | undefined;
          let toolCallName: string | undefined;
          let toolCallArgs: string | undefined;
          let toolCalls: OpenAI.ChatCompletionMessageToolCall[] = [];

          for await (const chunk of stream) {
            const choice = chunk.choices[0];
            if (choice.delta && choice.delta.tool_calls) {
              for (const toolCall of choice.delta.tool_calls) {
                if (toolCall.function.name) {
                  toolCalls.push({
                    id: `call-${new Date().valueOf()}`,
                    function: {
                      name: toolCall.function.name,
                      arguments: toolCall.function.arguments || "",
                    },
                    type: "function",
                  });
                } else {
                  toolCalls[toolCalls.length - 1].function.arguments +=
                    toolCall.function.arguments;
                }
              }
              continue;
            }

            if (choice.delta.content) {
              streamContent += choice.delta.content;
              controller.enqueue(
                encoder.encode(
                  `data: ${JSON.stringify(
                    enqueueMessage(false, choice.delta.content)
                  )}\n\n`
                )
              );
            }

            if (choice.finish_reason === "stop") {
              console.log("Finish reason: ", choice.finish_reason);
              finished = true;
            }
          }

          if (toolCalls && toolCalls.length > 0) {
            finished = false;

            // Refine the function call arguments
            for (const call of toolCalls) {
              call.function.arguments = call.function.arguments || "{}";
            }

            messages.push({
              role: "assistant",
              content: removeThink(streamContent || ""),
              tool_calls: toolCalls as OpenAI.ChatCompletionMessageToolCall[],
            });

            for (const call of toolCalls) {
              toolCallId = call.id;
              toolCallName = call.function.name;
              toolCallArgs = call.function.arguments || "{}";
              let toolResult = "";

              controller.enqueue(
                encoder.encode(
                  `data: ${JSON.stringify(
                    enqueueMessage(
                      false,
                      `<action>Executing ${toolCallName}</action>\n\n`
                    )
                  )}\n\n`
                )
              );

              const toolCallArgsMd = "```json\n" + toolCallArgs + "\n```";

              controller.enqueue(
                encoder.encode(
                  `data: ${JSON.stringify(
                    enqueueMessage(
                      false,
                      `<details>\n<summary>Arguments</summary>\n\n${toolCallArgsMd}\n\n</details>\n\n`
                    )
                  )}\n\n`
                )
              );

              try {
                const results = await processToolCalls(
                  [
                    {
                      id: toolCallId,
                      function: {
                        name: toolCallName,
                        arguments: toolCallArgs,
                      },
                      type: "function",
                    } as any,
                  ],
                  mcpClient
                );
                toolResult = results.join("\n");
              } catch (err) {
                toolResult = `Error executing tool: ${
                  err instanceof Error ? err.message : String(err)
                }`;
              }

              const toolResultMd = "```json\n" + toolResult + "\n```";

              controller.enqueue(
                encoder.encode(
                  `data: ${JSON.stringify(
                    enqueueMessage(
                      false,
                      `<details>\n<summary>Response</summary>\n\n${toolResultMd}\n\n</details>\n\n`
                    )
                  )}\n\n`
                )
              );

              messages.push({
                role: "tool",
                tool_call_id: toolCallId,
                content: toolResult,
              } as OpenAI.ChatCompletionToolMessageParam);
            }
          }
        }

        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify(enqueueMessage(true, ""))}\n\n`
          )
        );
        controller.close();
      },
    });
  } catch (error) {
    console.error("Error in prompt execution:", error);
    throw new Error(
      `Failed to execute prompt: ${
        error instanceof Error ? error.message : "Unknown error"
      }`
    );
  }
};
