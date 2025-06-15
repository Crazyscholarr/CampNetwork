# CampNetwork Bot 🚀

A powerful and flexible automation tool for **Camp Network** with multiple features for testnet activities and loyalty campaigns.


## 🌟 Features

- ✨ Multi-threaded processing with configurable threads
- 🔄 Automatic retries with configurable attempts
- 🔐 Proxy support with rotation
- 📊 Account range selection and exact account targeting
- 🎲 Random pauses between operations
- 🔔 Telegram logging integration
- 📝 Detailed transaction tracking and wallet statistics
- 🧩 Modular task system with custom sequences
- 🤖 Social media integration (Twitter, Discord)
- 💾 SQLite database for task management
- 🌐 Web-based configuration interface
- 💱 CEX withdrawal support (OKX, Bitget)
- 🔄 Cross-chain refueling via CrustySwap

## 🎯 Available Actions

**Network Operations:**
- Camp Network Faucet
- Loyalty Platform Integration
- Social Media Connections (Twitter, Discord)
- Display Name Configuration

**Loyalty Campaigns:**
- StoryChain
- Token Tails
- AWANA
- Pictographs
- Hitmakr
- Panenka
- Scoreplay
- Wide Worlds
- EntertainM
- RewardedTV
- Sporting Cristal
- Belgrano
- ARCOIN
- Kraft
- SummitX
- Pixudi
- Clusters
- JukeBlox
- Camp Network

**DeFi Operations:**
- CrustySwap Refueling
- Cross-chain Bridge Operations
- CEX Withdrawals (ETH from OKX/Bitget)

## 📋 Requirements

- Python `3.11.1` - `3.11.6`
- Private keys for Camp Network wallets
- Proxies for enhanced security (static proxies ONLY for loyalty campaigns)
- Twitter tokens for social media integration
- Discord tokens for social media integration
- Email addresses for account verification

## 🚀 Installation

### Option 1: Automatic Installation (Windows)
```bash
# Run the installation script
install.bat
```

### Option 2: Manual Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/Crazyscholarr/CampNetwork.git
   cd CampNetwork
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 📁 Project Structure

```
StarLabs-CampNetwork/
├── data/
│   ├── private_keys.txt         # Wallet private keys
│   ├── proxies.txt              # Proxy addresses
│   ├── twitter_tokens.txt       # Twitter authentication tokens
│   ├── discord_tokens.txt       # Discord authentication tokens
│   └── emails.txt               # Email addresses
├── src/
│   ├── model/
│   │   ├── projects/            # Project-specific modules
│   │   │   ├── camp_loyalty/    # Loyalty platform integration
│   │   │   ├── crustyswap/      # CrustySwap operations
│   │   │   └── others/          # Other project modules
│   │   ├── database/            # Database management
│   │   ├── onchain/             # Blockchain interactions
│   │   └── offchain/            # Off-chain operations
│   └── utils/                   # Helper utilities
├── config.yaml                  # Main configuration file
├── tasks.py                     # Task definitions
├── main.py                      # Entry point
├── process.py                   # Main process handler
└── start.bat                    # Windows startup script
```

## 📝 Configuration

### 1. Data Files

Create and populate the following files in the `data/` directory:

- **`private_keys.txt`**: One private key per line
- **`proxies.txt`**: One proxy per line (format: `http://user:pass@ip:port`)
- **`twitter_tokens.txt`**: One Twitter token per line
- **`discord_tokens.txt`**: One Discord token per line  
- **`emails.txt`**: One email address per line

### 2. Configuration File (`config.yaml`)

```yaml
SETTINGS:
  THREADS: 1                      # Number of parallel threads
  ATTEMPTS: 5                     # Retry attempts for failed actions
  ACCOUNTS_RANGE: [0, 0]          # Wallet range to use (default: all)
  EXACT_ACCOUNTS_TO_USE: []       # Specific wallets to use (default: all)
  SHUFFLE_WALLETS: true           # Randomize wallet processing order
  PAUSE_BETWEEN_ATTEMPTS: [5, 10] # Random pause between retries
  PAUSE_BETWEEN_SWAPS: [10, 20]   # Random pause between swap operations
  RANDOM_PAUSE_BETWEEN_ACCOUNTS: [10, 20]  # Pause between accounts
  RANDOM_PAUSE_BETWEEN_ACTIONS: [10, 20]   # Pause between actions
  RANDOM_INITIALIZATION_PAUSE: [10, 50]    # Initial pause before start
  SEND_TELEGRAM_LOGS: false       # Enable Telegram notifications
  TELEGRAM_BOT_TOKEN: "your_token"
  TELEGRAM_USERS_IDS: [123456789]

LOYALTY:
  REPLACE_FAILED_TWITTER_ACCOUNT: true
  MAX_ATTEMPTS_TO_COMPLETE_QUEST: 15

CRUSTY_SWAP:
  NETWORKS_TO_REFUEL_FROM: ["Arbitrum", "Optimism", "Base"]
  AMOUNT_TO_REFUEL: [0.0002, 0.0003]
  MINIMUM_BALANCE_TO_REFUEL: 99999
  WAIT_FOR_FUNDS_TO_ARRIVE: true
  MAX_WAIT_TIME: 999999
  BRIDGE_ALL: false
  BRIDGE_ALL_MAX_AMOUNT: 0.01

EXCHANGES:
  name: "OKX"  # Supported: "OKX", "BITGET"
  apiKey: 'your_api_key'
  secretKey: 'your_secret_key'
  passphrase: 'your_passphrase'
  withdrawals:
    - currency: "ETH"
      networks: ["Arbitrum", "Optimism", "Base"]
      min_amount: 0.0004
      max_amount: 0.0006
      max_balance: 0.005
      wait_for_funds: true
      max_wait_time: 99999
      retries: 3
```

## 🎮 Usage

### Starting the Bot

#### Option 1: Using Batch File (Windows)
```bash
start.bat
```

#### Option 2: Direct Python Execution
```bash
python main.py
```
#Captcha : @solvium_crypto_bot
### Interactive Menu

The bot provides an interactive menu with the following options:

1. **🚀 Start farming** - Begin task execution
2. **⚙️ Edit config** - Web-based configuration editor
3. **💾 Database actions** - Database management tools

### Task Configuration

Edit `tasks.py` to select which modules to run:

```python
TASKS = ["CRUSTY_SWAP"]  # Replace with your desired tasks
```

**Available task presets:**

**Basic Operations:**
- `FAUCET` - Claim Camp Network faucet
- `SKIP` - Skip task (for testing/logging)

**Loyalty Platform:**
- `CAMP_LOYALTY` - Complete loyalty setup and quests
- `CAMP_LOYALTY_CONNECT_SOCIALS` - Connect social media accounts
- `CAMP_LOYALTY_SET_DISPLAY_NAME` - Set display name
- `CAMP_LOYALTY_COMPLETE_QUESTS` - Complete available quests

**Individual Campaigns:**
- `CAMP_LOYALTY_STORYCHAIN` - StoryChain campaign
- `CAMP_LOYALTY_TOKEN_TAILS` - Token Tails campaign
- `CAMP_LOYALTY_AWANA` - AWANA campaign
- `CAMP_LOYALTY_PICTOGRAPHS` - Pictographs campaign
- `CAMP_LOYALTY_HITMAKR` - Hitmakr campaign
- `CAMP_LOYALTY_PANENKA` - Panenka campaign
- `CAMP_LOYALTY_SCOREPLAY` - Scoreplay campaign
- `CAMP_LOYALTY_WIDE_WORLDS` - Wide Worlds campaign
- `CAMP_LOYALTY_ENTERTAINM` - EntertainM campaign
- `CAMP_LOYALTY_REWARDED_TV` - RewardedTV campaign
- `CAMP_LOYALTY_SPORTING_CRISTAL` - Sporting Cristal campaign
- `CAMP_LOYALTY_BELGRANO` - Belgrano campaign
- `CAMP_LOYALTY_ARCOIN` - ARCOIN campaign
- `CAMP_LOYALTY_KRAFT` - Kraft campaign
- `CAMP_LOYALTY_SUMMITX` - SummitX campaign
- `CAMP_LOYALTY_PIXUDI` - Pixudi campaign
- `CAMP_LOYALTY_CLUSTERS` - Clusters campaign
- `CAMP_LOYALTY_JUKEBLOX` - JukeBlox campaign
- `CAMP_LOYALTY_CAMP_NETWORK` - Camp Network campaign

**DeFi Operations:**
- `CRUSTY_SWAP` - CrustySwap refueling operations

### Custom Task Sequences

Create custom task sequences combining different modules:

```python
TASKS = ["MY_CUSTOM_TASK"]

MY_CUSTOM_TASK = [
    "faucet",                                    # Run faucet first
    "camp_loyalty_connect_socials",              # Connect socials
    "camp_loyalty_set_display_name",             # Set display name
    ("camp_loyalty_awana", "camp_loyalty_kraft"), # Run both in random order
    ["camp_loyalty_storychain", "camp_loyalty_token_tails"], # Run one randomly
    "crusty_refuel",                             # Refuel via CrustySwap
]
```

**Task Sequence Syntax:**
- `( )` - Execute all modules inside brackets in random order
- `[ ]` - Execute only one module inside brackets randomly
- Regular strings - Execute in sequence

### Database Management

The bot includes a comprehensive database system for task management:

1. **Create/Reset Database** - Initialize or reset the task database
2. **Generate New Tasks** - Add tasks for completed wallets
3. **Show Database Contents** - View current database state
4. **Regenerate Tasks** - Reset tasks for all wallets
5. **Add Wallets** - Add new wallets to the database

### Web Configuration Interface

Access the web-based configuration editor:
1. Run the bot and select option `[2] ⚙️ Edit config`
2. Open your browser to `http://127.0.0.1:3456`
3. Edit configuration parameters through the web interface
4. Save changes and restart the bot

## ⚠️ Important Notes

### Loyalty Campaigns
- **Static proxies are required** for loyalty campaigns
- Residential proxies can be used but **without IP rotation**
- Failed Twitter accounts can be automatically replaced if configured

### Proxy Requirements
- Use format: `http://user:pass@ip:port`
- Static proxies recommended for stability
- Proxy rotation supported for most operations

### CEX Integration
- Supports OKX and Bitget exchanges
- Automatic ETH withdrawal to specified networks
- Configurable withdrawal amounts and timing

## 🔧 Advanced Features

### Telegram Integration
Configure Telegram notifications for real-time updates:
```yaml
SEND_TELEGRAM_LOGS: true
TELEGRAM_BOT_TOKEN: "your_bot_token"
TELEGRAM_USERS_IDS: [your_user_id]
```

### Multi-threading
Adjust concurrent operations:
```yaml
THREADS: 3  # Run 3 accounts simultaneously
```

### Account Selection
Target specific accounts:
```yaml
ACCOUNTS_RANGE: [5, 10]  # Use accounts 5-10
# OR
EXACT_ACCOUNTS_TO_USE: [1, 5, 8]  # Use specific accounts
```

## 📊 Monitoring and Logs

- **Console Logs**: Real-time progress and status updates
- **File Logs**: Detailed logs saved to `logs/app.log`
- **Telegram Notifications**: Optional real-time alerts
- **Wallet Statistics**: Comprehensive wallet performance tracking
- **Database Tracking**: Persistent task state management

## 🛠️ Troubleshooting

### Common Issues

1. **Database Errors**: Ensure database is created via the database menu
2. **Proxy Issues**: Verify proxy format and connectivity
3. **Token Errors**: Check Twitter/Discord token validity
4. **Task Failures**: Review logs for specific error messages

### Getting Help

- Review console logs for error details
- Ensure all configuration files are properly formatted

## 📜 License

MIT License

## ⚠️ Disclaimer

This tool is for educational purposes only. Use at your own risk and in accordance with relevant terms of service. Always ensure compliance with platform terms and local regulations.

# CampNetwork
https://t.me/dgpubretro
