# 🚀 Quick Start Guide

Get your AI Crypto Trading Bot up and running in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure Your API Key

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your xAI API key:
   ```
   XAI_API_KEY=your_actual_xai_api_key_here
   ```

   **Don't have an xAI API key?** Get one at [https://x.ai](https://x.ai)

## Step 3: Run the Application

### Option A: Using the run script (Recommended)
```bash
python run.py
```

### Option B: Using uvicorn directly
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option C: Using Python module
```bash
python -m backend.main
```

## Step 4: Open the Web Interface

Open your browser and go to:
```
http://localhost:8000
```

## Step 5: Start Trading!

1. **View the Dashboard**: You'll see market data, portfolio, and controls
2. **Run a Test Cycle**: Click "⚡ Run Single Cycle" to test the bot
3. **Start Automated Trading**: Click "▶ Start Bot" to begin automatic trading
4. **Monitor Activity**: Watch the AI make decisions and execute trades!

## 🎯 What Happens Next?

The bot will:
1. ✅ Fetch real-time market data for BTC/USD
2. 🧠 Send data to Grok AI for analysis
3. 📊 Receive a BUY/SELL/HOLD decision with reasoning
4. 💰 Execute simulated trades in your virtual portfolio
5. 📝 Log all activity for your review

## ⚙️ Optional: Customize Settings

Edit `.env` to change:

```bash
# Change the trading pair
CRYPTO_PAIR=ETH/USD

# Adjust trading frequency (seconds)
FETCH_INTERVAL=120

# Set initial virtual balance
INITIAL_USD_BALANCE=50000.0

# Change trade size (0.1 = 10% of balance)
TRADE_PERCENTAGE=0.05
```

## 🛑 Stopping the Bot

- In the web interface: Click "⏹ Stop Bot"
- In the terminal: Press `Ctrl+C`

## 📊 Understanding the Dashboard

- **Market Data**: Real-time prices and technical indicators
- **Portfolio**: Your virtual USD and crypto balances
- **AI Decision**: Latest decision from Grok with reasoning
- **Trade History**: All executed trades
- **Activity Log**: Detailed log of all bot actions

## 🆘 Need Help?

Check the full [README.md](README.md) for:
- Detailed documentation
- API endpoints
- Troubleshooting
- Configuration options

## ⚠️ Remember

This is a **SIMULATION** - no real money is used! Perfect for:
- Learning about algorithmic trading
- Testing AI-driven strategies
- Understanding market dynamics
- Having fun with crypto trading!

Happy Trading! 🚀📈

