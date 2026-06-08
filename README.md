# PopuSim 🤖

PopuSim is a full-stack website user simulation platform. It takes a target website URL, dynamically generates a population of autonomous user personas, runs parallel headless browser sessions in Playwright, collects behavioral drop-off data/console bugs, and synthesizes an intelligence report featuring Net Promoter Score (NPS), conversion funnels, willingness-to-pay (WTP) studies, and interactive debugging logs.

## Core Pillars
1. **Agentic Browsing**: Concurrently run Playwright headless browsers driven by AI.
2. **Synthetic Persona Modeling**: Dynamic archetypes (Scanners, Skeptics, Novices, Power Users) customized to your website content.
3. **Behavioral Simulation**: Emergent goal completion, form completions, and drop-off reasons logged verbatim.
4. **Natural QA Testing**: Capture client-side Javascript crashes and resource failures through organic navigation paths.
5. **Predictive Analytics**: Automated NPS calculation, Willingness-to-pay metrics, and engagement heatmaps.

---

## Folder Structure
```
popusim/
├── backend/
│   ├── routes/          # REST & WebSocket API endpoints
│   ├── main.py          # FastAPI application bootstrapper
│   ├── config.py        # Settings loader
│   ├── db.py            # SQLite schema initialization
│   ├── models.py        # Pydantic schemas
│   ├── ingestion.py     # HTML crawler & scraper
│   ├── persona_factory.py # Persona generator (Claude / fallback)
│   ├── agent.py         # Playwright autonomous loop
│   ├── orchestrator.py  # Swarm parallel manager
│   ├── synthesis.py     # Intelligence report generator
│   └── requirements.txt # Python package dependencies
├── frontend/
│   ├── src/             # React App and components
│   ├── index.html       # Entry template with Tailwind CSS CDN
│   ├── package.json     # Node configurations
│   └── vite.config.js   # Vite server proxy wiring
├── screenshots/          # Visual step logs directory
├── .env.example         # Template configuration env
└── README.md            # You are here
```

---

## Getting Started

### 1. Environment Configuration
Copy the env template in the root of the `popusim` directory:
```bash
cp .env.example .env
```
Inside `.env`, you can add your `GEMINI_API_KEY`:
```env
GEMINI_API_KEY=your-gemini-key-here
```
> [!NOTE]
> **Zero Configuration Sandbox Mode**:
> If the `GEMINI_API_KEY` is left blank, PopuSim automatically defaults to a local **Simulation Sandbox Mode** (Mock Mode). It executes deterministic behavioral logic models and local statistical analyzers to run agents, log screenshots, and produce intelligence reports, enabling you to test the entire application end-to-end without an API key.

### 2. Backend Setup
Python 3.10+ is required.
```bash
# Navigate to backend and install requirements
pip install -r backend/requirements.txt

# Install Playwright browser dependencies
python -m playwright install chromium

# Launch FastAPI server
python -m uvicorn backend.main:app --reload --port 8000
```
The server will run on [http://localhost:8000](http://localhost:8000).

### 3. Frontend Setup
Node.js and npm are required.
```bash
# Navigate to frontend and install packages
cd frontend
npm install

# Start Vite development server
npm run dev
```
The dashboard UI will launch on [http://localhost:5173](http://localhost:5173).

---

## Technologies Used
- **Backend**: FastAPI, Playwright (Async), Anthropic API, SQLite (aiosqlite), BeautifulSoup4, Pandas, httpx.
- **Frontend**: React 18, Vite, Tailwind CSS (CDN), Recharts, Lucide React, WebSockets.
