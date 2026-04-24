# 🎯 Interview Prep Assistant

A multi-agent AI system that helps you prepare for job interviews by researching companies, generating tailored questions, fetching real past interview questions, evaluating your answers, and giving actionable feedback — all powered by Groq's LLaMA 3.3 model.

---

## 🚀 Live Demo

> Deployed on Streamlit — [Your Streamlit URL here]

---

## ✨ Features

- 🔍 **Company Research** — Automatically researches company culture, recent news, and role expectations
- 📚 **Historical Questions** — Fetches real past interview and coding round questions for your target company
- 🤖 **AI Question Generator** — Generates role-specific behavioural, technical, and situational questions
- 📄 **Resume Parser** — Upload your resume (PDF/TXT) to personalise all questions and feedback
- ⚖️ **Judge Agent** — Scores your answers on clarity, depth, relevance, STAR format, and role fit
- 🎭 **Mock Interview Mode** — Simulates a real interview with follow-up questions
- 🗺️ **Study Roadmap** — Generates a personalised day-by-day prep plan based on your weak areas
- 💰 **Salary Negotiation Prep** — Research market rates and negotiation scripts
- 📊 **Progress Tracker** — Tracks your improvement across sessions over time
- 🏢 **Company Insider Tips** — Deep-dives into what interviewers actually look for
- 👥 **Peer Comparison** — Benchmarks your scores against other users anonymously

---

## 🏗️ Architecture — Multi-Agent System

```
User Input (Company + Role + Optional Resume)
        │
        ▼
  Orchestrator Agent
  ┌─────┬──────┬──────┬──────┐
  │     │      │      │      │
  ▼     ▼      ▼      ▼      ▼
Researcher  Historical  Question  Company
 Agent      Fetcher    Generator  Insider
             Agent      Agent     Agent
  │     │      │      │      │
  └─────┴──────┴──────┴──────┘
        │
        ▼
  Validation Gate
        │
        ▼
  Merged Question Set ◄── Resume Parser (async, background)
        │
        ▼
  User Submits Answer
        │
        ▼
   Judge Agent
        │
   Score ≥ 7? ──No──► Feedback + Refine Loop (max 5 iterations)
        │
       Yes
        │
        ▼
  Final Feedback Report
        │
        ▼
  Roadmap Agent + Progress Tracker
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | Groq API — LLaMA 3.3 70B Versatile |
| **Web Search** | Serper API (Google Search) |
| **Backend** | Python 3.10+ · FastAPI |
| **Task Queue** | Celery + Redis |
| **Cache** | Redis (ioredis) |
| **Database** | PostgreSQL + SQLAlchemy |
| **PDF Parsing** | PyMuPDF (fitz) |
| **Validation** | Pydantic v2 |
| **Observability** | OpenTelemetry |
| **Frontend** | Vanilla HTML/CSS/JS |
| **Deployment** | Streamlit |

---

## 📁 Project Structure

```
interview-prep-assistant/
├── agents/
│   ├── orchestrator.py          # Central controller, routes all tasks
│   ├── researcher.py            # Company research via web search
│   ├── historical_fetcher.py    # Past interview Q retrieval
│   ├── question_generator.py    # LLM-based question generation
│   ├── judge.py                 # Answer evaluation & scoring
│   ├── resume_parser.py         # Resume parsing & gap analysis
│   ├── mock_conductor.py        # Stateful mock interview simulation
│   ├── roadmap.py               # Personalised study plan generator
│   ├── salary_negotiator.py     # Market salary research
│   ├── peer_comparison.py       # Anonymous peer benchmarking
│   ├── company_insider.py       # Deep company research
│   ├── answer_template.py       # STAR-format answer templates
│   └── progress_tracker.py      # Cross-session progress tracking
├── tools/
│   ├── web_search.py            # Serper API wrapper
│   ├── cache.py                 # Redis cache helpers
│   ├── deduplicator.py          # Fuzzy string deduplication
│   └── retry.py                 # Exponential backoff retry
├── validation/
│   └── gate.py                  # Output quality validation
├── models/
│   ├── schemas.py               # All Pydantic models
│   ├── peer_scores.py           # SQLAlchemy peer scores table
│   └── user_progress.py         # SQLAlchemy progress table
├── api/
│   ├── server.py                # FastAPI app setup
│   └── routes.py                # All API endpoints
├── queue/
│   └── workers.py               # Celery worker definitions
├── observability/
│   └── tracing.py               # OpenTelemetry spans
├── ui/
│   ├── index.html               # Main frontend (5 views)
│   ├── style.css                # Dark theme styles
│   └── app.js                   # Frontend logic
├── tests/
│   ├── test_agents.py
│   ├── test_validation.py
│   └── test_judge.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- Redis (running locally or via Docker)
- PostgreSQL
- Groq API key — [console.groq.com](https://console.groq.com)
- Serper API key — [serper.dev](https://serper.dev)

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/interview-prep-assistant.git
cd interview-prep-assistant
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
# Edit .env and add your API keys
```

Your `.env` should look like:
```env
GROQ_API_KEY=your_groq_key_here
SERPER_API_KEY=your_serper_key_here
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/interview_prep
SECRET_KEY=your-secret-key
DEBUG=true
```

### 5. Set up the database
```bash
python -m alembic upgrade head
# or
python models/init_db.py
```

### 6. Start Redis (if not running)
```bash
# Using Docker
docker run -d -p 6379:6379 redis:alpine

# or install locally on Mac
brew install redis && redis-server
```

### 7. Start Celery worker
```bash
celery -A queue.workers worker --loglevel=info
```

### 8. Run the application
```bash
uvicorn api.server:app --reload --port 8000
```

Visit `http://localhost:8000`

---

## 🌐 Deploying on Streamlit

```bash
pip install streamlit
streamlit run streamlit_app.py
```

For Streamlit Cloud deployment:
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Add all environment variables in the Streamlit secrets manager
5. Deploy

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ | Groq API key for LLM calls |
| `SERPER_API_KEY` | ✅ | Serper API key for web search |
| `REDIS_URL` | ✅ | Redis connection string |
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `SECRET_KEY` | ✅ | App secret key |
| `DEBUG` | ❌ | Enable debug mode (default: false) |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/session/start` | Start a new prep session |
| `GET` | `/api/session/:id/questions` | Get generated question set |
| `POST` | `/api/session/upload-resume` | Upload and parse resume |
| `GET` | `/api/session/:id/resume-status` | Poll resume parsing status |
| `POST` | `/api/session/:id/evaluate` | Submit answer for judging |
| `POST` | `/api/session/:id/mock/start` | Start mock interview |
| `POST` | `/api/session/:id/mock/respond` | Send mock interview response |
| `POST` | `/api/session/:id/roadmap` | Generate study roadmap |
| `POST` | `/api/session/:id/salary` | Get salary negotiation prep |
| `GET` | `/api/session/:id/insider-tips` | Get company insider tips |
| `GET` | `/api/session/:id/template/:qid` | Get answer template |
| `GET` | `/api/user/:id/progress` | Get progress tracker data |

---

## 🧪 Running Tests

```bash
pytest tests/ -v
pytest tests/test_agents.py -v
pytest tests/test_judge.py -v
```

---

## 📦 requirements.txt

```
groq
fastapi
uvicorn[standard]
celery[redis]
redis
sqlalchemy[asyncio]
asyncpg
pydantic>=2.0
pymupdf
httpx
opentelemetry-sdk
opentelemetry-api
python-multipart
python-dotenv
alembic
pytest
pytest-asyncio
streamlit
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

Built with ❤️ using Groq, FastAPI, and a lot of multi-agent design thinking.
