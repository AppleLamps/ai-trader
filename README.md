# 🤖 AI Crypto Trading Bot

A sophisticated cryptocurrency trading simulator powered by **xAI's Grok** artificial intelligence. This application fetches real-time market data for **multiple cryptocurrencies simultaneously**, uses AI to make independent trading decisions for each, and simulates trades in a virtual portfolio.

## ✨ Features

- **Multi-Cryptocurrency Support**: Simultaneously tracks and trades **Bitcoin (BTC)**, **Dogecoin (DOGE)**, and **Solana (SOL)**
- **Real-time Market Data**: Fetches live cryptocurrency prices and technical indicators from FreeCryptoAPI
- **AI-Powered Decisions**: Uses xAI's Grok model to independently analyze each cryptocurrency and make BUY/SELL/HOLD decisions
- **Technical Analysis**: Incorporates MACD, RSI, and other indicators for informed trading
- **Risk Management**: Advanced risk management with position tracking, stop-loss, and take-profit triggers
- **Portfolio Simulation**: Tracks virtual USD balance and separate balances for each cryptocurrency
- **Interactive Web UI**: Modern, responsive dashboard to monitor all trading activity across multiple cryptos
- **Activity Logging**: Detailed logs of all data fetches, AI decisions, and trades
- **Trade History**: Complete record of all executed trades with reasoning and pair identification

## 🏗️ Architecture

### Backend (Python + FastAPI)
- **Data Fetcher**: Retrieves market data and technical indicators from FreeCryptoAPI for all tracked pairs
- **AI Agent**: Integrates with xAI's Grok model for independent trading decisions per cryptocurrency
- **Trading Engine**: Simulates portfolio management with multi-crypto balance tracking and trade execution
- **Risk Management**: Monitors positions across all pairs with stop-loss and take-profit triggers
- **Technical Analysis**: Calculates MACD, RSI, and other indicators for each cryptocurrency
- **REST API**: Provides endpoints for frontend communication

### Frontend (HTML + CSS + JavaScript)
- **Dashboard**: Displays market data cards for each cryptocurrency (BTC, DOGE, SOL)
- **Portfolio View**: Shows USD balance and individual crypto balances with USD values
- **AI Decisions**: Separate decision cards for each trading pair with confidence and risk levels
- **Controls**: Start/stop bot and run manual trading cycles
- **Trade History**: Table view of all executed trades with pair identification
- **Activity Log**: Real-time activity monitoring across all cryptocurrencies

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
   - Edit `.env` and add your API keys:
     ```
     XAI_API_KEY=your_actual_xai_api_key_here
     FREECRYPTO_API_KEY=your_actual_freecrypto_api_key_here
     ```

4. **Customize settings** (optional):
   Edit `.env` to adjust:
   - `CRYPTO_PAIRS`: Comma-separated list of trading pairs (default: BTC/USD,DOGE/USD,SOL/USD)
   - `FETCH_INTERVAL`: Seconds between trading cycles (default: 60)
   - `INITIAL_USD_BALANCE`: Starting virtual USD (default: 10000000.0)
   - `TRADE_PERCENTAGE`: Percentage of balance to trade (default: 0.1 = 10%)
   - `BACKEND_HOST`: Server host (default: 127.0.0.1)
   - `BACKEND_PORT`: Server port (default: 8001)

## 🎮 Usage

### Starting the Application

1. **Run the backend server**:
   ```bash
   python -m backend.main
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:8001
   ```

### Using the Web Interface

1. **View Market Data**: The dashboard displays real-time data for all tracked cryptocurrencies:
   - **BTC/USD**: Bitcoin price, 24h change, volume, RSI, and MACD
   - **DOGE/USD**: Dogecoin price, 24h change, volume, RSI, and MACD
   - **SOL/USD**: Solana price, 24h change, volume, RSI, and MACD

2. **Start Automated Trading**:
   - Click the "▶ Start Bot" button
   - The bot will automatically fetch data for all pairs, get independent AI decisions for each, and execute trades at the configured interval

3. **Run Single Cycle**:
   - Click "⚡ Run Single Cycle" to manually trigger one trading cycle for all cryptocurrencies
   - Useful for testing or manual control

4. **Monitor Activity**:
   - **Portfolio**: Track your virtual USD balance and individual crypto balances (BTC, DOGE, SOL) with their USD values
   - **AI Decisions**: See separate decision cards for each cryptocurrency with confidence levels and risk assessment
   - **Trade History**: Review all executed trades with pair identification
   - **Activity Log**: Monitor all bot activities in real-time across all cryptocurrencies

5. **Stop the Bot**:
   - Click "⏹ Stop Bot" to halt automated trading

## 📊 API Endpoints

The backend provides the following REST API endpoints:

- `GET /api/health` - Health check
- `GET /api/status` - Bot status, portfolio, and last decisions for all pairs
- `GET /api/portfolio` - Current portfolio with all crypto balances
- `GET /api/market-data` - Latest market data for all tracked pairs
- `GET /api/trades` - Trade history with pair identification
- `GET /api/activity-log` - Activity log
- `GET /api/statistics` - Trading statistics across all pairs
- `GET /api/crypto-list` - Available cryptocurrencies
- `GET /api/trading-pairs` - List of currently tracked trading pairs
- `POST /api/bot/control` - Start/stop bot
- `POST /api/bot/run-cycle` - Run single trading cycle for all pairs

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `XAI_API_KEY` | Your xAI API key | Required |
| `FREECRYPTO_API_KEY` | Your FreeCrypto API key | Optional |
| `CRYPTO_PAIRS` | Comma-separated trading pairs | BTC/USD,DOGE/USD,SOL/USD |
| `FETCH_INTERVAL` | Seconds between cycles | 60 |
| `INITIAL_USD_BALANCE` | Starting virtual USD | 10000000.0 |
| `TRADE_PERCENTAGE` | % of balance per trade | 0.1 (10%) |
| `MAX_POSITION_SIZE` | Max position size % | 0.1 (10%) |
| `STOP_LOSS_PERCENTAGE` | Stop loss trigger % | 0.05 (5%) |
| `TAKE_PROFIT_PERCENTAGE` | Take profit trigger % | 0.1 (10%) |
| `BACKEND_HOST` | Server host | 127.0.0.1 |
| `BACKEND_PORT` | Server port | 8001 |

### Trading Logic

**For each cryptocurrency independently**, the AI agent receives:
- Current price and 24h statistics
- Technical indicators (MACD, RSI)
- Market volume and trends
- Current portfolio position

Based on this data, Grok analyzes:
- RSI levels (oversold <30, overbought >70)
- MACD crossovers and momentum
- Price trends and volatility
- Risk management principles
- Position sizing and exposure

The bot then executes **for each pair**:
- **BUY**: Converts 10% of available USD to crypto (if risk limits allow)
- **SELL**: Converts 10% of crypto holdings to USD (if risk limits allow)
- **HOLD**: No action taken

**Risk Management**:
- Tracks positions across all pairs to prevent over-trading
- Enforces stop-loss triggers (5% default) to limit losses
- Enforces take-profit triggers (10% default) to lock in gains
- Limits maximum position size per cryptocurrency (10% default)
- Monitors daily trade limits to prevent excessive trading

## 📁 Project Structure

```
ai-trader/
├── backend/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── data_fetcher.py        # FreeCryptoAPI client
│   ├── ai_agent.py            # xAI Grok integration
│   ├── trading_engine.py      # Multi-crypto portfolio & trade simulation
│   ├── risk_management.py     # Risk management and position tracking
│   ├── technical_analysis.py  # Technical indicators (MACD, RSI, etc.)
│   ├── bot.py                 # Main trading bot orchestrator (multi-pair)
│   └── main.py                # FastAPI application
├── frontend/
│   ├── index.html             # Web UI with multi-crypto dashboard
│   ├── style.css              # Tailwind CSS styling
│   └── app.js                 # Frontend logic for multi-crypto display
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

## 🛡️ Safety Features

- **Simulated Trading**: No real money or cryptocurrency is used
- **Error Handling**: Comprehensive error handling for API failures
- **Default to HOLD**: On errors, the bot defaults to HOLD for safety
- **Risk Management**: Built-in stop-loss, take-profit, and position size limits
- **Position Tracking**: Monitors exposure across all cryptocurrencies
- **Configurable Limits**: Control trade sizes, intervals, and risk parameters
- **Activity Logging**: Full audit trail of all actions across all pairs

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
- The bot tracks **BTC/USD**, **DOGE/USD**, and **SOL/USD** simultaneously by default
- Each cryptocurrency receives independent AI analysis and trading decisions
- Market data is fetched from FreeCryptoAPI (free tier may have rate limits)
- AI decisions are based on technical analysis and may not always be profitable
- Past performance does not guarantee future results
- Risk management features help protect against large losses in simulation

## 🤝 Contributing

Feel free to fork this project and customize it for your needs. Some ideas:
- Add more cryptocurrencies to track
- Add more technical indicators (Bollinger Bands, Stochastic, etc.)
- Implement different trading strategies (momentum, mean reversion, etc.)
- Add charting/visualization with historical price charts
- Add backtesting capabilities with historical data
- Implement paper trading with real-time data
- Add email/SMS notifications for trades
- Create performance analytics and reporting

## 📄 License

This project is provided as-is for educational purposes.

## ⚠️ Disclaimer

This software is for educational and simulation purposes only. It does not provide financial advice. Cryptocurrency trading carries significant risk. Always do your own research and never invest more than you can afford to lose.

