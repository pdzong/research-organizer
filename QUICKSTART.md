# Quick Start Guide

Get the Research Paper Analyzer up and running in 5 minutes!

## 🚀 Quick Setup (Windows)

1. **Get your OpenAI API Key**
   - Visit https://platform.openai.com/api-keys
   - Create a new API key
   - Copy it

2. **Configure Backend**
   ```bash
   cd backend
   notepad .env
   ```
   Add your key:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```

3. **Start Backend** (Terminal 1)
   ```bash
   start-backend.bat
   ```
   Wait until you see: "Application startup complete"

4. **Start Frontend** (Terminal 2)
   ```bash
   start-frontend.bat
   ```
   Wait until you see: "Local: http://localhost:5173"

5. **Open Browser**
   - Go to http://localhost:5173
   - Done! 🎉

## 🚀 Quick Setup (Mac/Linux)

1. **Get your OpenAI API Key**
   - Visit https://platform.openai.com/api-keys
   - Create a new API key
   - Copy it

2. **Configure Backend**
   ```bash
   cd backend
   nano .env
   ```
   Add your key:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```
   Save: Ctrl+X, then Y, then Enter

3. **Start Backend** (Terminal 1)
   ```bash
   chmod +x start-backend.sh
   ./start-backend.sh
   ```
   Wait until you see: "Application startup complete"

4. **Start Frontend** (Terminal 2)
   ```bash
   chmod +x start-frontend.sh
   ./start-frontend.sh
   ```
   Wait until you see: "Local: http://localhost:5173"

5. **Open Browser**
   - Go to http://localhost:5173
   - Done! 🎉

## 📖 How to Use

### Step 1: Browse Papers
- The app loads papers from HuggingFace automatically
- Scroll through the list of recent research papers

### Step 2: Select a Paper
- Click on any paper card that interests you
- You'll see the paper's metadata (title, authors, ArXiv ID)

### Step 3: Load Content
- Click the "Load Paper Content" button
- Wait 10-30 seconds while the PDF is downloaded and parsed
- The paper content will appear in markdown format

### Step 4: Analyze
- Click the "Analyze Paper" button
- Wait 5-15 seconds for AI analysis
- Read the structured summary including:
  - Main Contribution
  - Methodology
  - Key Results
  - Significance

### Step 5: Explore More
- Click "Back to List" to choose another paper
- Repeat!

## 🎯 Example Papers to Try

1. **"Attention Is All You Need"** - ArXiv: 1706.03762
   - The famous Transformer paper
   - Good test for the system

2. **Latest Papers**
   - Try any of the papers from today's HuggingFace list
   - Most should work well

## ⚠️ Troubleshooting

### Papers won't load?
→ Make sure backend is running (check Terminal 1)
→ Should see "Application startup complete"

### Can't parse PDF?
→ Some papers may have download restrictions
→ Try a different paper

### Analysis fails?
→ Check your OpenAI API key in `backend/.env`
→ Make sure you have API credits

### Port already in use?
→ Backend: Something is using port 8000
→ Frontend: Something is using port 5173
→ Close other apps or change ports in config

## 🔧 Ports Used

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:5173

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed information
- Check [TESTING.md](TESTING.md) for comprehensive testing guide
- Explore the API docs at http://localhost:8000/docs

## 💡 Tips

- The first paper load may take longer (downloading dependencies)
- Larger papers take longer to parse
- Keep both terminals open while using the app
- Check console for any error messages

Enjoy analyzing papers! 🎓✨
