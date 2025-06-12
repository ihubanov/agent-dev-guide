## Technology Stack

The personal-agent is built using a modern, robust technology stack, ensuring efficient development and reliable performance. The core components include:

*   **Node.js:** Serving as the runtime environment, Node.js allows the agent to execute JavaScript (and TypeScript) code server-side. Its event-driven, non-blocking I/O model is well-suited for building responsive and scalable applications. The use of Node.js is evident from the `Dockerfile` (e.g., `FROM node:22-alpine`) and scripts within the `package.json` file that utilize Node.js for execution.

*   **Express.js:** This minimal and flexible Node.js web application framework is used to build the agent's API. Express.js provides a thin layer of fundamental web application features, without obscuring Node.js features. Its presence is confirmed by its inclusion in the `package.json` dependencies and its usage in `src/index.ts` for request handling and routing (e.g., `import express from "express"; const app = express();`).

*   **TypeScript:** As the primary programming language, TypeScript brings static typing to JavaScript, enhancing code quality, maintainability, and developer productivity. The project's use of `.ts` files (e.g., `src/index.ts`, `src/prompt/index.ts`), the `tsconfig.json` configuration file, and TypeScript-related packages listed in `package.json` (like `typescript` and various `@types/*` dependencies) clearly indicate its adoption.
