# Standalone Agent

This project provides a simple Node.js backend for streaming chat to a Large Language Model (LLM).

## Getting Started

1. **Install dependencies**
   Run the following command in your project directory:

   ```bash
   yarn install
   ```

2. **Set up environment variables**
   Create a `.env` file or export the variable in your shell:

   ```env
   LLM_BASE_URL=http://localhost:65534
   ```

3. **Start the backend server**
   Launch the server using:

   ```bash
   yarn start
   ```

## Backend Details

* Built with **Express** (`src/index.ts`)
* Streams chat messages to the LLM endpoint defined by `LLM_BASE_URL`

## Publishing

To package the agent, run:

```bash
yarn build
```

## Notes

* The server listens on the port defined by `EXPOSED_PORT` in `constants.ts`.
* By default, this is set to `8080`.
* If you need to change the port:

  * Update the value of `EXPOSED_PORT` in `constants.ts`
  * Also update `EXPOSE 8080` in the `Dockerfile` to match the new port

**Important:** Both must be changed together to ensure the container runs correctly.