# Phoenix Observability Setup

## Overview

Phoenix is now integrated to provide observability for all OpenAI LLM calls. You can view traces, messages, responses, token usage, and latency in the Phoenix UI.

## How It Works

1. **Phoenix launches automatically** when you start the backend server
2. **OpenAI calls are automatically traced** - no code changes needed in your service
3. **View traces in the Phoenix UI** at the URL printed in the console

## Starting the Backend

When you run the backend, you'll see:

```bash
🔭 Phoenix is running at: http://localhost:6006
   View your LLM traces and evaluations in the Phoenix UI

📡 OpenTelemetry traces will be sent to Phoenix
   Collector endpoint: http://127.0.0.1:6006

✅ OpenAI instrumented for tracing
```

This confirms that:
1. ✅ Phoenix UI is running on port 6006
2. ✅ OpenTelemetry collector is ready to receive traces
3. ✅ OpenAI SDK is instrumented

## Viewing LLM Traces

1. Open http://localhost:6006 in your browser
2. Navigate to the **Traces** tab
3. You'll see all OpenAI API calls with:
   - **Input messages** (system prompt, user prompt)
   - **Output response** (parsed structured output)
   - **Model used** (gpt-4o-mini, gpt-5.1-mini, etc.)
   - **Token usage** (prompt tokens, completion tokens, total)
   - **Latency** (time taken for the API call)
   - **Status** (success/error)

## What Gets Traced

Every call to `openai_client.beta.chat.completions.parse()` in `openai_service.py` is automatically traced:

- The complete prompt sent to OpenAI
- The full response received
- Token counts and costs
- Timing information
- Any errors or exceptions

## Useful Features

### 1. **Trace Search & Filter**
- Search traces by model, status, or date range
- Filter by success/failure
- Sort by latency, tokens, or timestamp

### 2. **Detailed Trace View**
- Click any trace to see the full conversation
- View the structured output schema
- See the exact prompt template used
- Check token breakdown

### 3. **Analytics**
- View aggregate statistics
- Track token usage over time
- Monitor API latency trends
- Identify failing requests

## Troubleshooting

### Phoenix UI not accessible?

Check that port 6006 is not in use:
```bash
netstat -ano | findstr :6006
```

### No traces appearing?

**Step 1: Verify Phoenix is running**
Look for this in the backend logs:
```
🔭 Phoenix is running at: http://localhost:6006
📡 OpenTelemetry traces will be sent to Phoenix
✅ OpenAI instrumented for tracing
```

**Step 2: Trigger an LLM call**
1. Select a paper in the UI
2. Load the paper content
3. Click "Analyze Paper"
4. Look for this in backend logs: `🤖 Starting LLM analysis...`

**Step 3: Check Phoenix UI**
1. Open http://localhost:6006 in your browser
2. Click "Traces" in the left sidebar
3. You should see a trace appear after the analysis completes
4. The trace will show the model, input messages, output, and token usage

**Step 4: Verify collector endpoint**
Check that the backend can reach the Phoenix collector:
```bash
curl http://localhost:6006/v1/traces
```
Should return: `Method Not Allowed` (this is expected - it confirms the endpoint exists)

**Common Issues:**

1. **Traces delayed**: Phoenix batches traces. Wait 5-10 seconds after the LLM call completes.
2. **Wrong endpoint**: Make sure Phoenix is using the default port (6006)
3. **Firewall blocking**: Check Windows Firewall isn't blocking localhost connections
4. **OpenAI client created too early**: The instrumentation must happen before the first OpenAI client is created

## Advanced Configuration

### Change Phoenix Port

Edit `backend/main.py`:
```python
phoenix_session = px.launch_app(port=7007)  # Change port
```

### Disable Phoenix

Comment out Phoenix initialization in `backend/main.py`:
```python
# phoenix_session = px.launch_app()
# OpenAIInstrumentor().instrument()
```

Or set environment variable:
```bash
PHOENIX_TELEMETRY_ENABLED=false
```

## Resources

- [Phoenix Documentation](https://arize.com/docs/phoenix)
- [OpenAI Integration Guide](https://arize.com/docs/phoenix/tracing/integrations-tracing/openai)
- [Phoenix GitHub](https://github.com/Arize-ai/phoenix)
