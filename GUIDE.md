# CricketArb — Complete Setup & User Guide

## Quick Start (TL;DR)

### Option A: One-Click Setup (Recommended for new users)
```
Double-click:  g:\sonu\CricketArb\setup.bat
```
This installs everything automatically — Docker containers, Python backend, database, frontend.
After setup, use:
```
start.bat   → Launches all 3 services + opens browser
stop.bat    → Stops everything
```

### Option B: Manual Setup
```
Terminal 1:  cd g:/sonu/CricketArb && docker-compose up -d
Terminal 2:  cd g:/sonu/CricketArb/backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && alembic revision --autogenerate -m "initial" && alembic upgrade head && python seed_bookmakers.py && python main.py
Terminal 3:  cd g:/sonu/CricketArb/backend && venv\Scripts\activate && celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
Terminal 4:  cd g:/sonu/CricketArb/backend && venv\Scripts\activate && celery -A app.tasks.celery_app beat --loglevel=info
Terminal 5:  cd g:/sonu/CricketArb/frontend && npm install && npm run dev
Open:        http://localhost:5173 → Register → Login → Dashboard
```

---

## Prerequisites

| Tool | Version | Why |
|------|---------|-----|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend build |
| Docker Desktop | Latest | PostgreSQL + Redis containers |
| Git | Latest | Version control |

Verify everything is installed:
```bash
python --version
node --version
docker --version
```

---

## Step 1: Start Infrastructure (Docker)

```bash
cd g:/sonu/CricketArb
docker-compose up -d
```

This starts:
- **PostgreSQL** on port `5433` (user: `cricket_arb`, pass: `cricket_arb_secret`, db: `cricket_arb`)
- **Redis** on port `6380`

Verify they're running:
```bash
docker-compose ps
```

You should see both containers with status `Up`:
```
NAME              STATUS
cricketarb-pg     Up
cricketarb-redis  Up
```

**If Docker is not installed**, download from https://www.docker.com/products/docker-desktop/

---

## Step 2: Backend Setup (Python Virtual Environment)

```bash
cd g:/sonu/CricketArb/backend

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate        # Windows CMD/PowerShell
# source venv/bin/activate   # Mac/Linux

# Install all Python dependencies
pip install -r requirements.txt
```

This installs: FastAPI, SQLAlchemy, Redis, Celery, Playwright, Telegram bot, httpx, etc.

### Install Playwright Browser (only needed for Playwright scraping mode)
```bash
playwright install chromium
```

---

## Step 3: Database Migration

```bash
cd g:/sonu/CricketArb/backend

# Make sure venv is activated
venv\Scripts\activate

# Generate the migration file from SQLAlchemy models
alembic revision --autogenerate -m "initial tables"

# Apply migration — creates all tables in PostgreSQL
alembic upgrade head
```

This creates **7 tables**:
| Table | Purpose |
|-------|---------|
| `users` | User accounts with email, hashed password |
| `user_arb_settings` | Per-user alert preferences (min profit, bookmakers, markets) |
| `bookmakers` | Registered betting sites (Bet365, Betfair, etc.) |
| `cricket_matches` | Match info + live scores + normalized team names |
| `odds_snapshots` | Every scraped odds value, decimal-normalized |
| `arbitrage_opportunities` | Detected arbs with legs (JSON), profit % |
| `hedge_positions` | User hedge positions with original + hedge bets |

### Seed Bookmakers (REQUIRED)

```bash
cd g:/sonu/CricketArb/backend
python seed_bookmakers.py
```

This inserts 5 bookmakers into the database:
- Bet365 (traditional)
- Betfair (exchange — has back + lay odds)
- Pinnacle (sharp bookmaker)
- 1xBet (traditional)
- Betway (traditional)

**The system will not work without this step.**

---

## Step 4: Configure Data Source

Edit `g:/sonu/CricketArb/.env`. The system supports **3 data source modes**:

### Option A: Demo Mode (default — start here)
```env
DATA_SOURCE_MODE=demo
```
- Generates **realistic mock cricket odds** every 30 seconds
- Arb opportunities are injected in ~30% of cycles
- Perfect for **testing the full pipeline** without any API keys
- Includes: India vs Australia, IPL matches, England vs SA, etc.
- **No signup or API key needed — works immediately**

### Option B: The Odds API (recommended for real data)
```env
DATA_SOURCE_MODE=api
THE_ODDS_API_KEY=your-key-here
ODDS_API_REGIONS=uk,eu,au
```
**Setup steps:**
1. Go to **https://the-odds-api.com/#get-access**
2. Click "Get API Key" — sign up with email (free)
3. You'll get a key like `abc123def456...`
4. Paste it as `THE_ODDS_API_KEY` in `.env`
5. Free tier gives **500 requests/month** — enough for testing
6. Returns **real aggregated odds** from 70+ bookmakers worldwide
7. No Playwright or browser automation needed
8. Regions: `uk` (UK bookmakers), `eu` (European), `au` (Australian), `us` (US)

### Option C: Playwright Browser Scraping (advanced)
```env
DATA_SOURCE_MODE=playwright
PROXY_LIST=http://user:pass@proxy1:8080,http://user:pass@proxy2:8080
```
- Uses headless Chromium to scrape betting sites directly
- **Requires**: Calibrated CSS selectors per site (in `data/bookmaker_configs/*.json`)
- **Requires**: Residential proxies to avoid IP blocks
- **Note:** CSS selectors need inspection against each site's live DOM
- To inspect: Set `headless=False` in `base_scraper.py` to see the browser

### Other Settings
```env
# Minimum profit % to trigger arb alerts (lower = more alerts)
MIN_ARB_PROFIT_PCT=0.5

# Betfair exchange commission rate (default 5%)
BETFAIR_COMMISSION_PCT=5.0

# Default stake for arb calculations (in INR)
DEFAULT_ARB_STAKE=1000.0

# How often to scrape (seconds)
SCRAPE_INTERVAL_SECONDS=30

# How old odds can be before considered stale (seconds)
MAX_ODDS_AGE_SECONDS=120
```

### Telegram Bot Setup (optional — for mobile alerts)
1. Open Telegram app
2. Search for `@BotFather`
3. Send `/newbot`
4. Follow prompts — choose a name and username for your bot
5. BotFather gives you a token like `7123456789:AAH...`
6. Paste it in `.env` as `TELEGRAM_BOT_TOKEN=7123456789:AAH...`
7. Start a chat with your new bot and send `/start`
8. Your `chat_id` gets linked when you register in the web app

---

## Step 5: Start the Backend Server

```bash
cd g:/sonu/CricketArb/backend
venv\Scripts\activate
python main.py
```

You should see:
```
INFO     Cricket Arb backend started
INFO     Uvicorn running on http://0.0.0.0:8000
```

**Verify it's working:**
- Health check: http://localhost:8000/health
- API docs (Swagger): http://localhost:8000/docs
- Scraper status: http://localhost:8000/health/scrapers

---

## Step 6: Start Celery Workers (Data Scraping Engine)

On Windows, worker and beat scheduler must run **separately** (the `-B` flag doesn't work on Windows).

Open a **new/second terminal** — Celery Worker:

```bash
cd g:/sonu/CricketArb/backend
venv\Scripts\activate

# Start Celery worker (processes tasks)
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

Open a **new/third terminal** — Celery Beat:

```bash
cd g:/sonu/CricketArb/backend
venv\Scripts\activate

# Start Celery beat (schedules periodic tasks)
celery -A app.tasks.celery_app beat --loglevel=info
```

You should see in each terminal:
```
Worker:  [celery.worker] Ready.
Beat:    [celery.beat] Scheduler started.
```

**What this does every cycle:**
| Task | Frequency | Description |
|------|-----------|-------------|
| `scrape_all_bookmakers` | Every 30s | Fetches odds (demo/API/Playwright based on mode) |
| `discover_matches` | Every 5 min | Finds new cricket matches |
| `cleanup_stale_data` | Every 1 hour | Removes odds older than 24 hours |

**In demo mode**, you'll immediately see logs like:
```
[Demo] Cycle #1: Published 30 demo odds (3 matches, with arb injection)
[Demo] Cycle #2: Published 30 demo odds (3 matches, normal)
```

### Windows Note
On Windows, you **must** run worker and beat separately (as shown above). The `-B` flag is not supported on Windows. Always use `--pool=solo` for the worker.

---

## Step 7: Frontend Setup

Open a **new/third terminal**:

```bash
cd g:/sonu/CricketArb/frontend

# Install Node.js dependencies
npm install

# Start development server
npm run dev
```

You should see:
```
VITE v5.x.x  ready in XXX ms
➜  Local:   http://localhost:5173/
```

---

## Step 8: Create Your Account & Start Using

1. Open **http://localhost:5173** in your browser (Chrome recommended)
2. You'll see the **Login** page
3. Click **"Register"** tab/link
4. Enter:
   - **Email**: your email
   - **Username**: pick a username
   - **Password**: pick a password
5. Click Register
6. Login with your new credentials
7. **Allow browser notifications** when prompted (needed for sound alerts)

---

## Step 9: Explore the Dashboard

### Dashboard (Home Page)
- Shows all **active arbitrage opportunities** in real-time
- Cards appear with a **sound alert** when a new arb is detected
- Each card shows:
  - **Arb type**: Cross-Book / Back-Lay / Live Hedge (color-coded)
  - **Profit %**: Guaranteed profit percentage
  - **Match**: Teams + tournament
  - **Legs**: Exact bookmaker + selection + odds for each leg
  - **Stakes**: How much to bet on each leg
  - **Guaranteed profit**: Amount in INR
- Cards auto-refresh every **10 seconds** + instant **WebSocket push**
- In demo mode, arbs appear roughly every 1-2 minutes

### Hedge Monitor (Main Feature — Your Flow)
This is the core feature for your use case: **pre-match bet → live monitoring → hedge alert**.

**How to use:**
1. Go to **Hedge Monitor** page (second item in nav bar)
2. Click **"+ Record New Bet"**
3. Fill in your bet details:
   - **Team A / Team B**: e.g., India / Australia
   - **Tournament**: e.g., IPL 2025 (optional)
   - **Bookmaker**: e.g., bet365, betway, dream11
   - **You Bet On**: which team you bet on (e.g., India)
   - **Odds You Got**: e.g., 2.50
   - **Your Stake**: e.g., 1000 (in Rs.)
4. Click **"Start Monitoring"**
5. The system shows:
   - Your potential return (stake x odds)
   - **Breakeven odds**: the minimum opposite team odds needed for profit
6. System checks live odds every **5 seconds**
7. When the opposite team's odds exceed breakeven:
   - Card glows **yellow** with "HEDGE NOW!" badge
   - **Double beep** sound plays
   - **Browser notification**: "HEDGE NOW! Profit Rs.875"
   - **Telegram message** (if configured)
   - Shows **exact instruction**: "Bet Rs.625 on Australia @ 4.00 on betway"
8. You place the hedge bet on the recommended bookmaker
9. Click **"I Placed the Hedge"** to mark as done
10. **Guaranteed profit** locked in regardless of match result!

**Example walkthrough:**
```
Step 1: You bet Rs.1000 on India @ 2.50 on Bet365 (pre-match)
        Potential return: Rs.2500
        Breakeven: opposite odds must exceed 1.67

Step 2: Match starts. India batting well, 80/1 after 10 overs.
        Australia's odds drift to 4.00 on Betway.

Step 3: System detects 4.00 > 1.67 → HEDGE ALERT!
        "Bet Rs.625 on Australia @ 4.00 on Betway"
        "Guaranteed profit: Rs.875"

Step 4: You place Rs.625 on Australia @ 4.00 on Betway

Result: If India wins:    Rs.2500 - Rs.1000 - Rs.625 = +Rs.875
        If Australia wins: Rs.2500 - Rs.1000 - Rs.625 = +Rs.875
        PROFIT EITHER WAY!
```

### Live Matches
- Shows all currently live/upcoming cricket matches
- Click a match to see **odds comparison table** across all bookmakers
- **Green highlight** = best available odds for that selection
- Useful for manually spotting value

### Arb History
- Historical log of all detected arb opportunities
- Filter by type: Cross-Book, Back-Lay, Live Swing
- Shows: when detected, profit %, which bookmakers, status (active/expired/executed)

### Positions (Hedge Tracker)
- Record your **actual bets** to track hedge positions
- **Create Position**: Log your initial bet (bookmaker, selection, odds, stake)
- **Record Hedge**: When you place the hedge bet, log it here
- System auto-calculates your **guaranteed profit**
- Close positions when settled
- Tracks P&L across all your hedged positions

### Settings
- **Min Profit %**: Only get alerts above this threshold (default: 0.5%)
- **Max Stake**: Cap for stake calculations
- **Bookmakers**: Select which bookmakers to monitor
- **Markets**: Choose which market types to track (Match Winner, Total Runs, etc.)
- **Formats**: T20 / ODI / TEST
- **Notifications**: Toggle Telegram, Web Push, Sound independently

---

## Step 10: Install Chrome Extension (Live Odds Auto-Capture)

The Chrome extension **automatically captures live odds** from any betting website you have open. No manual clicking needed — just set the match once and it scans every few seconds.

### Install the Extension
1. Open Chrome → go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top right)
3. Click **"Load unpacked"**
4. Select the folder: `g:/sonu/CricketArb/extension/`
5. Extension icon appears in Chrome toolbar

### Set Your Auth Token
1. Login at http://localhost:5173
2. Open Chrome DevTools (F12) → Application tab → Local Storage → `access_token`
3. Copy the token value
4. Click the CricketArb extension icon in toolbar
5. Paste the token and click **"Save Token"**

### Using Auto-Capture (Recommended — Live Matches)
1. Go to **any betting website** (bet365, betway, dream11, parimatch, etc.)
2. Navigate to the **live match** you're monitoring
3. Click the CricketArb extension icon → **"Open Capture Panel"**
4. Fill in: **Team A**, **Team B** (bookmaker auto-detected from URL)
5. Click the **"Auto"** button in the panel header
6. Extension now:
   - Scans the page every **7 seconds** for odds values
   - Detects odds using CSS classes, data attributes, and text patterns
   - Associates each odds value with the nearest team/selection name
   - **Only sends when odds actually change** (no flooding)
   - Shows real-time status: green dot, odds count, last send time
7. The panel shows: `Scans: 12 | Detected: 6 | Sent: 4 | Errors: 0`
8. You can change scan interval: **5s / 7s / 10s / 15s**
9. Click **"Stop"** to pause, **"Auto"** to resume

### How Auto-Capture Detects Odds
The scanner uses 4 strategies (tries each until it finds odds):
1. **CSS class heuristics** — looks for elements with classes like `odd`, `price`, `bet-btn`, `rate`, `coefficient`
2. **Data attributes** — checks `data-odds`, `data-price`, `data-selection-id` attributes
3. **Structural patterns** — finds buttons/spans with decimal numbers in odds range
4. **Text walker** — last resort: walks all text nodes looking for numbers like `2.10`

It also uses a **MutationObserver** to instantly detect when odds change in the DOM (no need to wait for the next scan cycle).

### Manual Capture (Fallback)
If auto-capture doesn't detect odds well on a specific site:
1. Click **"Select"** → click any odds number on the page → auto-captured
2. Or type selection name + odds value manually → click **"+ Add"**
3. Click **"Send to CricketArb"**
4. Supports all formats: `2.10` (decimal), `5/2` (fractional), `+150` (American)

### Supported Bookmakers (Auto-Detected from URL)
bet365, betfair, pinnacle, 1xbet, betway, dream11, parimatch, mostbet, fairplay, lotus365, dafabet, unibet, william hill, ladbrokes, paddypower, bwin, 10cric, fun88, 22bet, melbet, rajabets, betwinner, stake, betmgm + any other site (just type the name)

---

## How Arbitrage Detection Works

### 1. Cross-Book Arbitrage
Different bookmakers offer odds on the same match. When the best odds across bookmakers are generous enough, you can bet on ALL outcomes and guarantee profit.

**Example:**
```
Bet365:    India    @ 2.10
Pinnacle:  Australia @ 2.15

Arb check: (1/2.10) + (1/2.15) = 0.476 + 0.465 = 0.941
Since 0.941 < 1.0 → ARBITRAGE EXISTS!

Profit = (1 - 0.941) × 100 = 5.9%

With ₹1000 total stake:
  → Bet ₹488 on India @ 2.10 (Bet365)
  → Bet ₹512 on Australia @ 2.15 (Pinnacle)
  → Guaranteed profit: ₹59 regardless of who wins
```

### 2. Back-Lay Arbitrage
Back a selection on a bookmaker, then lay (bet against) on Betfair Exchange.

**Example:**
```
Bet365:  BACK India @ 2.20  (bet FOR India to win)
Betfair: LAY India  @ 2.05  (bet AGAINST India, 5% commission)

Back stake: ₹1000 on India @ 2.20
Lay stake:  ₹1073 against India @ 2.05

If India wins:  +₹1200 (back) - ₹1073×1.05 (lay) = +₹73
If India loses: -₹1000 (back) + ₹1073×0.95 (lay) = +₹19
→ Profit either way!
```

### 3. Live Swing Hedge
Place a pre-match bet. During the live match, the opposite team's odds shift dramatically (wickets fall, run rate changes). Hedge at the new odds to lock in profit.

**Example:**
```
Pre-match:  Bet ₹1000 on India @ 2.50
            (potential return: ₹2500)

After 10 overs (India batting well, 80/1):
Live odds:  Australia drifts to 4.00

Hedge:      Bet ₹625 on Australia @ 4.00
            (potential return: ₹2500)

If India wins:   ₹2500 - ₹1000 - ₹625 = +₹875
If Australia wins: ₹2500 - ₹1000 - ₹625 = +₹875
→ Guaranteed profit: ₹875 regardless of result!
```

---

## Data Flow (How the System Works End-to-End)

### Flow 1: Automatic Arb Detection
```
1. Celery Beat triggers scrape task every 30 seconds
                    ↓
2. Data Source fetches odds:
   - Demo: generates mock data
   - API: calls The Odds API REST endpoint
   - Playwright: scrapes betting websites
                    ↓
3. Odds published to Redis channel "cricket:odds:raw"
                    ↓
4. Arb Engine (background subscriber) picks up odds:
   - Groups by match + market
   - Runs Cross-Book detection
   - Runs Back-Lay detection (Betfair lay vs others)
                    ↓
5. If arb detected (profit > MIN_ARB_PROFIT_PCT):
   → Published to Redis channel "cricket:arb:detected"
                    ↓
6. Notifications fan out:
   → WebSocket push → React dashboard (card appears + sound plays)
   → Telegram bot sends formatted message to your chat
```

### Flow 2: Your Main Flow (Pre-Match Bet → Live Hedge)
```
1. You place a pre-match bet on any betting app
   (e.g., India @ 2.50 for Rs.1000 on Bet365)
                    ↓
2. Record it in Hedge Monitor page
   System calculates breakeven odds for opposite team
                    ↓
3. Match goes live. Odds keep updating in Redis
   (from Demo/API/Playwright + Chrome Extension captures)
                    ↓
4. Hedge Monitor checks every 5 seconds:
   "Are opposite team's live odds > breakeven?"
                    ↓
5. YES → HEDGE ALERT!
   → Double beep sound plays
   → Browser notification: "HEDGE NOW! Profit Rs.875"
   → Telegram: "Bet Rs.625 on Australia @ 4.00 on Betway"
   → WebSocket push to Hedge Monitor page
                    ↓
6. You place the hedge bet → Guaranteed profit locked in!
```

### Flow 3: Chrome Extension Auto-Capture (Live Data)
```
1. Open any betting site → navigate to live match page
                    ↓
2. Open CricketArb panel → set Team A, Team B → click "Auto"
                    ↓
3. Extension auto-scans page every 7 seconds:
   → Finds odds via CSS classes, data attributes, text patterns
   → Associates each odds value with team/selection name
   → Compares with last snapshot (change detection)
                    ↓
4. Only changed odds sent → POST /api/v1/cricket/capture/
   (MutationObserver also triggers instant re-scan on DOM changes)
                    ↓
5. Odds published to Redis → Arb Engine + Hedge Monitor both use them
   → If your hedge bet's breakeven is crossed → HEDGE ALERT!
```

---

## API Endpoints Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Create account (email, username, password) |
| POST | `/api/v1/auth/login` | Get JWT access + refresh tokens |
| POST | `/api/v1/auth/refresh` | Refresh expired access token |

### Cricket Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/cricket/bookmakers/` | List all registered bookmakers |
| GET | `/api/v1/cricket/matches/` | List matches (filter: status, format) |
| GET | `/api/v1/cricket/matches/live` | Live matches only |
| GET | `/api/v1/cricket/matches/{id}` | Single match detail |
| GET | `/api/v1/cricket/odds/{match_id}` | All odds for a match |
| GET | `/api/v1/cricket/odds/{match_id}/comparison` | Side-by-side bookmaker odds |
| GET | `/api/v1/cricket/odds/{match_id}/history` | Odds timeline for a selection |

### Arbitrage
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/cricket/arb/active` | Currently active arb opportunities |
| GET | `/api/v1/cricket/arb/history` | Historical arb log |
| GET | `/api/v1/cricket/arb/{id}` | Single arb detail with legs |
| POST | `/api/v1/cricket/arb/{id}/dismiss` | Dismiss/hide an arb |

### Hedge Monitor (Main Feature)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/cricket/hedge-monitor/` | Record your pre-match bet (start monitoring) |
| GET | `/api/v1/cricket/hedge-monitor/` | All your bets + live hedge opportunities |
| GET | `/api/v1/cricket/hedge-monitor/{id}` | Single bet + current hedge calculation |
| POST | `/api/v1/cricket/hedge-monitor/{id}/hedged` | Mark as hedged (you placed the bet) |
| DELETE | `/api/v1/cricket/hedge-monitor/{id}` | Remove a monitor |

### Odds Capture (Extension / Manual)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/cricket/capture/` | Send odds from extension or manual entry |

### Positions & Settings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/cricket/positions/` | Your hedge positions |
| POST | `/api/v1/cricket/positions/` | Record initial bet |
| PUT | `/api/v1/cricket/positions/{id}/hedge` | Record hedge bet |
| PUT | `/api/v1/cricket/positions/{id}/close` | Close settled position |
| GET | `/api/v1/cricket/settings/` | Your alert settings |
| PUT | `/api/v1/cricket/settings/` | Update alert preferences |

### WebSocket
| Protocol | Endpoint | Description |
|----------|----------|-------------|
| WS | `/ws/arb-stream?token=JWT` | Real-time arb + hedge alerts (JSON messages) |

WebSocket message types:
- `arb_detected` — new arbitrage opportunity found
- `hedge_available` — profitable hedge opportunity for your bet

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health (Redis, WS clients, data source mode) |
| GET | `/health/scrapers` | Scraper status + active odds count |

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────┐
│                   DATA SOURCES                        │
│                                                       │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌────────┐│
│  │  Demo    │ │ The Odds  │ │Playwright│ │ Chrome ││
│  │  (Mock)  │ │   API     │ │(Browser) │ │Extension││
│  │          │ │ (Real)    │ │          │ │(Manual) ││
│  └────┬─────┘ └─────┬─────┘ └────┬─────┘ └───┬────┘│
│       └──────────────┼────────────┘            │     │
│                      ▼                         ▼     │
│         Redis PubSub: "cricket:odds:raw"             │
└──────────────────────┬───────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND                     │
│                                                       │
│  ┌─────────────────────────────────────┐             │
│  │           ARB ENGINE                 │             │
│  │  ┌─────────────┐ ┌──────────────┐  │             │
│  │  │ Cross-Book  │ │  Back-Lay    │  │             │
│  │  │ Detection   │ │  Detection   │  │             │
│  │  └─────────────┘ └──────────────┘  │             │
│  └────────────────┬────────────────────┘             │
│                   ▼                                   │
│  ┌─────────────────────────────────────┐             │
│  │        HEDGE MONITOR (every 5s)     │             │
│  │  ┌─────────────────────────────┐   │             │
│  │  │ Your bet: India @ 2.50     │   │             │
│  │  │ Checks: Australia live odds │   │             │
│  │  │ If profitable → ALERT!      │   │             │
│  │  └─────────────────────────────┘   │             │
│  └────────────────┬────────────────────┘             │
│                   ▼                                   │
│       Redis PubSub: "cricket:arb:detected"           │
│                   │                                   │
│          ┌────────┼────────┐                         │
│          ▼        ▼        ▼                         │
│    ┌──────────┐ ┌────┐ ┌──────────────┐             │
│    │ Telegram │ │ WS │ │  PostgreSQL  │             │
│    │   Bot    │ │Push│ │  (persist)   │             │
│    └──────────┘ └──┬─┘ └──────────────┘             │
│                    │                                  │
│              REST API (FastAPI)                       │
└────────────────────┬─────────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────────┐
│               REACT FRONTEND                          │
│                                                       │
│  ┌───────────┐ ┌──────────┐ ┌───────────────┐       │
│  │ Dashboard │ │  Hedge   │ │   Position    │       │
│  │ (Arb Cards│ │ Monitor  │ │   Tracker     │       │
│  │ + Sound)  │ │(Your Bets│ │               │       │
│  │           │ │+ Alerts) │ │               │       │
│  └───────────┘ └──────────┘ └───────────────┘       │
└──────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Docker containers not starting
```bash
# Restart containers
docker-compose down && docker-compose up -d

# Check logs
docker-compose logs postgres
docker-compose logs redis

# Check if ports are free
netstat -an | findstr 5433
netstat -an | findstr 6380
```

### Alembic migration fails
```bash
# Reset and recreate from scratch
alembic downgrade base
alembic revision --autogenerate -m "initial tables"
alembic upgrade head
```

### "Module not found" errors
```bash
# Make sure venv is activated
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Celery not working on Windows
```bash
# Use solo pool mode
celery -A app.tasks.celery_app worker -B --loglevel=info --pool=solo
```

### No arb opportunities showing
- **In demo mode**: Wait 1-2 minutes — arbs appear in ~30% of cycles
- **In API mode**: Real arbs are rare and short-lived (seconds). Lower `MIN_ARB_PROFIT_PCT` to `0.1`
- Check Celery terminal for scrape logs
- Check http://localhost:8000/health/scrapers for active odds count

### WebSocket not connecting
- Backend must be running on port 8000
- Check browser console (F12) for errors
- JWT token might be expired — try re-logging in
- CORS must include `http://localhost:5173`

### Telegram alerts not working
- Verify `TELEGRAM_BOT_TOKEN` in `.env` is correct
- You must send `/start` to your bot first
- Check backend logs for Telegram errors
- Token format: `7123456789:AAHxxxx...`

### Frontend build errors
```bash
cd g:/sonu/CricketArb/frontend
rm -rf node_modules
npm install
npm run dev
```

---

## File Structure

```
g:/sonu/CricketArb/
├── setup.bat                         # ONE-CLICK SETUP (run this first!)
├── start.bat                         # Launches all 3 services (created by setup.bat)
├── stop.bat                          # Stops all services (created by setup.bat)
├── .env                              # All environment variables
├── .gitignore                        # Git ignore rules
├── docker-compose.yml                # PostgreSQL + Redis containers
├── GUIDE.md                          # This file
│
├── extension/                        # Chrome Extension (AUTO-CAPTURE live odds)
│   ├── manifest.json                 # Extension config (Manifest V3 + alarms)
│   ├── content.js                    # Auto-scan engine + floating panel
│   ├── content.css                   # Dark-themed panel + auto-capture styles
│   ├── background.js                 # Service worker + keep-alive alarm
│   ├── popup/
│   │   ├── popup.html                # Extension popup UI + auto-capture status
│   │   └── popup.js                  # Token management + status check
│   └── icons/                        # Extension icons (add your own)
│
├── backend/
│   ├── main.py                       # FastAPI app + WebSocket + lifespan
│   ├── requirements.txt              # Python dependencies
│   ├── seed_bookmakers.py            # Seeds 5 bookmakers into DB
│   ├── alembic.ini                   # DB migration config
│   ├── alembic/env.py                # Migration runner
│   ├── data/bookmaker_configs/       # CSS selectors per site (Playwright mode)
│   └── app/
│       ├── core/                     # Config, DB, Redis, Auth, Enums, Exceptions
│       ├── models/                   # SQLAlchemy models (7 tables)
│       ├── schemas/                  # Pydantic request/response models
│       ├── services/
│       │   ├── arb_engine.py         # Cross-book, back-lay detection
│       │   ├── hedge_monitor.py      # LIVE HEDGE MONITOR (core feature)
│       │   ├── hedge_calculator.py   # Stake sizing + P&L projection
│       │   ├── odds_normalizer.py    # Decimal/fractional/American conversion
│       │   └── match_tracker.py      # Team name normalization (fuzzy match)
│       ├── scrapers/
│       │   ├── demo_scraper.py       # Mock data generator (demo mode)
│       │   ├── odds_api_scraper.py   # The Odds API client (api mode)
│       │   ├── base_scraper.py       # Playwright base class
│       │   ├── bet365_scraper.py     # Bet365 Playwright scraper
│       │   ├── betfair_scraper.py    # Betfair Exchange scraper
│       │   ├── pinnacle_scraper.py   # Pinnacle scraper
│       │   ├── onexbet_scraper.py    # 1xBet scraper
│       │   ├── betway_scraper.py     # Betway scraper
│       │   ├── scraper_manager.py    # Orchestrator + health monitoring
│       │   └── anti_detect.py        # Proxy/UA rotation, stealth
│       ├── tasks/                    # Celery periodic tasks
│       │   ├── celery_app.py         # Celery config + beat schedule
│       │   ├── scrape_tasks.py       # Scraping (supports 3 modes)
│       │   └── cleanup_tasks.py      # Stale data purge
│       ├── websocket/
│       │   ├── connection_manager.py # WS pool + user tracking
│       │   └── arb_stream.py         # Redis→WS bridge + hedge monitor checker
│       ├── notifications/
│       │   ├── telegram_bot.py       # Formatted Telegram messages
│       │   └── push_manager.py       # Web push via WebSocket
│       └── api/v1/
│           ├── router.py             # Main router (registers all sub-routers)
│           ├── auth.py               # Register, login, refresh
│           ├── bookmakers.py         # List bookmakers
│           ├── matches.py            # Match listing, live, detail
│           ├── odds.py               # Odds comparison, history
│           ├── arb.py                # Active/historical arb opportunities
│           ├── hedge_monitor.py      # HEDGE MONITOR API (record bet, get alerts)
│           ├── capture.py            # CAPTURE API (from extension/manual)
│           ├── positions.py          # Hedge position tracking
│           └── settings.py           # Per-user alert preferences
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.tsx                  # React entry point
│       ├── App.tsx                   # Router + auth guard + WS init
│       ├── index.css                 # Tailwind + animations
│       ├── services/
│       │   ├── api.ts                # Axios client + JWT auto-refresh
│       │   └── websocket.ts          # WS client + auto-reconnect
│       ├── stores/
│       │   ├── authStore.ts          # Zustand auth state
│       │   └── arbStore.ts           # Zustand arb state + sound toggle
│       ├── hooks/
│       │   ├── useWebSocket.ts       # WS connection + arb + hedge events + sound
│       │   ├── useAuth.ts            # Auth helper hook
│       │   └── useSound.ts           # AudioContext sound player
│       ├── components/
│       │   ├── Layout.tsx            # Page layout wrapper
│       │   ├── Navbar.tsx            # Navigation bar
│       │   ├── ArbCard.tsx           # Arb opportunity card (color-coded)
│       │   ├── OddsTable.tsx         # Bookmaker odds comparison matrix
│       │   ├── MatchCard.tsx         # Match info + live scores
│       │   ├── PositionTracker.tsx   # Hedge position display
│       │   └── SoundAlert.tsx        # Sound notification component
│       └── pages/
│           ├── Dashboard.tsx         # Main — live arb cards + sound
│           ├── HedgeMonitor.tsx      # HEDGE MONITOR (record bet, see alerts)
│           ├── LiveMatches.tsx       # Live matches + odds comparison
│           ├── ArbHistory.tsx        # Historical arb log
│           ├── Positions.tsx         # Hedge position tracker
│           ├── Settings.tsx          # Alert preferences
│           └── Login.tsx             # Login + register
│
└── tests/
    ├── conftest.py                   # Test fixtures
    ├── test_odds_normalizer.py       # Odds conversion tests
    ├── test_arb_engine.py            # Arb detection algorithm tests
    └── test_hedge_calculator.py      # Hedge calculation tests
```

---

## Running Tests

```bash
cd g:/sonu/CricketArb
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_arb_engine.py -v
```

---

## How To Use CricketArb (Step-by-Step)

### Step A: First-Time Setup (One Time Only)
1. Double-click `setup.bat` — installs everything automatically
2. Double-click `install-extension.bat` — opens Chrome extensions page
3. In Chrome: Enable Developer Mode → Load Unpacked → select `extension/` folder

### Step B: Every Time You Want to Use
1. Double-click `start.bat` — launches all services + opens browser
2. Login at http://localhost:5173 (or register if first time)

### Step C: Live Match Flow (The Money-Making Part)

**BEFORE the match starts:**
1. Open your betting app (bet365, dream11, betway, etc.)
2. Place your **first bet** on the match (e.g., India to win @ 2.50, Rs.1000)
3. Open CricketArb dashboard → go to **Hedge Monitor** page
4. Click **"+ Record New Bet"** → enter exactly what you bet:
   - Team A: India, Team B: Australia
   - Bet on: India, Odds: 2.50, Stake: 1000
5. Click **"Start Monitoring"**
6. System shows your breakeven odds (e.g., 1.67 for Australia)

**DURING the live match:**
7. Open the betting website in Chrome (where odds are showing live)
8. Click CricketArb extension icon → **"Open Capture Panel"**
9. Enter Team A: India, Team B: Australia
10. Click **"Auto"** button → green dot appears → extension starts scanning
11. Extension reads odds from the page every 7 seconds and sends to CricketArb
12. You can minimize the panel and keep watching the match

**WHEN THE ALERT COMES:**
13. India starts batting well → Australia's odds rise from 1.40 to 1.80
14. 1.80 > 1.67 (your breakeven) → **HEDGE ALERT!**
15. You hear a **double beep** sound
16. Browser notification: **"HEDGE NOW! Profit Rs.111"**
17. Hedge Monitor shows: **"Bet Rs.1389 on Australia @ 1.80"**

**LOCK IN YOUR PROFIT:**
18. Open your betting app → place Rs.1389 on Australia @ 1.80
19. Click **"I Placed the Hedge"** in CricketArb
20. **Done! You make Rs.111 profit no matter who wins!**

### Important Notes
- The extension **only reads odds** — it never places bets or touches your betting account
- You always place bets **manually** on your betting apps
- The system works with **any betting website** that shows odds on the page
- For best results, have **2-3 betting apps** open — different sites offer different odds
- You need the betting website **open in Chrome** for the extension to read odds
- The extension runs in **Developer Mode** because it's not published to Chrome Web Store

### When NOT to Hedge
- If the alert shows very small profit (< Rs.50), transaction fees may eat it
- If odds are moving very fast, they might change before you place the bet
- Always double-check the odds on the betting site match what CricketArb shows

---

## Complete Live Match Workflow (End-to-End)

Here's exactly what happens during a real live match:

### Before the Match
1. **Double-click `start.bat`** — launches backend, Celery, frontend
2. Open http://localhost:5173 → Login
3. Go to **Hedge Monitor** page
4. Click **"+ Record New Bet"** → enter your pre-match bet details:
   - Team A: India, Team B: Australia
   - You bet on: India @ 2.50, Stake: Rs.1000
5. System shows: Breakeven odds = 1.67 (Australia must exceed this)

### During the Match
6. **Open the betting app** in Chrome (bet365, dream11, betway, etc.)
7. Navigate to the **live match page**
8. Click CricketArb extension icon → **Open Capture Panel**
9. Type: Team A = India, Team B = Australia (bookmaker auto-fills from URL)
10. Click **"Auto"** button → extension starts scanning every 7 seconds
11. Panel shows: green dot, odds detected count, auto-sending to backend

### The Alert
12. India batting well → Australia's odds drift from 1.40 to 1.80
13. 1.80 > 1.67 (breakeven) → **HEDGE ALERT fires!**
14. You hear a **double beep** sound
15. Browser notification: **"HEDGE NOW! Profit Rs.111"**
16. Hedge Monitor page glows yellow: **"Bet Rs.1389 on Australia @ 1.80 on betway"**

### Lock In Profit
17. Open betway → place Rs.1389 on Australia @ 1.80
18. Click **"I Placed the Hedge"** in CricketArb
19. **Guaranteed profit: Rs.111 regardless of who wins!**

---

## Switching Data Source Modes

### From Demo → Real Data (API)
1. Sign up at https://the-odds-api.com/#get-access
2. Edit `.env`:
   ```env
   DATA_SOURCE_MODE=api
   THE_ODDS_API_KEY=your-actual-key
   ```
3. Restart Celery worker (Ctrl+C → restart command)
4. Real odds will flow in on next cycle

### From API → Playwright (Advanced)
1. Edit `.env`:
   ```env
   DATA_SOURCE_MODE=playwright
   PROXY_LIST=http://user:pass@proxy1:8080
   ```
2. Calibrate CSS selectors in `data/bookmaker_configs/*.json`
3. Restart Celery worker




###env
# Database
DATABASE_URL=postgresql+asyncpg://cricket_arb:cricket_arb_secret@localhost:5433/cricket_arb

# Redis
REDIS_URL=redis://localhost:6380/0

# JWT
JWT_SECRET_KEY=dev-cricket-arb-secret-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Data Source Mode: "demo" (mock data), "api" (The Odds API), "playwright" (browser scraping)
DATA_SOURCE_MODE=demo

# The Odds API (free tier: 500 requests/month)
# Sign up at: https://the-odds-api.com/#get-access
THE_ODDS_API_KEY=
ODDS_API_REGIONS=uk,eu,au

# Cricket Arbitrage
SCRAPE_INTERVAL_SECONDS=30
MATCH_DISCOVERY_INTERVAL_SECONDS=300
MIN_ARB_PROFIT_PCT=0.5
MAX_ODDS_AGE_SECONDS=120
PROXY_LIST=
BETFAIR_COMMISSION_PCT=5.0
DEFAULT_ARB_STAKE=1000.0
ODDS_CLEANUP_HOURS=24

# Telegram
TELEGRAM_BOT_TOKEN=

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
