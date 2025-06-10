# Amazon Agent

Welcome to the Amazon Agent setup guide. Follow these steps to get your environment ready.

---

## 1. Clone the GitHub Repository

Clone the template repository to your local machine:

```bash
git clone https://github.com/eternalai-org/agent-dev-guide/examples/amazon-agent
cd amazon-agent
````

---

## 2. Prerequisites

Ensure you have the following installed:

* [Docker](https://www.docker.com/)

---

## 3. (Optional) Set Environment Variables

You may define these environment variables for flexibility:

```env
LLM_MODEL_ID=model-name
LLM_BASE_URL=http://localhost:65534/v1
LLM_API_KEY=unknown
```

---

## 4. Build the Docker Image

Run this command to build the Docker image:

```bash
docker build -t container_name .
```

---

## 5. Run the Docker Container & Start the Agent

Start your container and set environment variables:

```bash
docker run --rm -it \
  -v ${pwd}:/workspace \
  -p 8000:80 -p 6080:6080 \
  -e LLM_BASE_URL=http://localmodel:65534/v1 \
  -e LLM_API_KEY=unknown \
  -e LLM_MODEL_ID=model-name \
  --entrypoint /bin/bash \
  --add-host=localmodel:host-gateway \
  container_name
```

Inside the container, start the server:

```bash
cd /workspace    # If not already in this directory
python server.py
```

---

## 6. Open the Agent Interface in Your Browser

Access the interface via:

[http://localhost:6080/vnc.html?host=localhost\&port=6080\&autoconnect=true](http://localhost:6080/vnc.html?host=localhost&port=6080&autoconnect=true)

---

## 7. Send a Prompt to the Agent

Test the agent with a prompt using `curl`:

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

## ✅ Done

Your agent is now up and running and ready to process requests.