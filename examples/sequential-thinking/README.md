# Sequential Thinking Agent

This agent demonstrates how to implement an MCP (Model Context Protocol) server agent using the [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) framework.

## Quick Start

### 1. Install Dependencies

```bash
yarn install
```

### 2. Development Mode

Start the agent in development mode:

```bash
yarn dev
```

### 3. Add or Modify Tool Calls

You can add or customize tool calls in:

```
examples/sequential-thinking/src/mcp-server/index.ts
```

Edit this file to register new tools or change existing ones.

### 4. Configure Environment Variables

You can modify the agent's behavior by changing environment variables. Replace or update values in your environment as needed (e.g., in a `.env` file or your shell).

### 5. Package for Publishing

To package your agent for publishing:

```bash
yarn package
```

This will create a distributable package of your agent.

## Summary

- **Development:** `yarn dev`
- **Add tools:** Edit `src/mcp-server/index.ts`
- **Configure:** Update environment variables
- **Package:** `yarn package`
- **Note:** The `greeting.txt` file is shown to users the first time they start a new conversation. You can customize this file to change the initial greeting message.

For more details, see the [modelcontextprotocol/servers documentation](https://github.com/modelcontextprotocol/servers/blob/main/src/sequentialthinking/README.md).
