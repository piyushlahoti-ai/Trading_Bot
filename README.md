# 🤖 Binance Futures Testnet Trading Bot

A **production-quality**, modular Python trading bot that connects to the
[Binance USDT-M Futures Testnet](https://testnet.binancefuture.com) and lets
you place **MARKET** and **LIMIT** orders via a clean CLI or an interactive
terminal menu — with full logging, rich console output, and robust error
handling throughout.

---

## ✨ Features

| Feature | Details |
|---|---|
| ✅ Testnet only | Connects exclusively to `https://testnet.binancefuture.com` |
| ✅ API key loading | Reads credentials from `.env` via `python-dotenv` |
| ✅ Credential validation | Verifies keys before placing any order |
| ✅ Market orders | BUY & SELL market orders via CLI |
| ✅ Limit orders | BUY & SELL limit orders with price validation |
| ✅ Interactive menu | Numbered Rich menu (bonus feature) |
| ✅ Input validation | Symbol, side, quantity, price — all validated with friendly errors |
| ✅ Structured logging | Rotating file log + coloured console output |
| ✅ Beautiful output | Rich-powered tables and panels |
| ✅ Robust error handling | API errors, timeouts, network failures, bad input — never crashes |

---

## 🗂️ Project Structure

```
trading_bot/
│
├── bot/
│   ├── __init__.py        # Package metadata
│   ├── client.py          # Binance client factory + credential validation
│   ├── orders.py          # place_market_order / place_limit_order
│   ├── validators.py      # All input validation helpers
│   ├── logging_config.py  # Rotating file + coloured console logging
│   ├── cli.py             # Typer commands + interactive Rich menu
│   └── config.py          # Settings dataclass (reads from .env)
│
├── logs/
│   └── trading.log        # Auto-created on first run
│
├── .env.example           # Template — copy to .env and fill in keys
├── .gitignore
├── README.md
├── requirements.txt
└── main.py                # Entry point
```

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/trading-bot.git
cd trading-bot/trading_bot
```

### 2. Create a virtual environment (recommended)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Copy the example file and fill in your Testnet API keys:

```bash
cp .env.example .env
```

Then edit `.env`:

```dotenv
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```

### Getting Testnet API Keys

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in (create a free account if needed)
3. Navigate to **API Management**
4. Generate a new API key/secret pair
5. Paste them into your `.env` file

> ⚠️ **Never** commit your `.env` file to version control. It is already in
> `.gitignore`.

---

## 🚀 Usage

### Interactive Menu (default — no arguments required)

```bash
python main.py
# or explicitly:
python main.py menu
```

You will see:

```
╭──────────────────────────────╮
│   Binance Futures Testnet    │
│         Trading Bot          │
╰──────────────────────────────╯

 Key   Action
═════════════════════════
  1    Market Buy
  2    Market Sell
  3    Limit Buy
  4    Limit Sell
  5    Exit

Select an option: _
```

---

### Market Order (CLI)

```bash
python main.py market \
  --symbol BTCUSDT \
  --side BUY \
  --quantity 0.01
```

```bash
python main.py market --symbol ETHUSDT --side SELL --quantity 0.1
```

---

### Limit Order (CLI)

```bash
python main.py limit \
  --symbol BTCUSDT \
  --side SELL \
  --quantity 0.01 \
  --price 120000
```

```bash
python main.py limit --symbol ETHUSDT --side BUY --quantity 0.5 --price 2000
```

---

### Help

```bash
python main.py --help
python main.py market --help
python main.py limit  --help
```

---

## 📊 Example Output

```
╭──────────────────────────────────╮
│     Binance Futures Testnet      │
│           Trading Bot            │
╰──────────────────────────────────╯

Placing MARKET BUY order for 0.01 BTCUSDT…

╭──────────────────────── Order Summary ─────────────────────────╮
│  Symbol           BTCUSDT                                       │
│  Side             BUY                                           │
│  Type             MARKET                                        │
│  Quantity         0.010                                         │
│  ─────────────── ──────────────────────                         │
│  Status           FILLED                                        │
│  Order ID         4521367890                                    │
│  Client Order ID  x-HNA2EJOP3                                   │
│  Executed Qty     0.010                                         │
│  Average Price    65234.50                                      │
╰─────────────────────────────────────────────────────────────────╯

╭─────────────╮
│  SUCCESS ✓  │
╰─────────────╯
```

---

## 📋 Validation Rules

| Parameter | Rule |
|---|---|
| `symbol` | Non-empty string (normalised to uppercase) |
| `side` | Must be `BUY` or `SELL` (case-insensitive) |
| `quantity` | Must be a positive number (`> 0`) |
| `price` | Required for LIMIT; must be positive. Must NOT be supplied for MARKET |
| Order type | `market` or `limit` subcommand |

Invalid input produces a friendly error panel — the app never crashes with a
raw Python traceback.

---

## 📁 Logging

Logs are written to `logs/trading.log` with automatic rotation (5 MB per file,
3 backups kept).

Every entry includes:
- Timestamp
- Log level
- Order request parameters
- Raw API response
- Errors, exceptions, and full stack traces

Example log entries:

```
2024-01-15 14:32:10 [INFO    ] trading_bot — Credentials valid ✓  |  USDT Futures balance: 10000.00
2024-01-15 14:32:11 [DEBUG   ] trading_bot — Placing BUY MARKET order | symbol=BTCUSDT | qty=0.01 | price=@ MARKET
2024-01-15 14:32:12 [INFO    ] trading_bot — MARKET order SUCCESS | id=4521367890 | symbol=BTCUSDT | side=BUY | qty=0.010 | executedQty=0.010 | avgPrice=65234.50 | status=FILLED
```

---

## 🛡️ Error Handling

| Scenario | Behaviour |
|---|---|
| Missing `.env` / empty keys | Friendly error panel before any API call |
| Invalid API key | Caught as `BinanceAPIException`, displayed clearly |
| Internet failure | `ConnectionError` caught, helpful message shown |
| Request timeout | Caught and displayed; logged with full details |
| Invalid user input | `typer.BadParameter` → friendly red error panel |
| Unexpected exception | Caught, logged with stack trace, friendly message shown |

The bot **never** exits with an unhandled Python traceback.

---

## 🔧 Configuration

All settings live in `bot/config.py` and `bot/logging_config.py`.

| Setting | Default | Description |
|---|---|---|
| `futures_base_url` | `https://testnet.binancefuture.com` | Testnet API base URL |
| `request_timeout` | `15` seconds | HTTP request timeout |
| `log_file` | `logs/trading.log` | Log file path |
| `MAX_BYTES` | `5 242 880` (5 MB) | Max log file size before rotation |
| `BACKUP_COUNT` | `3` | Number of rotated log files to keep |

---

## 🖼️ Screenshots

> Add screenshots of your terminal output here after running the bot.

---

## 🚀 Future Improvements

- [ ] **Account balance display** — show USDT balance before placing orders
- [ ] **Open positions viewer** — list current open positions in a Rich table
- [ ] **Cancel order support** — cancel an open order by ID
- [ ] **WebSocket live prices** — stream real-time price feed in the menu
- [ ] **Stop-Loss / Take-Profit** — attach SL/TP to orders
- [ ] **Order history** — retrieve and display recent order history
- [ ] **Unit tests** — pytest suite with mocked Binance responses
- [ ] **Docker support** — Dockerfile + compose for containerised deployment
- [ ] **Telegram notifications** — send order confirmations via Telegram bot

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## ⚠️ Disclaimer

This bot connects to the **Testnet only** and uses **fake** funds.
Do **not** use this code with real Binance API keys without a thorough security
review. Trading involves risk; this software is provided for educational
purposes only.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
