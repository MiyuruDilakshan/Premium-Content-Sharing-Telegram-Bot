#!/bin/bash

# ========================================
# Telegram Media Deep Link Bot
# Automated Installation Script
# Author: Miyuru Dilakshan
# Website: miyuru.dev
# ========================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emojis
CHECK="✅"
CROSS="❌"
ARROW="➤"
STAR="⭐"
ROCKET="🚀"
GEAR="⚙️"
PACKAGE="📦"
KEY="🔑"
WARNING="⚠️"
INFO="ℹ️"

# ========================================
# FUNCTIONS
# ========================================

print_header() {
    clear
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                                                        ║${NC}"
    echo -e "${PURPLE}║       ${CYAN}🤖 TELEGRAM MEDIA DEEP LINK BOT 🤖${PURPLE}        ║${NC}"
    echo -e "${PURPLE}║                                                        ║${NC}"
    echo -e "${PURPLE}║           ${GREEN}Automated Installation Script${PURPLE}            ║${NC}"
    echo -e "${PURPLE}║                                                        ║${NC}"
    echo -e "${PURPLE}║              ${YELLOW}👨‍💻 Miyuru Dilakshan 👨‍💻${PURPLE}               ║${NC}"
    echo -e "${PURPLE}║               ${BLUE}https://miyuru.dev${PURPLE}                ║${NC}"
    echo -e "${PURPLE}║                                                        ║${NC}"
    echo -e "${PURPLE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}${CHECK} $1${NC}"
}

print_error() {
    echo -e "${RED}${CROSS} $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}${WARNING} $1${NC}"
}

print_info() {
    echo -e "${CYAN}${INFO} $1${NC}"
}

print_step() {
    echo -e "${BLUE}${ARROW} $1${NC}"
}

check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "This script should NOT be run as root!"
        print_info "Please run as a regular user. The script will ask for sudo when needed."
        exit 1
    fi
}

check_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    else
        print_error "Cannot detect OS. This script supports Ubuntu/Debian/CentOS/Fedora."
        exit 1
    fi
    
    print_info "Detected OS: $OS $VER"
}

install_dependencies() {
    print_step "Installing system dependencies..."
    
    if [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
        # Update package list
        print_info "Updating package list..."
        sudo apt update -y
        
        # Install dependencies
        print_info "Installing Python, FFmpeg, SQLite, and other tools..."
        sudo apt install -y \
            python3 \
            python3-pip \
            python3-dev \
            ffmpeg \
            sqlite3 \
            git \
            curl \
            wget \
            libopencv-dev \
            python3-opencv \
            build-essential \
            libssl-dev \
            libffi-dev
        
    elif [[ "$OS" == "centos" ]] || [[ "$OS" == "rhel" ]] || [[ "$OS" == "fedora" ]]; then
        print_info "Updating package list..."
        sudo yum update -y
        
        print_info "Installing Python, FFmpeg, SQLite, and other tools..."
        sudo yum install -y \
            python3 \
            python3-pip \
            python3-devel \
            ffmpeg \
            sqlite \
            git \
            curl \
            wget \
            opencv \
            opencv-devel \
            gcc \
            gcc-c++ \
            make
    else
        print_error "Unsupported OS: $OS"
        exit 1
    fi
    
    print_success "System dependencies installed successfully!"
}

clone_repository() {
    print_step "Cloning bot repository..."
    
    BOT_DIR="$HOME/telegram-media-bot"
    
    if [[ -d "$BOT_DIR" ]]; then
        print_warning "Directory $BOT_DIR already exists!"
        read -p "Do you want to remove it and clone fresh? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Removing old directory..."
            rm -rf "$BOT_DIR"
        else
            print_info "Using existing directory..."
            cd "$BOT_DIR"
            return
        fi
    fi
    
    print_info "Cloning from GitHub..."
    git clone https://github.com/MiyuruDilakshan/Premium-Content-Sharing-Telegram-Bot.git "$BOT_DIR"
    
    cd "$BOT_DIR"
    print_success "Repository cloned successfully!"
}

install_python_packages() {
    print_step "Installing Python packages..."
    
    # Upgrade pip
    print_info "Upgrading pip..."
    python3 -m pip install --upgrade pip
    
    # Install requirements
    if [[ -f "requirements.txt" ]]; then
        print_info "Installing from requirements.txt..."
        pip3 install -r requirements.txt
    else
        print_info "requirements.txt not found. Installing packages manually..."
        pip3 install pyTelegramBotAPI python-dotenv Pillow opencv-python numpy requests pyrogram TgCrypto
    fi
    
    print_success "Python packages installed successfully!"
}

configure_bot() {
    print_step "Configuring bot..."
    
    if [[ -f ".env" ]]; then
        print_warning ".env file already exists!"
        read -p "Do you want to reconfigure? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Skipping configuration..."
            return
        fi
    fi
    
    echo ""
    print_info "${KEY} Let's set up your bot credentials..."
    echo ""
    
    # Bot Token
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    print_info "Step 1: Get Bot Token from @BotFather"
    echo -e "${YELLOW}  1. Open Telegram and search for @BotFather${NC}"
    echo -e "${YELLOW}  2. Send /newbot command${NC}"
    echo -e "${YELLOW}  3. Follow instructions and copy the token${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    read -p "$(echo -e ${GREEN}Enter Bot Token: ${NC})" BOT_TOKEN
    
    # API ID
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    print_info "Step 2: Get API Credentials from https://my.telegram.org"
    echo -e "${YELLOW}  1. Visit https://my.telegram.org${NC}"
    echo -e "${YELLOW}  2. Log in with your phone number${NC}"
    echo -e "${YELLOW}  3. Go to 'API Development Tools'${NC}"
    echo -e "${YELLOW}  4. Create a new application${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    read -p "$(echo -e ${GREEN}Enter API ID: ${NC})" API_ID
    read -p "$(echo -e ${GREEN}Enter API Hash: ${NC})" API_HASH
    
    # Admin IDs
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    print_info "Step 3: Get Your User ID"
    echo -e "${YELLOW}  1. Open Telegram and search for @userinfobot${NC}"
    echo -e "${YELLOW}  2. Send /start command${NC}"
    echo -e "${YELLOW}  3. Copy your User ID${NC}"
    echo -e "${YELLOW}  Note: For multiple admins, separate IDs with commas (e.g., 123,456)${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    read -p "$(echo -e ${GREEN}'Enter Admin User ID(s): '${NC})" ADMIN_IDS
    
    # Optional: Channel Message
    echo ""
    print_info "Step 4: Customize Bot Messages (Optional - Press Enter to skip)"
    read -p "$(echo -e ${GREEN}'Enter Channel Message [Leave empty for default]: '${NC})" CHANNEL_MESSAGE
    
    # Create .env file
    cat > .env << EOF
# ========================================
# TELEGRAM BOT CONFIGURATION
# ========================================

# Bot Token from @BotFather
BOT_TOKEN=$BOT_TOKEN

# API Credentials from https://my.telegram.org
API_ID=$API_ID
API_HASH=$API_HASH

# Admin User IDs (comma-separated)
ADMIN_IDS=$ADMIN_IDS

# ========================================
# OPTIONAL CUSTOMIZATION
# ========================================

# Bot Description
BOT_DESCRIPTION=🎬 Premium Content Sharing Bot\n\nAccess exclusive content through secure links.

# Message shown to non-admin users
${CHANNEL_MESSAGE:+CHANNEL_MESSAGE=$CHANNEL_MESSAGE}
EOF
    
    # Set proper permissions
    chmod 600 .env
    
    print_success "Configuration saved to .env file!"
}

create_systemd_service() {
    print_step "Creating systemd service..."
    
    SERVICE_FILE="/etc/systemd/system/telegram-media-bot.service"
    
    if [[ -f "$SERVICE_FILE" ]]; then
        print_warning "Service file already exists!"
        read -p "Do you want to overwrite it? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Skipping service creation..."
            return
        fi
    fi
    
    print_info "Creating service file..."
    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Telegram Media Deep Link Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BOT_DIR
ExecStart=/usr/bin/python3 $BOT_DIR/bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    print_info "Reloading systemd daemon..."
    sudo systemctl daemon-reload
    
    print_info "Enabling service to start on boot..."
    sudo systemctl enable telegram-media-bot
    
    print_success "Systemd service created successfully!"
}

start_bot() {
    print_step "Starting bot..."
    
    echo ""
    print_info "How would you like to run the bot?"
    echo ""
    echo -e "${YELLOW}1)${NC} Run as systemd service (recommended for 24/7 operation)"
    echo -e "${YELLOW}2)${NC} Run in screen session (good for testing)"
    echo -e "${YELLOW}3)${NC} Run directly (will stop when terminal closes)"
    echo -e "${YELLOW}4)${NC} Skip - I'll start it manually"
    echo ""
    read -p "$(echo -e ${GREEN}Enter your choice [1-4]: ${NC})" choice
    
    case $choice in
        1)
            print_info "Starting as systemd service..."
            sudo systemctl start telegram-media-bot
            sleep 2
            sudo systemctl status telegram-media-bot --no-pager
            print_success "Bot started as systemd service!"
            echo ""
            print_info "Useful commands:"
            echo -e "${CYAN}  • Check status:${NC}  sudo systemctl status telegram-media-bot"
            echo -e "${CYAN}  • View logs:${NC}     sudo journalctl -u telegram-media-bot -f"
            echo -e "${CYAN}  • Restart:${NC}       sudo systemctl restart telegram-media-bot"
            echo -e "${CYAN}  • Stop:${NC}          sudo systemctl stop telegram-media-bot"
            ;;
        2)
            if ! command -v screen &> /dev/null; then
                print_info "Installing screen..."
                if [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
                    sudo apt install -y screen
                else
                    sudo yum install -y screen
                fi
            fi
            print_info "Starting in screen session..."
            screen -dmS mediabot bash -c "cd $BOT_DIR && python3 bot.py"
            print_success "Bot started in screen session 'mediabot'!"
            echo ""
            print_info "Useful commands:"
            echo -e "${CYAN}  • Attach to session:${NC}  screen -r mediabot"
            echo -e "${CYAN}  • Detach (inside):${NC}    Ctrl+A then D"
            echo -e "${CYAN}  • List sessions:${NC}      screen -ls"
            ;;
        3)
            print_info "Starting bot directly..."
            cd "$BOT_DIR"
            python3 bot.py
            ;;
        4)
            print_info "Skipping bot startup..."
            echo ""
            print_info "To start the bot manually:"
            echo -e "${CYAN}  cd $BOT_DIR${NC}"
            echo -e "${CYAN}  python3 bot.py${NC}"
            ;;
        *)
            print_error "Invalid choice!"
            ;;
    esac
}

print_completion() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                        ║${NC}"
    echo -e "${GREEN}║            ${STAR} INSTALLATION COMPLETED! ${STAR}            ║${NC}"
    echo -e "${GREEN}║                                                        ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    print_success "Bot installed successfully!"
    echo ""
    print_info "${ROCKET} Quick Start Guide:"
    echo ""
    echo -e "${CYAN}1. Test your bot:${NC}"
    echo -e "   Open Telegram and search for your bot"
    echo -e "   Send /start command"
    echo ""
    echo -e "${CYAN}2. Bot directory:${NC}"
    echo -e "   cd $BOT_DIR"
    echo ""
    echo -e "${CYAN}3. Configuration file:${NC}"
    echo -e "   nano $BOT_DIR/.env"
    echo ""
    echo -e "${CYAN}4. View logs (if using systemd):${NC}"
    echo -e "   sudo journalctl -u telegram-media-bot -f"
    echo ""
    echo -e "${CYAN}5. Manual start:${NC}"
    echo -e "   cd $BOT_DIR && python3 bot.py"
    echo ""
    print_info "${INFO} Documentation:"
    echo -e "   ${BLUE}https://github.com/MiyuruDilakshan/Premium-Content-Sharing-Telegram-Bot${NC}"
    echo ""
    print_info "${KEY} Need Help?"
    echo -e "   ${YELLOW}Email:${NC}    Miyurudilakshan@gmail.com"
    echo -e "   ${YELLOW}WhatsApp:${NC} +94 78 7517274"
    echo -e "   ${YELLOW}Website:${NC}  https://miyuru.dev"
    echo -e "   ${YELLOW}LinkedIn:${NC} https://www.linkedin.com/in/miyurudilakshan"
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${PURPLE}         Made with ❤️  by Miyuru Dilakshan${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# ========================================
# MAIN EXECUTION
# ========================================

main() {
    print_header
    
    # Pre-flight checks
    print_step "Running pre-flight checks..."
    check_root
    check_os
    print_success "Pre-flight checks passed!"
    echo ""
    
    # Confirmation
    print_warning "This script will install:"
    echo -e "${CYAN}  • System dependencies (Python, FFmpeg, SQLite, etc.)${NC}"
    echo -e "${CYAN}  • Python packages (pyTelegramBotAPI, Pyrogram, etc.)${NC}"
    echo -e "${CYAN}  • Telegram Media Deep Link Bot${NC}"
    echo ""
    read -p "$(echo -e ${GREEN}Do you want to continue? [Y/n]: ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_error "Installation cancelled by user."
        exit 0
    fi
    
    echo ""
    
    # Installation steps
    install_dependencies
    echo ""
    
    clone_repository
    echo ""
    
    install_python_packages
    echo ""
    
    configure_bot
    echo ""
    
    create_systemd_service
    echo ""
    
    start_bot
    echo ""
    
    print_completion
}

# Run main function
main

# Exit successfully
exit 0
