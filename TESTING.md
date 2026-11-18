# Testing Guide

This guide will help you test the Research Paper Analyzer application.

## Prerequisites

Before testing, ensure you have:

1. ✅ Python 3.9+ installed
2. ✅ Node.js 18+ installed
3. ✅ OpenAI API key configured in `backend/.env`
4. ✅ Both backend and frontend servers running

## Starting the Application

### Option 1: Using Startup Scripts (Windows)

Open two terminals:

**Terminal 1 - Backend:**
```bash
start-backend.bat
```

**Terminal 2 - Frontend:**
```bash
start-frontend.bat
```

### Option 2: Using Startup Scripts (Mac/Linux)

Open two terminals:

**Terminal 1 - Backend:**
```bash
chmod +x start-backend.sh
./start-backend.sh
```

**Terminal 2 - Frontend:**
```bash
chmod +x start-frontend.sh
./start-frontend.sh
```

### Option 3: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Test Checklist

### 0. Optional Local vLLM Smoke Test

This validates only the Docker Compose-hosted local model endpoint. It does not
wire the model into the backend provider registry yet.

Start the local model service:
```bash
bash scripts/start-local-vllm.sh
```

In another terminal, run:
```bash
bash scripts/smoke-local-vllm.sh
```

Expected result: the script waits for `http://localhost:9001/v1/models`, calls
`/v1/chat/completions`, and prints a non-empty response.

### 1. Backend API Tests

Visit `http://localhost:8000/docs` to access the interactive API documentation.

#### Test 1.1: Health Check
- Endpoint: `GET /health`
- Expected: `{"status": "healthy"}`

#### Test 1.2: Fetch Papers
- Endpoint: `GET /api/papers`
- Expected: Array of paper objects with titles, authors, and ArXiv URLs
- Verify: At least one paper is returned

#### Test 1.3: Parse Paper (Example)
- Endpoint: `GET /api/papers/1706.03762/parse?arxiv_url=https://arxiv.org/abs/1706.03762`
- Expected: Success response with markdown content
- Note: This is the famous "Attention Is All You Need" paper

#### Test 1.4: Analyze Paper
- Endpoint: `POST /api/papers/analyze`
- Body: `{"markdown": "Sample paper content here..."}`
- Expected: Success response with AI-generated summary
- Verify: Summary includes key sections

### 2. Frontend UI Tests

Visit `http://localhost:5173`

#### Test 2.1: Paper List Loading
1. Open the application
2. Wait for papers to load
3. ✅ Verify: Paper cards are displayed
4. ✅ Verify: Each card shows title and authors
5. ✅ Verify: Loading spinner appears briefly during fetch

#### Test 2.2: Paper Selection
1. Click on any paper card
2. ✅ Verify: Detail view opens
3. ✅ Verify: Paper title and authors are displayed
4. ✅ Verify: "Load Paper Content" button is visible
5. ✅ Verify: "Back to List" button works

#### Test 2.3: PDF Parsing
1. Select a paper
2. Click "Load Paper Content"
3. ✅ Verify: Loading indicator appears
4. ✅ Verify: Markdown content is displayed after loading
5. ✅ Verify: Content is properly formatted
6. ✅ Verify: "Analyze Paper" button becomes available

#### Test 2.4: AI Analysis
1. After loading paper content
2. Click "Analyze Paper"
3. ✅ Verify: Button shows "Analyzing..." state
4. ✅ Verify: AI summary appears in blue highlighted box
5. ✅ Verify: Summary includes structured sections
6. ✅ Verify: Summary is informative and relevant

#### Test 2.5: Error Handling
1. Try selecting a paper without valid ArXiv URL
2. ✅ Verify: Error message is displayed
3. ✅ Verify: App doesn't crash

#### Test 2.6: Navigation Flow
1. Browse papers → Select paper → Load content → Analyze → Back to list
2. ✅ Verify: All transitions are smooth
3. ✅ Verify: State is preserved correctly

### 3. Integration Tests

#### Test 3.1: Full User Flow
1. ✅ Open application
2. ✅ Wait for papers to load from HuggingFace
3. ✅ Click on a paper (e.g., first paper in the list)
4. ✅ Click "Load Paper Content"
5. ✅ Wait for PDF to download and parse (may take 10-30 seconds)
6. ✅ Verify markdown content is readable
7. ✅ Click "Analyze Paper"
8. ✅ Wait for AI analysis (may take 5-15 seconds)
9. ✅ Verify summary includes:
   - Main Contribution
   - Methodology
   - Key Results
   - Significance
10. ✅ Click "Back to List"
11. ✅ Select a different paper and repeat

#### Test 3.2: Multiple Papers
1. Test with at least 3 different papers
2. ✅ Verify each parses correctly
3. ✅ Verify each generates unique summaries

### 4. Performance Tests

#### Test 4.1: Initial Load Time
- ✅ Measure time to load paper list
- Expected: < 5 seconds

#### Test 4.2: PDF Parsing Time
- ✅ Measure time to parse a typical paper
- Expected: 10-30 seconds depending on paper size

#### Test 4.3: AI Analysis Time
- ✅ Measure time to generate summary
- Expected: 5-15 seconds

### 5. Edge Cases

#### Test 5.1: Large Papers
- Select a paper with many pages
- ✅ Verify: Content truncation works properly
- ✅ Verify: Analysis still completes

#### Test 5.2: Network Errors
- Stop backend server while frontend is running
- ✅ Verify: Frontend shows appropriate error messages
- ✅ Verify: App remains usable after reconnection

#### Test 5.3: Invalid ArXiv URLs
- Test with a paper that doesn't have a valid ArXiv link
- ✅ Verify: Error is handled gracefully

## Common Issues and Solutions

### Issue: Papers not loading
**Solution:** 
- Check backend is running on port 8000
- Check browser console for CORS errors
- Verify HuggingFace website is accessible

### Issue: PDF parsing fails
**Solution:**
- Verify ArXiv URL is valid
- Check if paper is publicly available
- Some papers may have download restrictions

### Issue: OpenAI analysis fails
**Solution:**
- Verify OPENAI_API_KEY in backend/.env
- Check API key has available credits
- Verify network connection to OpenAI

### Issue: Frontend build errors
**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Issue: Backend import errors
**Solution:**
```bash
cd backend
deactivate  # if in venv
rm -rf venv
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

## Manual Testing Checklist

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] API documentation accessible at /docs
- [ ] Papers load from HuggingFace
- [ ] Can select and view paper details
- [ ] PDF parsing works for at least one paper
- [ ] AI analysis generates relevant summary
- [ ] Can navigate back to paper list
- [ ] Error messages display appropriately
- [ ] UI is responsive and intuitive

## Automated Testing (Future Enhancement)

For production, consider adding:
- Unit tests for backend services (pytest)
- Frontend component tests (Jest, React Testing Library)
- E2E tests (Playwright, Cypress)
- API integration tests

## Success Criteria

✅ All manual tests pass
✅ No console errors during normal operation
✅ UI is responsive and user-friendly
✅ Papers parse correctly
✅ AI summaries are informative
✅ Error handling works properly

## Testing discovery & company-profiled research (P1 + P2)

These features were added in the P1/P2 roadmap phases. Easiest setup: `docker compose up --build backend frontend`, then open `http://localhost:5173`.

### Backend unit tests (no API keys needed)

```powershell
cd backend
.\venv\Scripts\python.exe test_source_paper.py
.\venv\Scripts\python.exe test_openalex_provider.py
.\venv\Scripts\python.exe test_pdf_url_parse.py
.\venv\Scripts\python.exe test_add_paper_generalized.py
.\venv\Scripts\python.exe test_company_profiles.py
.\venv\Scripts\python.exe test_app_improve.py
.\venv\Scripts\python.exe test_llm_models.py
```

Each script prints an "all tests passed" line on success. (LLM calls are mocked; no keys or network needed except your local venv.)

### From the UI (http://localhost:5173)

1. **Discover tab → keyword search.** Type e.g. `retrieval augmented generation`, click **Search OpenAlex**. You should see results with `openalex` / `open access` badges. Click **Add** on one — it lands in the Papers tab with source badges.
2. **Create a company profile.** Discover tab → **New profile**. Give it a name, and at minimum a couple of *watch topics* (one per line), e.g. `retrieval augmented generation` and `small language models on-device`. Optionally fill in description, tech stack, strategic questions, and assumptions (assumptions are used to flag "surprise-risk" papers).
3. **Company-profiled discovery.** With the profile selected, keep "Score results for strategic fit" on (Score top N = 3) and click **Discover for company**. Each watch topic is searched on OpenAlex; the top results get an LLM strategic-fit verdict — a colored badge like `analyze · 80/100` plus a summary of opportunities/threats and any challenged assumptions. *(Requires a valid LLM key for the `strategic_fit` role — configure via the gear icon.)*
4. **App-improvement discovery.** Discover tab → **App improvement**. Paste an app description and an intended improvement (no company profile needed). Click **Find fitting papers**. The backend derives academic search topics, searches OpenAlex, ranks scored papers by fit, and **saves the run** under `backend/data/app_improve/{run_id}/` (`run.json` + `report.md`). Reopen, download markdown, or delete from the **Saved reports** dropdown. *(Uses `app_improve_topics` + `strategic_fit` LLM roles.)*
5. **Add + parse a discovered paper.** Add a result to the library, open it in Papers, click "Load Paper Content" — the open-access PDF is downloaded from its `pdf_url` and parsed (no arXiv involved).
6. **Generalized add.** Papers tab → Add Paper: paste a DOI (e.g. `10.7717/peerj.4375`), a doi.org URL, an OpenAlex URL, or a direct `.pdf` link.

### From the API (http://localhost:8000/docs)

```powershell
# Create a profile
$body = @{ name = "Acme AI"; watch_topics = @("retrieval augmented generation") } | ConvertTo-Json
Invoke-RestMethod -Method Post http://localhost:8000/api/profiles -ContentType "application/json" -Body $body

# Discover for the profile (score top 2 results; costs LLM calls)
Invoke-RestMethod "http://localhost:8000/api/profiles/acme-ai/discover?limit_per_topic=3&score_top=2"

# Find papers for an app + improvement direction (costs LLM calls)
$appBody = @{
  app_description = "Voice notes app for clinicians that drafts SOAP notes"
  improvement_direction = "Reduce hallucination in generated clinical summaries"
  score_top = 3
} | ConvertTo-Json
Invoke-RestMethod -Method Post http://localhost:8000/api/app-improve/discover -ContentType "application/json" -Body $appBody

# List and fetch saved app-improvement reports
Invoke-RestMethod http://localhost:8000/api/app-improve/runs
Invoke-RestMethod http://localhost:8000/api/app-improve/runs/<run_id>
Invoke-RestMethod http://localhost:8000/api/app-improve/runs/<run_id>/markdown

# Add a paper by DOI, then score it against the profile
Invoke-RestMethod -Method Post http://localhost:8000/api/papers/add -ContentType "application/json" -Body (@{ doi = "10.7717/peerj.4375" } | ConvertTo-Json)
Invoke-RestMethod -Method Post "http://localhost:8000/api/profiles/acme-ai/score/openalex:W2741809807"
```

Expected: profile create returns the profile with a slug id; discover returns deduped papers grouped by watch topic (scored ones include `strategic_fit`); scoring returns `fit_score`, `recommended_action`, opportunities, threats, and challenged assumptions — and `from_cache: true` on the second call. App-improve discover returns derived `topics_searched` plus papers ranked by `strategic_fit.fit_score`, and persists the run (`run_id`) for later list/get/markdown.

## Reporting Issues

If you encounter any issues:
1. Check the console for error messages
2. Verify all prerequisites are met
3. Review the TESTING.md troubleshooting section
4. Check backend logs for detailed error information
