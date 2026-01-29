# Documentation Index
# AI News Aggregator

**Project:** AI-powered Vietnamese News Aggregator  
**Version:** 3.0  
**Last Updated:** 2026-01-29

---

## 📚 Documentation Structure

```
.agent/
├── SESSION_SUMMARY.md          # Latest development session summary
├── docs/
│   ├── PRD.md                  # Product Requirements Document
│   ├── IMPLEMENTATION_PLAN.md  # Technical implementation details
│   ├── TASK.md                 # Task tracking and sprint planning
│   └── README.md               # This file
```

---

## 📖 Quick Links

### For Product Managers
- **[PRD.md](./PRD.md)** - Complete product requirements and feature specifications
- **[TASK.md](./TASK.md)** - Sprint planning, task tracking, and metrics

### For Developers
- **[IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)** - Technical architecture and implementation details
- **[SESSION_SUMMARY.md](../SESSION_SUMMARY.md)** - Latest development session notes

### For Users
- **USER_MANUAL.md** (Coming soon) - Step-by-step user guide

---

## 🎯 Project Overview

### What is this?
An intelligent news aggregation platform that helps Vietnamese users efficiently consume news from multiple sources with AI-powered features:
- Multi-source news aggregation (10+ Vietnamese newspapers)
- AI-powered summarization using Google Gemini
- Semantic duplicate detection across sources
- Official source verification with Báo Nhân Dân
- Real-time progress tracking

### Key Features
1. **Smart Aggregation:** Fetch articles from multiple sources with date/time filtering
2. **AI Summarization:** Generate concise summaries using Gemini 2.0 Flash
3. **Duplicate Detection:** Group similar articles about the same event
4. **Source Verification:** Cross-reference with official Báo Nhân Dân
5. **Progress Tracking:** Real-time updates during processing

---

## 🏗️ Architecture

### Tech Stack
- **Backend:** FastAPI (Python) + Google Gemini API
- **Frontend:** Next.js 14 (React) + Tailwind CSS
- **Communication:** REST API + Server-Sent Events (SSE)

### System Flow
```
User Input → RSS Matching → Article Fetching → AI Processing → Display Results
                                                      ↓
                                        [Deduplication + Verification]
```

---

## 📊 Current Status

### Completed Phases
- ✅ **Phase 1:** Core functionality (RSS aggregation, AI summarization)
- ✅ **Phase 2:** Advanced features (duplicate detection, source verification)
- ✅ **Phase 3:** Real-time progress tracking

### In Progress
- 🔄 **Phase 4:** Documentation and polish

### Planned
- 📋 **Phase 5:** Analytics and insights
- 📋 **Phase 6:** Personalization features
- 📋 **Phase 7:** Collaboration tools

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Google Gemini API key

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Access
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📝 Development Guidelines

### Code Style
- **Python:** PEP 8
- **TypeScript:** ESLint + Prettier
- **Commits:** Conventional Commits

### Testing
- Unit tests: `pytest` (backend), `jest` (frontend)
- Integration tests: Manual testing + automated scripts
- E2E tests: Playwright (planned)

### Deployment
- **Frontend:** Vercel (automatic from main branch)
- **Backend:** Local/Cloud (manual deployment)

---

## 🐛 Known Issues

See [TASK.md](./TASK.md#known-issues) for current issues and their priorities.

---

## 📞 Support

For questions or issues:
1. Check documentation in this folder
2. Review [SESSION_SUMMARY.md](../SESSION_SUMMARY.md) for recent changes
3. Contact development team

---

## 📄 License

Internal project - All rights reserved

---

**Maintained by:** Development Team  
**Last Review:** 2026-01-29
