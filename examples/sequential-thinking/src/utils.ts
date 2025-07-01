import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import OpenAI from "openai";
import { MODEL } from "./constants.js";
import { ChatCompletionChunk } from "openai/resources/chat/completions";

export interface McpTool {
  name: string;
  description: string;
  inputSchema?: {
    type: string;
    properties?: Record<string, unknown>;
    required?: string[];
  };
}

export const convertMcpToolsToOpenAiFormat = (
  mcpTools: McpTool[] | Record<string, unknown>
): OpenAI.ChatCompletionTool[] => {
  const toolsList = (
    Array.isArray(mcpTools)
      ? mcpTools
      : "tools" in mcpTools
      ? (mcpTools as { tools?: McpTool[] }).tools ?? []
      : []
  ) as McpTool[];

  return toolsList
    .filter(
      (tool: unknown): tool is McpTool =>
        typeof tool === "object" &&
        tool !== null &&
        "name" in tool &&
        "description" in tool
    )
    .map((tool: McpTool) => {
      const toolSchema = {
        type: "object",
        properties:
          (tool.inputSchema as { properties?: Record<string, unknown> })
            ?.properties ?? {},
        required: (tool.inputSchema as { required?: string[] })?.required ?? [],
      };

      const openAiTool: OpenAI.ChatCompletionTool = {
        type: "function",
        function: {
          name: tool.name,
          description: tool.description,
          parameters: toolSchema,
        },
      };
      return openAiTool;
    });
};

export const processToolCalls = async (
  toolCalls: OpenAI.ChatCompletionMessageToolCall[],
  client: Client
): Promise<string[]> => {
  const results: string[] = [];

  for (const call of toolCalls) {
    const {
      function: { name, arguments: args },
    } = call;

    try {
      const parsedArgs = JSON.parse(args);
      const res = (await client.callTool({
        name: name,
        arguments: parsedArgs,
      })) as { content: Array<{ type: "text"; text: string }> };

      if (res?.content?.[0]?.text) {
        results.push(res.content[0].text);
      }
    } catch (error) {
      results.push(
        `Error executing tool ${name}: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      );
    }
  }

  return results;
};

export async function ensureConnection(
  client: Client,
  transport: StdioClientTransport,
  retries = 3
): Promise<void> {
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      if (!(await client.ping())) {
        await client.connect(transport);
      }
      return;
    } catch (error) {
      if (attempt === retries - 1) {
        throw new Error(
          `Failed to connect to MCP server after ${retries} attempts: ${
            error instanceof Error ? error.message : "Unknown error"
          }`
        );
      }
      await new Promise((resolve) =>
        setTimeout(resolve, 1000 * Math.pow(2, attempt))
      );
    }
  }
}

export const enqueueMessage = (
  stop: boolean,
  content: string,
  role: string = "assistant"
): ChatCompletionChunk => {
  return {
    id: `chatcmpl-${new Date().valueOf()}`,
    object: "chat.completion.chunk",
    created: new Date().getTime(),
    model: MODEL,
    choices: [
      {
        index: 0,
        delta: {
          content: content as any,
          role: role as any,
        },
        logprobs: null,
        finish_reason: stop ? "stop" : null,
      },
    ],
  };
};

export const removeThink = (content: string) => {
  return content.replace(/<think>.*?<\/think>/gs, "");
};
