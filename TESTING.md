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

## Reporting Issues

If you encounter any issues:
1. Check the console for error messages
2. Verify all prerequisites are met
3. Review the TESTING.md troubleshooting section
4. Check backend logs for detailed error information
