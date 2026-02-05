# Phoenix Windows File Locking Issue - Fix Applied

## Problem
Phoenix was creating temporary database files that Windows couldn't clean up during hot reloads, causing `PermissionError: [WinError 32]` errors.

## Solution Applied
The code has been updated to use FastAPI's lifespan context manager, which:
1. Initializes Phoenix only once during startup
2. Uses persistent storage instead of temp files
3. Avoids cleanup issues during hot reloads

## Next Step Required
**Please restart the backend server** to apply the fix:

### Windows PowerShell:
```bash
# Stop the current server (Ctrl+C in the terminal)
# Then restart:
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

## What Changed

### Before:
- Phoenix initialized at module level
- Used temp files (cleaned up on reload, causing Windows errors)
- No proper lifecycle management

### After:
- Phoenix initialized in FastAPI lifespan context
- Uses persistent database in `backend/data/phoenix/`
- Proper startup/shutdown handling
- Graceful error handling if Phoenix fails to start

## Expected Behavior After Restart

You should see:
```
🔭 Phoenix is running at: http://localhost:6006/
   View your LLM traces and evaluations in the Phoenix UI

📡 OpenTelemetry traces will be sent to Phoenix
   Default endpoint: http://127.0.0.1:6006/v1/traces

✅ OpenAI instrumented for tracing
```

**NO MORE** `PermissionError` messages during hot reloads!

## Verification

After restart, try making a code change and watch for hot reload - you should see:
```
WARNING: WatchFiles detected changes in 'some_file.py'. Reloading...
```

And then immediately:
```
Application startup complete.
```

No permission errors!

## If Phoenix Fails to Start

The application will continue to work without observability:
```
⚠️  Phoenix initialization failed: [error message]
   Continuing without observability...
```

This is intentional - the app remains functional even if Phoenix has issues.

## Phoenix Data Location

Phoenix database files are now stored in:
```
backend/data/phoenix/
```

This directory is git-ignored and will persist across reloads.
