# 🤖 AI Crypto Trading Bot

A sophisticated cryptocurrency trading simulator powered by **xAI's Grok** artificial intelligence. This application fetches real-time market data, uses AI to make trading decisions, and simulates trades in a virtual portfolio.

## ✨ Features

- **Real-time Market Data**: Fetches live cryptocurrency prices and technical indicators from FreeCryptoAPI
- **AI-Powered Decisions**: Uses xAI's Grok model to analyze market data and make BUY/SELL/HOLD decisions
- **Technical Analysis**: Incorporates MACD, RSI, and other indicators for informed trading
- **Portfolio Simulation**: Tracks virtual USD and cryptocurrency balances
- **Interactive Web UI**: Modern, responsive dashboard to monitor trading activity
- **Activity Logging**: Detailed logs of all data fetches, AI decisions, and trades
- **Trade History**: Complete record of all executed trades with reasoning

## 🏗️ Architecture

### Backend (Python + FastAPI)
- **Data Fetcher**: Retrieves market data and technical indicators from FreeCryptoAPI
- **AI Agent**: Integrates with xAI's Grok model for trading decisions
- **Trading Engine**: Simulates portfolio management and trade execution
- **REST API**: Provides endpoints for frontend communication

### Frontend (HTML + CSS + JavaScript)
- **Dashboard**: Displays market data, portfolio status, and AI decisions
- **Controls**: Start/stop bot and run manual trading cycles
- **Trade History**: Table view of all executed trades
- **Activity Log**: Real-time activity monitoring

## 📋 Prerequisites

- Python 3.8 or higher
- xAI API key (get one from [xAI](https://x.ai))
- Internet connection for API access

## 🚀 Installation

1. **Clone or download this repository**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your xAI API key:
     ```
     XAI_API_KEY=your_actual_api_key_here
     ```

4. **Customize settings** (optional):
   Edit `.env` to adjust:
   - `CRYPTO_PAIR`: Trading pair (default: BTC/USD)
   - `FETCH_INTERVAL`: Seconds between trading cycles (default: 60)
   - `INITIAL_USD_BALANCE`: Starting virtual USD (default: 10000.0)
   - `TRADE_PERCENTAGE`: Percentage of balance to trade (default: 0.1 = 10%)

## 🎮 Usage

### Starting the Application

1. **Run the backend server**:
   ```bash
   python -m backend.main
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:8000
   ```

### Using the Web Interface

1. **View Market Data**: The dashboard displays real-time cryptocurrency prices and technical indicators

2. **Start Automated Trading**:
   - Click the "▶ Start Bot" button
   - The bot will automatically fetch data, get AI decisions, and execute trades at the configured interval

3. **Run Single Cycle**:
   - Click "⚡ Run Single Cycle" to manually trigger one trading cycle
   - Useful for testing or manual control

4. **Monitor Activity**:
   - **Portfolio**: Track your virtual USD and crypto balances
   - **AI Decision**: See the latest decision and reasoning from Grok
   - **Trade History**: Review all executed trades
   - **Activity Log**: Monitor all bot activities in real-time

5. **Stop the Bot**:
   - Click "⏹ Stop Bot" to halt automated trading

## 📊 API Endpoints

The backend provides the following REST API endpoints:

- `GET /api/health` - Health check
- `GET /api/status` - Bot status and portfolio
- `GET /api/portfolio` - Current portfolio
- `GET /api/market-data` - Latest market data
- `GET /api/trades` - Trade history
- `GET /api/activity-log` - Activity log
- `GET /api/statistics` - Trading statistics
- `GET /api/crypto-list` - Available cryptocurrencies
- `POST /api/bot/control` - Start/stop bot
- `POST /api/bot/run-cycle` - Run single trading cycle
- `POST /api/bot/change-pair` - Change trading pair

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `XAI_API_KEY` | Your xAI API key | Required |
| `CRYPTO_PAIR` | Trading pair to monitor | BTC/USD |
| `FETCH_INTERVAL` | Seconds between cycles | 60 |
| `INITIAL_USD_BALANCE` | Starting virtual USD | 10000.0 |
| `TRADE_PERCENTAGE` | % of balance per trade | 0.1 (10%) |
| `BACKEND_HOST` | Server host | 0.0.0.0 |
| `BACKEND_PORT` | Server port | 8000 |

### Trading Logic

The AI agent receives:
- Current price and 24h statistics
- Technical indicators (MACD, RSI)
- Market volume and trends

Based on this data, Grok analyzes:
- RSI levels (oversold <30, overbought >70)
- MACD crossovers and momentum
- Price trends and volatility
- Risk management principles

The bot then executes:
- **BUY**: Converts 10% of USD to crypto
- **SELL**: Converts 10% of crypto to USD
- **HOLD**: No action taken

## 📁 Project Structure

```
ai-trader/
├── backend/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── data_fetcher.py    # FreeCryptoAPI client
│   ├── ai_agent.py        # xAI Grok integration
│   ├── trading_engine.py  # Portfolio & trade simulation
│   ├── bot.py             # Main trading bot orchestrator
│   └── main.py            # FastAPI application
├── frontend/
│   ├── index.html         # Web UI
│   ├── style.css          # Styling
│   └── app.js             # Frontend logic
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
└── README.md             # This file
```

## 🛡️ Safety Features

- **Simulated Trading**: No real money or cryptocurrency is used
- **Error Handling**: Comprehensive error handling for API failures
- **Default to HOLD**: On errors, the bot defaults to HOLD for safety
- **Configurable Limits**: Control trade sizes and intervals
- **Activity Logging**: Full audit trail of all actions

## 🔍 Troubleshooting

### Bot won't start
- Check that your `.env` file exists and contains a valid `XAI_API_KEY`
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### No market data
- Verify internet connection
- Check FreeCryptoAPI status
- Try a different trading pair

### AI decisions failing
- Verify xAI API key is correct
- Check xAI API quota/limits
- Review activity log for error messages

## 📝 Notes

- This is a **simulation** - no real trading occurs
- Market data is fetched from FreeCryptoAPI (free tier may have rate limits)
- AI decisions are based on technical analysis and may not always be profitable
- Past performance does not guarantee future results

## 🤝 Contributing

Feel free to fork this project and customize it for your needs. Some ideas:
- Add more technical indicators
- Implement different trading strategies
- Add charting/visualization
- Support multiple trading pairs simultaneously
- Add backtesting capabilities

## 📄 License

This project is provided as-is for educational purposes.

## ⚠️ Disclaimer

This software is for educational and simulation purposes only. It does not provide financial advice. Cryptocurrency trading carries significant risk. Always do your own research and never invest more than you can afford to lose.

