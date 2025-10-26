<div align="center">
# 🤖 Telegram Media Deep Link Bot

<div align="center">

**Welcome to the Premium Content Sharing Telegram Bot! 🎉 
This powerful Python-based bot, powered by Telebot, allows admins to upload videos or photos, customize previews, collages, and watermarks, and generate secure deep links for sharing exclusive content. Users access media via these links, with optional protection to prevent unauthorized forwarding or saving. Perfect for content creators, channels, or businesses distributing premium material safely and efficiently.

Built with ❤️ by Miyuru Dilakshan 
a passionate developer focused on innovative Telegram solutions.**

[Features](#-features) • [Installation](#-installation) • [Configuration](#-configuration) • [Usage](#-usage) • [VPS Hosting](#-vps-hosting-247) • [Support](#-support)

</div>

---

## 📋 Table of Contents

- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
  - [Quick Install (Ubuntu/Debian)](#quick-install-ubuntudebian)
  - [Manual Installation](#manual-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [VPS Hosting 24/7](#-vps-hosting-247)
- [Database](#-database)
- [Commands Reference](#-commands-reference)
- [Troubleshooting](#-troubleshooting)
- [Support](#-support)
- [License](#-license)

---

## ✨ Features

### 🎬 **Media Management**
- ✅ Support for **Videos** and **Photos**
- ✅ Generate **secure deep links** for media sharing
- ✅ **Instant link generation** (no download needed when no processing required)
- ✅ Content protection (forward/save restriction)
- ✅ Large file support (up to 2GB) via MTProto

### 🎥 **Video Processing**
- ✅ **Video Preview Generation** (3s, 5s, 7s, or 10s)
- ✅ Random clip selection for engaging previews
- ✅ **Image Collage Generation** (4, 6, 9, or 12 frames)
- ✅ Smart frame extraction from key moments

### 💧 **Watermarking**
- ✅ Custom text watermarks
- ✅ 9 position options (corners, center, edges)
- ✅ Adjustable opacity (10% - 100%)
- ✅ High-quality video watermarking with audio preservation

### 🚀 **Performance**
- ✅ **Parallel downloads** (up to 8 simultaneous connections)
- ✅ Optimized MTProto for large files
- ✅ Automatic cleanup of temporary files
- ✅ Efficient database storage

### 👥 **Administration**
- ✅ Multi-admin support
- ✅ Broadcast messages to all users
- ✅ File management (list, delete)
- ✅ Customizable bot settings
- ✅ User tracking for analytics

---

## 📦 Requirements

### System Requirements
- **OS**: Ubuntu 20.04+, Debian 10+, or any Linux distribution
- **RAM**: Minimum 512MB (1GB+ recommended)
- **Storage**: 5GB+ free space (for temporary video processing)
- **Python**: 3.8 or higher

### Software Dependencies
- Python 3.8+
- FFmpeg (for video processing)
- SQLite3 (for database)

---

## 🚀 Installation

### Quick Install (Ubuntu/Debian)

Run this single command to install everything automatically:

```bash
# Download and run the installation script
curl -sSL https://raw.githubusercontent.com/MiyuruDilakshan/Premium-Content-Sharing-Telegram-Bot/refs/heads/main/install.sh | bash
```

Or download and run manually:

```bash
# Download the script
wget https://raw.githubusercontent.com/MiyuruDilakshan/Premium-Content-Sharing-Telegram-Bot/refs/heads/main/install.sh

# Make it executable
chmod +x install.sh

# Run the installer
./install.sh
```

**What the installer does:**
- ✅ Detects your OS automatically
- ✅ Installs all system dependencies (Python, FFmpeg, SQLite)
- ✅ Clones the repository from GitHub
- ✅ Installs Python packages
- ✅ Guides you through configuration
- ✅ Sets up systemd service for 24/7 operation
- ✅ Starts the bot automatically

### Manual Installation

#### Step 1: Update System Packages

```bash
sudo apt update && sudo apt upgrade -y
```

#### Step 2: Install System Dependencies

```bash
# Install Python and pip
sudo apt install python3 python3-pip -y

# Install FFmpeg (required for video processing)
sudo apt install ffmpeg -y

# Install SQLite3 (for database)
sudo apt install sqlite3 -y

# Install system libraries
sudo apt install libopencv-dev python3-opencv -y
```

#### Step 3: Clone/Download the Bot

```bash
# Create directory for the bot
mkdir ~/telegram-media-bot
cd ~/telegram-media-bot

# Download bot files (or git clone if you have a repository)
# git clone https://github.com/MiyuruDilakshan/Premium-Content-Sharing-Telegram-Bot.git 
```


#### Step 4: Install Python Dependencies

```bash
# Install required Python packages
pip3 install -r requirements.txt
```

**Create `requirements.txt` file with these packages:**

```txt
pyTelegramBotAPI==4.14.0
python-dotenv==1.0.0
Pillow==10.1.0
opencv-python==4.8.1.78
numpy==1.24.3
requests==2.31.0
pyrogram==2.0.106
TgCrypto==1.2.5
```

Install them:

```bash
pip3 install pyTelegramBotAPI python-dotenv Pillow opencv-python numpy requests pyrogram TgCrypto
```

---

## ⚙️ Configuration

### Step 1: Create Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow the instructions:
   - Enter bot name (e.g., "My Media Bot")
   - Enter bot username (e.g., "my_media_bot")
4. **Save the Bot Token** (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Get Telegram API Credentials

1. Visit [https://my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Go to **API Development Tools**
4. Create a new application:
   - App title: "Media Bot"
   - Short name: "mediabot"
   - Platform: Other
5. **Save the API ID and API Hash**

### Step 3: Get Your User ID

1. Open Telegram and search for **@userinfobot**
2. Send `/start` command
3. **Save your User ID** (e.g., 123456789)

### Step 4: Create Environment File

Create a `.env` file in the bot directory:

```bash
nano .env
```

Add the following configuration:

```env
# ========================================
# TELEGRAM BOT CONFIGURATION
# ========================================

# Bot Token from @BotFather
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# API Credentials from https://my.telegram.org
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890

# Admin User IDs (comma-separated for multiple admins)
ADMIN_IDS=123456789,987654321

# ========================================
# OPTIONAL CUSTOMIZATION
# ========================================

# Bot Description (shown to admins)
BOT_DESCRIPTION=🎬 Premium Content Sharing Bot

Access exclusive content through secure links.

# Message shown to non-admin users
CHANNEL_MESSAGE=🔗 Join our channels for more content!
📢 Main Channel: https://t.me/your_channel
💬 Support: https://t.me/your_support
```

**Save and exit**: Press `Ctrl+X`, then `Y`, then `Enter`

### Step 5: Set File Permissions

```bash
chmod 600 .env
chmod +x bot.py
```

---

## 🎯 Usage

### Starting the Bot

#### Method 1: Direct Run (for testing)

```bash
python3 bot.py
```

#### Method 2: Run in Background (using screen)

```bash
# Install screen if not available
sudo apt install screen -y

# Create a new screen session
screen -S mediabot

# Start the bot
python3 bot.py

# Detach from screen: Press Ctrl+A, then D
# To reattach: screen -r mediabot
```

#### Method 3: Run as a Service (recommended for production)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/telegram-media-bot.service
```

Add the following content:

```ini
[Unit]
Description=Telegram Media Deep Link Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/telegram-media-bot
ExecStart=/usr/bin/python3 /home/YOUR_USERNAME/telegram-media-bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Replace `YOUR_USERNAME` with your actual username**

Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable telegram-media-bot

# Start the service
sudo systemctl start telegram-media-bot

# Check status
sudo systemctl status telegram-media-bot

# View logs
sudo journalctl -u telegram-media-bot -f
```

### Using the Bot

1. **Start the bot** on Telegram by searching for your bot username
2. **Send `/start`** - You'll see the admin panel
3. **Upload or forward media** (video or photo)
4. **Customize settings**:
   - 🎬 Video Preview (optional)
   - 🖼️ Image Collage (optional)
   - 💧 Watermark (optional)
   - 🔐 Content Protection
5. **Generate deep link** - Share the link anywhere!

---

## 🌐 VPS Hosting (24/7)

To run your bot 24/7, you need a VPS (Virtual Private Server). Here are the best options:

### 💰 Free VPS Options

| Provider | RAM | Storage | Bandwidth | Notes |
|----------|-----|---------|-----------|-------|
| **Oracle Cloud** | 1GB-24GB | 50GB+ | Unlimited | Free forever tier |
| **Google Cloud** | 1GB | 30GB | 1GB/day | $300 free credit |
| **AWS Free Tier** | 1GB | 30GB | 15GB/month | 12 months free |
| **Azure** | 1GB | 64GB | 15GB/month | $200 free credit |

### 💎 Paid VPS Options (Budget-Friendly)

| Provider | Price/Month | RAM | Storage | Bandwidth |
|----------|-------------|-----|---------|-----------|
| **DigitalOcean** | $4 | 512MB | 10GB | 500GB |
| **Vultr** | $3.50 | 512MB | 10GB | 500GB |
| **Linode** | $5 | 1GB | 25GB | 1TB |
| **Hetzner** | €4.15 | 2GB | 20GB | 20TB |
| **Contabo** | €4.99 | 4GB | 50GB | 32TB |

### 🎯 Recommended VPS Providers

#### 1. **Oracle Cloud (Best Free Option)** ⭐
```
✅ Free forever
✅ Up to 24GB RAM
✅ Unlimited bandwidth
✅ Excellent performance
🔗 https://www.oracle.com/cloud/free/
```

#### 2. **DigitalOcean (Best Paid Option)** ⭐
```
✅ Easy to use
✅ Great documentation
✅ Fast setup
✅ $200 free credit for new users
🔗 https://m.do.co/c/YOUR_REFERRAL
```

#### 3. **Contabo (Best Value)** ⭐
```
✅ Cheapest prices
✅ High resources
✅ Great for heavy use
🔗 https://contabo.com
```

### 📝 VPS Setup Tutorial

After getting a VPS, follow these steps:

```bash
# 1. Connect via SSH
ssh root@YOUR_VPS_IP

# 2. Update system
sudo apt update && sudo apt upgrade -y

# 3. Install required packages
sudo apt install python3 python3-pip ffmpeg sqlite3 git -y

# 4. Clone your bot
cd ~
git clone YOUR_REPO_URL telegram-media-bot
cd telegram-media-bot

# 5. Install Python packages
pip3 install -r requirements.txt

# 6. Configure the bot
nano .env
# (Add your tokens and IDs)

# 7. Run as a service
sudo nano /etc/systemd/system/telegram-media-bot.service
# (Copy the service file from above)

sudo systemctl daemon-reload
sudo systemctl enable telegram-media-bot
sudo systemctl start telegram-media-bot

# 8. Check if running
sudo systemctl status telegram-media-bot
```

---

## 🗄️ Database

The bot uses **SQLite3** for data storage. The database file (`media.db`) is created automatically on first run.

### Database Schema

```sql
-- Media table: stores uploaded media with deep links
CREATE TABLE media (
    payload TEXT PRIMARY KEY,
    file_id TEXT,
    media_type TEXT,
    content_protection INTEGER DEFAULT 1
);

-- Users table: stores user IDs for broadcasting
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY
);

-- Config table: stores bot configuration
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

### Backup Database

```bash
# Create backup
cp media.db media.db.backup

# Or use SQLite dump
sqlite3 media.db .dump > backup.sql

# Restore from backup
sqlite3 media.db < backup.sql
```

### Reset Database

```bash
# Stop the bot
sudo systemctl stop telegram-media-bot

# Delete database
rm media.db

# Start the bot (it will create a new database)
sudo systemctl start telegram-media-bot
```

---

## 📚 Commands Reference

### Admin Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Show admin panel | `/start` |
| `/help` | Show help message | `/help` |
| `/settings` | View current settings | `/settings` |
| `/set_preview <seconds>` | Set preview duration | `/set_preview 5` |
| `/set_collage <frames>` | Set collage frames | `/set_collage 6` |
| `/set_description <text>` | Set bot description | `/set_description My Bot` |
| `/list_files` | List all stored media | `/list_files` |
| `/delete_file <payload>` | Delete media by payload | `/delete_file abc123def` |
| `/broadcast <message>` | Send message to all users | `/broadcast Hello everyone!` |
| `/cleanup` | Clean temporary files | `/cleanup` |

### User Commands

| Command | Description |
|---------|-------------|
| `/start` | Show channel links |
| `/start <payload>` | Access media via deep link |

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### ❌ Error: "BOT_TOKEN not found"
**Solution**: Make sure `.env` file exists and contains your bot token
```bash
# Check if .env exists
ls -la .env

# Edit .env file
nano .env
```

#### ❌ Error: "FFmpeg not found"
**Solution**: Install FFmpeg
```bash
sudo apt install ffmpeg -y
```

#### ❌ Error: "Permission denied"
**Solution**: Set proper file permissions
```bash
chmod +x bot.py
chmod 600 .env
```

#### ❌ Bot not responding
**Solution**: Check if bot is running
```bash
# Check service status
sudo systemctl status telegram-media-bot

# View logs
sudo journalctl -u telegram-media-bot -f

# Restart bot
sudo systemctl restart telegram-media-bot
```

#### ❌ Error: "ModuleNotFoundError"
**Solution**: Install missing Python packages
```bash
pip3 install -r requirements.txt

# Or install specific package
pip3 install pyTelegramBotAPI
```

#### ❌ Large file download fails
**Solution**: Make sure Pyrogram and TgCrypto are installed
```bash
pip3 install pyrogram TgCrypto
```

#### ❌ Video processing takes too long
**Solution**: Disable preview/collage generation or use smaller videos

---

## 💡 Tips and Best Practices

### Performance Optimization

1. **Use SSD storage** for faster video processing
2. **Allocate at least 1GB RAM** for smooth operation
3. **Enable swap** if RAM is limited:
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### Security

1. **Keep `.env` file secure** (never share it)
2. **Use strong admin IDs** (don't add untrusted users)
3. **Regular backups** of database
4. **Update packages** regularly:
   ```bash
   sudo apt update && sudo apt upgrade -y
   pip3 install --upgrade -r requirements.txt
   ```

### Monitoring

Check bot health regularly:
```bash
# View live logs
sudo journalctl -u telegram-media-bot -f

# Check disk space
df -h

# Check memory usage
free -h

# Check bot process
ps aux | grep bot.py
```

---

## 📞 Support

Need help? Contact the developer:

### 👨‍💻 Developer Information

**Miyuru Dilakshan**

- 📧 **Email**: [Miyurudilakshan@gmail.com](mailto:Miyurudilakshan@gmail.com)
- 💬 **WhatsApp**: [+94 78 7517274](https://wa.me/94787517274)
- 🌐 **Website**: [miyuru.dev](https://miyuru.dev)
- 💼 **LinkedIn**: [linkedin.com/in/miyurudilakshan](https://www.linkedin.com/in/miyurudilakshan/)
- 🐙 **GitHub**: [github.com/miyurudilakshan](https://github.com/miyurudilakshan)

### 💬 Support Channels

- 🐛 **Report Bugs**: Open an issue on GitHub
- 💡 **Feature Requests**: Email or create a GitHub issue
- ❓ **Questions**: Email or WhatsApp

### ⏰ Response Time

- Email: 24-48 hours
- WhatsApp: 12-24 hours
- GitHub Issues: 48-72 hours

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2024 Miyuru Dilakshan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🌟 Star History

If you find this project useful, please give it a ⭐ on GitHub!

---


## 🎉 Acknowledgments

- **pyTelegramBotAPI** - Telegram Bot API wrapper
- **Pyrogram** - MTProto API framework for large files
- **FFmpeg** - Video processing
- **OpenCV** - Video frame extraction
- **Pillow** - Image processing

---

## 📈 Version History

### v1.0.0 (Current)
- ✨ Initial release
- ✅ Video & photo deep links
- ✅ Preview generation
- ✅ Collage creation
- ✅ Watermarking
- ✅ Content protection
- ✅ Multi-admin support

---

<div align="center">

**Made with ❤️ by [Miyuru Dilakshan](https://miyuru.dev)**

[⬆ Back to Top](#-telegram-media-deep-link-bot)

</div>
