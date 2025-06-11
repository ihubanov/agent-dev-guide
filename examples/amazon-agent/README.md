# Amazon Agent Setup Guide

Follow these simple steps to set up and run the Amazon Agent.

---

## 1. Clone the Repository

Open your terminal and run:

```bash
git clone https://github.com/eternalai-org/agent-dev-guide.git
cd agent-dev-guide/examples/amazon-agent
```

---

## 2. Prerequisites

Make sure you have [Docker](https://www.docker.com/) installed on your computer.

---

## 3. Build the Docker Image

Build the Docker image with:

```bash
docker build -t amazon-agent .
```

---

## 4. Run the Docker Container

Start the container with the following command:

```bash
docker run --rm -it \
  -v $(pwd):/workspace \
  -p 8000:80 -p 6080:6080 \
  -e LLM_BASE_URL=http://localmodel:65534/v1 \
  -e LLM_API_KEY=unknown \
  -e LLM_MODEL_ID=model-name \
  --entrypoint /bin/bash \
  --add-host=localmodel:host-gateway \
  amazon-agent
```

---

## 5. Start the Agent Server

Inside the container, run:

```bash
cd /workspace
python server.py
```

---

## 6. Open the Agent Interface

In your browser, go to:

[http://localhost:6080/vnc.html?host=localhost&port=6080&autoconnect=true](http://localhost:6080/vnc.html?host=localhost&port=6080&autoconnect=true)

---

## 7. Test the Agent

You can test the agent by sending a prompt with `curl`:

```bash
curl --location 'http://0.0.0.0:8000/prompt' \
  --header 'Content-Type: application/json' \
  --data '{
    "messages": [
      {
        "role": "user",
        "content": "Find me a coffee maker under $50"
      }
    ],
    "stream": true
  }'
```

---

## 8. Customizing and Expanding the Agent

You can extend the agent to support more tasks and capabilities by following these steps:

- **Implement More Functions in `agent.py`:**

  - The `prompt` function in `agent.py` is responsible for handling user input and determining the agent's behavior. You can add more logic to this function to support additional tasks or customize how the agent responds to different prompts.

- **Define and Handle More Tool Calls:**
  - To add new capabilities, define additional tool functions in `tool_impl.py`. Each function should implement the logic for a specific tool or action the agent can perform.
  - Register and describe these tools in `tools.py`, specifying their names, descriptions, and parameters. This allows the agent to recognize and use the new tools when needed.
