# Using Ollama with Third-Party URL Wrappers

This guide explains how to configure MetaGPT to use Ollama through a third-party URL wrapper.

## Background

Ollama's API structure requires endpoints to be accessed via paths like:
- `/api/chat` for chat completions
- `/api/generate` for text generation
- `/api/embeddings` for embeddings

When using a third-party URL wrapper or proxy, you need to ensure the URL structure is correctly maintained.

## Configuration Options

### Option 1: Include `/api` in the Base URL (Recommended)

```yaml
llm:
  api_type: "ollama"
  model: "llama2"
  base_url: "http://localhost:8989/ollama/api"  # Note the /api at the end
  api_key: "not-needed-for-ollama"
```

With this configuration, MetaGPT will correctly form URLs like:
- `http://localhost:8989/ollama/api/chat`
- `http://localhost:8989/ollama/api/generate`

### Option 2: Let MetaGPT Handle the `/api` Path

```yaml
llm:
  api_type: "ollama"
  model: "llama2"
  base_url: "http://localhost:8989/ollama"  # No /api at the end
  api_key: "not-needed-for-ollama"
```

MetaGPT will automatically insert `/api` before the specific endpoint, resulting in:
- `http://localhost:8989/ollama/api/chat`
- `http://localhost:8989/ollama/api/generate`

### Option 3: Using the Proxy Parameter

```yaml
llm:
  api_type: "ollama"
  model: "llama2"
  base_url: "http://localhost:11434"  # Direct Ollama URL
  proxy: "http://localhost:8989"      # Proxy server
  api_key: "not-needed-for-ollama"
```

Note: The proxy parameter is passed to the HTTP client but may not work with all wrapper configurations.

## Troubleshooting

If you encounter a 404 error, check that:

1. Your wrapper correctly forwards requests to Ollama
2. The URL structure includes `/api` before the specific endpoint (e.g., `/chat`, `/generate`)
3. Your wrapper preserves the complete path when forwarding requests

## Example Wrapper Configuration

If you're implementing a wrapper for Ollama, ensure it correctly handles the path structure:

```javascript
// Example Node.js proxy for Ollama
app.use('/ollama', createProxyMiddleware({
  target: 'http://localhost:11434',
  pathRewrite: {
    '^/ollama': '/api'  // Rewrite /ollama to /api
  },
  changeOrigin: true,
}));
```

Or alternatively:

```javascript
// Pass through the complete path
app.use('/ollama', createProxyMiddleware({
  target: 'http://localhost:11434',
  pathRewrite: {
    '^/ollama': ''  // Remove /ollama prefix
  },
  changeOrigin: true,
}));
```

## Related Configuration Files

For a complete example configuration, see:
- `config/examples/ollama-third-party-wrapper.yaml`
