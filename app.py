from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all origins

# NVIDIA NIM API Configuration
NVIDIA_API_KEY = os.environ.get('NVIDIA_API_KEY', '')
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Model configurations
MODELS = {
    "deepseek-ai/deepseek-r1": {
        "name": "deepseek-ai/deepseek-r1",
        "reasoning": True,
        "description": "DeepSeek R1 with reasoning"
    },
    "deepseek-ai/deepseek-r1_5": {
        "name": "deepseek-ai/deepseek-r1_5",
        "reasoning": True,
        "description": "DeepSeek R1.5 (Updated)"
    },
    "deepseek-ai/deepseek-v3_1": {
        "name": "deepseek-ai/deepseek-v3_1",
        "reasoning": False,
        "description": "DeepSeek V3.1 (Fast, Recommended)"
    },
    "deepseek-ai/deepseek-v3_2": {
        "name": "deepseek-ai/deepseek-v3_2",
        "reasoning": False,
        "description": "DeepSeek V3.2 (Latest)"
    }
}

def filter_reasoning_tokens(content):
    """Remove reasoning/thinking tokens from response"""
    if not content:
        return content
    
    # Remove common reasoning markers
    reasoning_markers = [
        '<think>', '</think>',
        '<reasoning>', '</reasoning>',
        '<thought>', '</thought>',
        '<internal>', '</internal>'
    ]
    
    filtered_content = content
    for marker in reasoning_markers:
        filtered_content = filtered_content.replace(marker, '')
    
    # Remove content between thinking tags
    import re
    filtered_content = re.sub(r'<think>.*?</think>', '', filtered_content, flags=re.DOTALL)
    filtered_content = re.sub(r'<reasoning>.*?</reasoning>', '', filtered_content, flags=re.DOTALL)
    
    return filtered_content.strip()

@app.route('/v1/models', methods=['GET'])
def list_models():
    """List available models"""
    models_list = []
    for model_id, info in MODELS.items():
        models_list.append({
            "id": model_id,
            "object": "model",
            "created": int(datetime.now().timestamp()),
            "owned_by": "nvidia",
            "description": info["description"]
        })
    
    return jsonify({
        "object": "list",
        "data": models_list
    })

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """Proxy chat completions to NVIDIA NIM API"""
    try:
        # Check if API key is configured
        if not NVIDIA_API_KEY:
            return jsonify({"error": "NVIDIA_API_KEY not configured in environment variables"}), 500
        
        data = request.json
        
        # Extract parameters
        model = data.get('model', 'deepseek-ai/deepseek-r1')
        messages = data.get('messages', [])
        stream = data.get('stream', False)
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1024)
        top_p = data.get('top_p', 1.0)
        
        # Check for disable_reasoning flag (custom parameter)
        disable_reasoning = data.get('disable_reasoning', False)
        
        # If user wants to disable reasoning, add system message
        if disable_reasoning and model in MODELS and MODELS[model]["reasoning"]:
            system_msg = {
                "role": "system",
                "content": "You are a helpful assistant. Provide direct answers without showing your reasoning process or thinking steps. Do not use <think> tags or explain your thought process."
            }
            # Insert at the beginning if no system message exists
            if not messages or messages[0].get("role") != "system":
                messages.insert(0, system_msg)
            else:
                # Append to existing system message
                messages[0]["content"] += " " + system_msg["content"]
        
        # Prepare NVIDIA API request
        nvidia_payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": stream
        }
        
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Make request to NVIDIA API
        response = requests.post(
            f"{NVIDIA_BASE_URL}/chat/completions",
            headers=headers,
            json=nvidia_payload,
            stream=stream
        )
        
        # Check for errors from NVIDIA API
        if response.status_code != 200:
            error_text = response.text
            print(f"NVIDIA API Error: {response.status_code} - {error_text}")
            return jsonify({
                "error": f"NVIDIA API error: {error_text}",
                "status_code": response.status_code
            }), response.status_code
        
        if stream:
            def generate():
                for chunk in response.iter_lines():
                    if chunk:
                        if disable_reasoning:
                            # Parse and filter reasoning tokens from stream
                            try:
                                chunk_str = chunk.decode('utf-8')
                                if chunk_str.startswith('data: '):
                                    chunk_str = chunk_str[6:]
                                if chunk_str.strip() == '[DONE]':
                                    yield b'data: [DONE]\n\n'
                                    continue
                                
                                chunk_data = json.loads(chunk_str)
                                if 'choices' in chunk_data:
                                    for choice in chunk_data['choices']:
                                        if 'delta' in choice and 'content' in choice['delta']:
                                            choice['delta']['content'] = filter_reasoning_tokens(
                                                choice['delta']['content']
                                            )
                                yield f"data: {json.dumps(chunk_data)}\n\n".encode('utf-8')
                            except:
                                yield chunk + b'\n'
                        else:
                            yield chunk + b'\n'
            
            return Response(generate(), content_type='text/event-stream')
        else:
            result = response.json()
            
            # Filter reasoning tokens if requested
            if disable_reasoning:
                if 'choices' in result:
                    for choice in result['choices']:
                        if 'message' in choice and 'content' in choice['message']:
                            choice['message']['content'] = filter_reasoning_tokens(
                                choice['message']['content']
                            )
            
            return jsonify(result)
            
    except Exception as e:
        print(f"Error in chat_completions: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "type": type(e).__name__}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        "message": "NVIDIA NIM Proxy Server",
        "endpoints": {
            "/v1/models": "List available models",
            "/v1/chat/completions": "Chat completions",
            "/health": "Health check"
        },
        "available_models": list(MODELS.keys()),
        "features": [
            "Multiple DeepSeek models support",
            "Disable reasoning mode with 'disable_reasoning' parameter",
            "OpenAI-compatible API"
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
