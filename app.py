from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import time

app = Flask(__name__)
CORS(app)

# ================= CONFIG =================

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY")

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1/inference"

DEFAULT_MODEL = "deepseek-ai/deepseek-v3_2"

# ================= HELPERS =================

def messages_to_prompt(messages):
    """
    Convert OpenAI-style chat messages to a single prompt string
    """
    prompt = ""
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "system":
            prompt += f"[SYSTEM]\n{content}\n\n"
        elif role == "assistant":
            prompt += f"[ASSISTANT]\n{content}\n\n"
        else:
            prompt += f"[USER]\n{content}\n\n"
    prompt += "[ASSISTANT]\n"
    return prompt


def openai_style_response(text, model):
    """
    Wrap NVIDIA output into OpenAI-compatible response
    """
    now = int(time.time())
    return {
        "id": f"chatcmpl-{now}",
        "object": "chat.completion",
        "created": now,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": text
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }

# ================= ROUTES =================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/v1/models", methods=["GET"])
def list_models():
    return jsonify({
        "object": "list",
        "data": [
            {
                "id": DEFAULT_MODEL,
                "object": "model",
                "owned_by": "nvidia"
            }
        ]
    })


@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    if not NVIDIA_API_KEY:
        return jsonify({"error": "NVIDIA_API_KEY not set"}), 500

    data = request.json or {}

    model = data.get("model", DEFAULT_MODEL)
    messages = data.get("messages", [])
    temperature = data.get("temperature", 0.7)
    max_tokens = data.get("max_tokens", 512)

    prompt = messages_to_prompt(messages)

    nvidia_payload = {
        "input": prompt,
        "parameters": {
            "temperature": temperature,
            "max_new_tokens": max_tokens
        }
    }

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }

    url = f"{NVIDIA_BASE_URL}/{model}"

    resp = requests.post(url, headers=headers, json=nvidia_payload)

    if resp.status_code != 200:
        return jsonify({
            "error": f"NVIDIA API error: {resp.text}",
            "status_code": resp.status_code
        }), resp.status_code

    result = resp.json()

    # NVIDIA NIM response text extraction
    output_text = ""
    if isinstance(result, dict):
        output_text = (
            result.get("output_text")
            or result.get("generated_text")
            or result.get("text")
            or ""
        )

    return jsonify(openai_style_response(output_text, model))


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "DeepSeek NVIDIA NIM → OpenAI-compatible proxy",
        "endpoints": [
            "/v1/chat/completions",
            "/v1/models",
            "/health"
        ]
    })


# ================= MAIN =================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
