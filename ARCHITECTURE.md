# 🏗️ Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Browser                              │
│                      (Frontend - UI)                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  - Dashboard (Market Data, Portfolio)                     │  │
│  │  - Controls (Start/Stop Bot, Run Cycle)                   │  │
│  │  - Trade History & Activity Log                           │  │
│  │  - Real-time Updates (5s polling)                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/REST API
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                               │
│                   (backend/main.py)                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  REST API Endpoints:                                      │  │
│  │  - /api/status, /api/portfolio                           │  │
│  │  - /api/market-data, /api/trades                         │  │
│  │  - /api/bot/control, /api/bot/run-cycle                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Trading Bot Orchestrator                      │
│                      (backend/bot.py)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Main Loop:                                               │  │
│  │  1. Fetch Market Data                                     │  │
│  │  2. Get AI Decision                                       │  │
│  │  3. Execute Trade                                         │  │
│  │  4. Log Activity                                          │  │
│  │  5. Wait (FETCH_INTERVAL)                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└───┬─────────────────┬─────────────────┬─────────────────────────┘
    │                 │                 │
    ▼                 ▼                 ▼
┌─────────┐    ┌─────────────┐   ┌──────────────┐
│  Data   │    │  AI Agent   │   │   Trading    │
│ Fetcher │    │   (Grok)    │   │   Engine     │
└─────────┘    └─────────────┘   └──────────────┘
    │                 │                 │
    ▼                 ▼                 │
┌─────────┐    ┌─────────────┐         │
│FreeCrypto│   │  xAI API    │         │
│   API    │   │  (Grok)     │         │
└─────────┘    └─────────────┘         │
                                        ▼
                                 ┌──────────────┐
                                 │  Portfolio   │
                                 │  Simulation  │
                                 └──────────────┘
```

## Component Details

### 1. Frontend (HTML/CSS/JavaScript)
**Location**: `frontend/`

**Files**:
- `index.html` - Main UI structure
- `style.css` - Styling and layout
- `app.js` - Frontend logic and API communication

**Responsibilities**:
- Display market data and portfolio status
- Provide bot controls (start/stop/run cycle)
- Show AI decisions and reasoning
- Display trade history and activity logs
- Auto-refresh data every 5 seconds

### 2. FastAPI Backend
**Location**: `backend/main.py`

**Responsibilities**:
- Serve the web frontend
- Provide REST API endpoints
- Handle bot lifecycle (start/stop)
- Coordinate between components
- Serve static files

**Key Endpoints**:
- `GET /api/status` - Bot and portfolio status
- `GET /api/market-data` - Current market data
- `GET /api/portfolio` - Portfolio details
- `GET /api/trades` - Trade history
- `POST /api/bot/control` - Start/stop bot
- `POST /api/bot/run-cycle` - Manual cycle execution

### 3. Trading Bot Orchestrator
**Location**: `backend/bot.py`

**Responsibilities**:
- Coordinate the trading cycle
- Manage bot state (running/stopped)
- Log all activities
- Handle errors gracefully

**Trading Cycle**:
1. Fetch market data from FreeCryptoAPI
2. Send data to AI agent for decision
3. Execute trade based on AI decision
4. Update portfolio
5. Log all actions
6. Wait for next interval

### 4. Data Fetcher
**Location**: `backend/data_fetcher.py`

**Components**:
- `FreeCryptoAPIClient` - API client for FreeCryptoAPI
- `MarketDataAggregator` - Combines market data and technical indicators

**Responsibilities**:
- Fetch current market data (price, volume, 24h stats)
- Fetch technical indicators (MACD, RSI)
- Fetch historical data (optional)
- Aggregate data for AI analysis

**API Endpoints Used**:
- `/getData` - Current market data
- `/getTechnicalAnalysis` - Technical indicators
- `/getCryptoList` - Available cryptocurrencies
- `/getHistory` - Historical data (optional)

### 5. AI Agent
**Location**: `backend/ai_agent.py`

**Components**:
- `GrokTradingAgent` - xAI Grok integration

**Responsibilities**:
- Format market data into AI prompts
- Send prompts to Grok API
- Parse AI responses
- Extract trading decisions (BUY/SELL/HOLD)
- Extract reasoning

**Decision Process**:
1. Receive market snapshot with technical indicators
2. Create detailed prompt with market context
3. Send to Grok model via xAI SDK
4. Parse response for decision and reasoning
5. Return structured decision object

### 6. Trading Engine
**Location**: `backend/trading_engine.py`

**Components**:
- `TradingSimulator` - Portfolio and trade management
- `Portfolio` - Portfolio state
- `Trade` - Trade record

**Responsibilities**:
- Manage virtual USD and crypto balances
- Execute BUY/SELL trades
- Track trade history
- Calculate portfolio value
- Generate statistics

**Trade Execution**:
- **BUY**: Convert TRADE_PERCENTAGE of USD to crypto
- **SELL**: Convert TRADE_PERCENTAGE of crypto to USD
- **HOLD**: No action

### 7. Configuration
**Location**: `backend/config.py`

**Responsibilities**:
- Load environment variables
- Provide application settings
- Validate configuration

**Key Settings**:
- `XAI_API_KEY` - xAI API authentication
- `CRYPTO_PAIR` - Trading pair (e.g., BTC/USD)
- `FETCH_INTERVAL` - Seconds between cycles
- `INITIAL_USD_BALANCE` - Starting virtual balance
- `TRADE_PERCENTAGE` - Trade size (% of balance)

## Data Flow

### Trading Cycle Flow

```
1. Timer Triggers
   ↓
2. Fetch Market Data (FreeCryptoAPI)
   ↓
3. Get Technical Indicators (FreeCryptoAPI)
   ↓
4. Aggregate Data
   ↓
5. Format AI Prompt
   ↓
6. Send to Grok (xAI API)
   ↓
7. Receive AI Decision + Reasoning
   ↓
8. Parse Decision (BUY/SELL/HOLD)
   ↓
9. Execute Trade (if BUY or SELL)
   ↓
10. Update Portfolio
   ↓
11. Log Activity
   ↓
12. Wait for Next Interval
```

### Frontend Update Flow

```
1. User Opens Browser
   ↓
2. Load index.html
   ↓
3. Initialize JavaScript
   ↓
4. Fetch Initial Data (API calls)
   ↓
5. Update UI
   ↓
6. Start Auto-Refresh Timer (5s)
   ↓
7. Periodic API Calls
   ↓
8. Update UI with New Data
```

## Technology Stack

### Backend
- **Python 3.8+** - Programming language
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **Requests** - HTTP client
- **xai-sdk** - xAI Grok integration

### Frontend
- **HTML5** - Structure
- **CSS3** - Styling (with CSS Grid/Flexbox)
- **Vanilla JavaScript** - Logic (no frameworks)
- **Fetch API** - HTTP requests

### External APIs
- **FreeCryptoAPI** - Market data and technical indicators
- **xAI API** - Grok AI model for trading decisions

## Security Considerations

1. **API Key Protection**:
   - API keys stored in `.env` file
   - `.env` excluded from version control
   - Never exposed to frontend

2. **Simulated Trading**:
   - No real money or cryptocurrency
   - No connection to real exchanges
   - Safe for testing and learning

3. **Error Handling**:
   - Graceful degradation on API failures
   - Default to HOLD on errors
   - Comprehensive logging

## Scalability Considerations

Current implementation is designed for:
- Single trading pair
- Single user
- Local deployment

Potential enhancements:
- Multi-pair trading
- Database for persistent storage
- WebSocket for real-time updates
- User authentication
- Cloud deployment
- Backtesting engine

