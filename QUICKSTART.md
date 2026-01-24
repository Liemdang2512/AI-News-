# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Add Your Gemini API Key

1. Get your API key from: https://makersuite.google.com/app/apikey
2. Open `backend/.env` file
3. Replace the empty value with your key:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

### Step 2: Start the Backend Server

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend running at: http://localhost:8000
📚 API docs at: http://localhost:8000/docs

### Step 3: Start the Frontend

Open a new terminal:

```bash
cd frontend
npm run dev
```

✅ Frontend running at: http://localhost:3000

## 🎯 Using the Application

1. **Enter Search Criteria**:
   - Newspaper names (e.g., "Lao Động, Dân Trí, VTV")
   - Date (DD/MM/YYYY format)
   - Time range (select from dropdown)

2. **View Results**:
   - See filtered articles with titles, categories, and timestamps
   - Select articles you want to summarize

3. **Get AI Summaries**:
   - Click "Tóm tắt" button
   - View formatted markdown summaries

## 📝 Example Search

- **Newspapers**: Lao Động, Dân Trí
- **Date**: 24/01/2026
- **Time Range**: 6h00 đến 8h00

This will find all articles from Lao Động and Dân Trí published between 6:00 AM and 8:00 AM on January 24, 2026.

## 🔧 Troubleshooting

**Backend won't start?**
- Check that you've activated the virtual environment
- Verify your Gemini API key is set in `.env`

**Frontend can't connect?**
- Make sure backend is running first
- Check that `NEXT_PUBLIC_API_URL` in `.env.local` is `http://localhost:8000`

**No articles found?**
- Try a different time range
- Check that the date format is DD/MM/YYYY
- Verify newspaper names are spelled correctly

## 📖 Full Documentation

See [README.md](file:///Users/tanliem/Desktop/App%20crwal/README.md) for complete documentation.
