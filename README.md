# NVIDIA NIM Proxy Server for Janitor AI

An OpenAI-compatible proxy server that routes requests to NVIDIA NIM API, supporting multiple DeepSeek models with optional reasoning mode control.

## Features

- ✅ OpenAI-compatible API endpoints
- ✅ Multiple DeepSeek models support
- ✅ **Toggle reasoning/thinking mode on/off**
- ✅ Streaming support
- ✅ Easy deployment on Render.com

## Supported Models

| Model ID | Description | Reasoning |
|----------|-------------|-----------|
| `deepseek-ai/deepseek-r1` | DeepSeek R1 (original) | Yes |
| `deepseek-ai/deepseek-r1-distill-llama-70b` | DeepSeek R1 Distilled 70B | Yes |
| `deepseek-ai/deepseek-v3` | DeepSeek V3 | No |
| `deepseek-ai/deepseek-coder-6.7b-instruct` | DeepSeek Coder 6.7B | No |

## Quick Deploy to Render.com

### Step 1: Create GitHub Repository

1. Create a new repository on GitHub
2. Add these files:
   - `app.py` (the Python proxy server)
   - `requirements.txt` (Python dependencies)
   - `README.md` (this file)

### Step 2: Deploy on Render.com

1. Go to [Render.com](https://render.com) and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `nvidia-nim-proxy` (or any name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free (or paid for better performance)

5. **Add Environment Variable**:
   - Key: `NVIDIA_API_KEY`
   - Value: Your NVIDIA NIM API key (starts with `nvapi-`)

6. Click **"Create Web Service"**

### Step 3: Configure Janitor AI

Once deployed, Render will give you a URL like: `https://nvidia-nim-proxy.onrender.com`

#### Basic Setup (with reasoning):
1. Open Janitor AI
2. Go to Settings → API Settings
3. Select **"OpenAI"** as API type
4. Enter your proxy URL: `https://your-service-name.onrender.com/v1`
5. Enter any dummy API key (like `sk-dummy`)
6. Select model: `deepseek-ai/deepseek-r1`
7. Save and start chatting!

#### Disable Reasoning Mode:

**Method 1: Use a Non-Reasoning Model**
Simply select a model without built-in reasoning:
- `deepseek-ai/deepseek-v3` - Fast, no reasoning tokens
- `deepseek-ai/deepseek-coder-6.7b-instruct` - For coding tasks

**Method 2: Add Custom Parameter** (if Janitor AI supports it)
Add to your request JSON:
```json
{
  "model": "deepseek-ai/deepseek-r1",
  "messages": [...],
  "disable_reasoning": true
}
```

**Method 3: Use System Prompt** (Works on all platforms)
Start your conversation with this system message:
```
You are a helpful assistant. Provide direct answers without showing your reasoning process or thinking steps. Do not use <think> tags.
```

## How Reasoning Mode Works

### With Reasoning (Default for R1 models):
```
User: What's 2+2?

<think>
Let me calculate this...
2 + 2 = 4
</think>

The answer is 4.
```

### Without Reasoning (`disable_reasoning: true`):
```
User: What's 2+2?

The answer is 4.
```

## API Usage Examples

### Basic Request (with reasoning):
```bash
curl https://your-service.onrender.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/deepseek-r1",
    "messages": [
      {"role": "user", "content": "Explain quantum computing"}
    ]
  }'
```

### Request Without Reasoning:
```bash
curl https://your-service.onrender.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/deepseek-r1",
    "messages": [
      {"role": "user", "content": "Explain quantum computing"}
    ],
    "disable_reasoning": true
  }'
```

### Using DeepSeek V3 (no reasoning by default):
```bash
curl https://your-service.onrender.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/deepseek-v3",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

### List All Models:
```bash
curl https://your-service.onrender.com/v1/models
```

## Choosing the Right Model

**For Roleplay/Creative Writing (Janitor AI):**
- ✅ **Recommended**: `deepseek-ai/deepseek-v3` (fast, no thinking tokens)
- ✅ **Alternative**: `deepseek-ai/deepseek-r1` with `disable_reasoning: true`

**For Complex Problem Solving:**
- ✅ `deepseek-ai/deepseek-r1` (keeps reasoning visible)

**For Coding:**
- ✅ `deepseek-ai/deepseek-coder-6.7b-instruct`

**For Best Performance:**
- ✅ `deepseek-ai/deepseek-r1-distill-llama-70b` (balanced)

## Troubleshooting

### Still seeing `<think>` tags?
1. Try using `deepseek-ai/deepseek-v3` instead
2. Add system prompt to disable thinking
3. Ensure `disable_reasoning: true` is in your request

### "Model not found"
- Check the exact model name from the list above
- Visit [NVIDIA Build](https://build.nvidia.com/explore/discover) to see available models

### Slow responses on Free tier
- Render's free tier spins down after inactivity
- First request takes 30-60 seconds to wake
- Upgrade to paid tier for always-on service

### "API key not configured"
- Add `NVIDIA_API_KEY` environment variable in Render
- Restart service after adding the variable

## Advanced Configuration

### Environment Variables
- `NVIDIA_API_KEY` (required): Your NVIDIA NIM API key
- `PORT` (optional): Server port (default: 10000)

### Custom Model Addition
Edit `app.py` and add to the `MODELS` dictionary:
```python
"your-model-id": {
    "name": "your-model-id",
    "reasoning": False,
    "description": "Your model description"
}
```

## Performance Tips

1. **Use V3 for Janitor AI**: Faster responses, no reasoning overhead
2. **Enable Streaming**: Set `"stream": true` for real-time responses
3. **Adjust Temperature**: Lower (0.3-0.7) for consistent responses, higher (0.8-1.0) for creative
4. **Paid Render Plan**: Eliminates cold starts

## Notes

- Free tier sleeps after 15 minutes of inactivity
- First request after sleep: ~30-60 seconds
- Reasoning filter works on streaming and non-streaming requests
- Your NVIDIA API key should start with `nvapi-`

## Get NVIDIA API Key

1. Go to [NVIDIA NGC](https://ngc.nvidia.com)
2. Sign up/Login  
3. Go to "Setup" → "Generate Personal Key"
4. Copy the key (starts with `nvapi-`)

## License

MIT
