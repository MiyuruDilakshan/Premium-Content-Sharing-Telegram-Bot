"""
Telegram Media Deep Link Bot
Author: Miyuru Dilakshan
Website: miyuru.dev
Email: Miyurudilakshan@gmail.com

A powerful Telegram bot for generating deep links to media files with 
advanced preview generation, collage creation, and watermarking features.
"""

import telebot
from telebot import types
import os
import sqlite3
import uuid
import cv2
import logging
import json
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import asyncio
from threading import Thread
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# ======================== LOGGING CONFIGURATION ========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ======================== ENVIRONMENT VARIABLES ========================
load_dotenv()

# Required: Get from @BotFather on Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found! Please set it in .env file")

# Required: Get from https://my.telegram.org
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
if not API_ID or not API_HASH:
    raise ValueError("API_ID and API_HASH not found! Please set them in .env file")

# Required: Comma-separated list of admin user IDs
ADMIN_IDS = os.getenv('ADMIN_IDS', '')
if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS not found! Please set at least one admin ID in .env file")

ADMINS = [int(uid.strip()) for uid in ADMIN_IDS.split(',') if uid.strip()]

# Optional: Customize bot messages
BOT_DESCRIPTION = os.getenv('BOT_DESCRIPTION', '🎬 Premium Content Sharing Bot\n\nAccess exclusive content through secure links.')
CHANNEL_MESSAGE = os.getenv('CHANNEL_MESSAGE', 'Join our channels for more content!')

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# ======================== GLOBAL CONFIGURATION ========================
# Temporary storage for pending uploads
PENDING_UPLOADS = {}

# Bot configuration with defaults
BOT_CONFIG = {
    'bot_description': BOT_DESCRIPTION,
    'preview_length': 3,  # Default preview duration in seconds
    'collage_frames': 4,  # Default number of frames in collage
    'collage_quality': 85,  # JPEG quality for collage
    'generate_preview': True,  # Generate video preview by default
    'generate_collage': True,  # Generate collage by default
    'watermark_enabled': False,  # Watermark disabled by default
    'watermark_text': '',  # Default watermark text
    'watermark_position': 'bottom-right',  # Default watermark position
    'watermark_opacity': 0.5,  # Default watermark opacity
    'content_protection': True,  # Protect content from forwarding by default
}

# ======================== DATABASE FUNCTIONS ========================
def get_db():
    """Create database connection with thread safety"""
    conn = sqlite3.connect('media.db', check_same_thread=False)
    return conn

def init_database():
    """Initialize database tables and schema"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Media table: stores media files with payloads
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS media (
            payload TEXT PRIMARY KEY, 
            file_id TEXT, 
            media_type TEXT, 
            content_protection INTEGER DEFAULT 1
        )
    ''')
    
    # Users table: stores user IDs for broadcasting
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    
    # Config table: stores bot configuration
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY, 
            value TEXT
        )
    ''')
    
    # Add content_protection column if it doesn't exist (for existing databases)
    try:
        cursor.execute('ALTER TABLE media ADD COLUMN content_protection INTEGER DEFAULT 1')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized successfully")

def load_config():
    """Load configuration from database"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM config")
    results = cursor.fetchall()
    conn.close()
    
    for key, value in results:
        if key in BOT_CONFIG:
            try:
                BOT_CONFIG[key] = json.loads(value)
            except:
                BOT_CONFIG[key] = value
    
    logger.info(f"📋 Loaded config: {BOT_CONFIG}")

def save_config(key, value):
    """Save configuration to database"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", 
        (key, json.dumps(value))
    )
    conn.commit()
    conn.close()
    BOT_CONFIG[key] = value
    logger.info(f"💾 Saved config: {key} = {value}")

# ======================== UTILITY FUNCTIONS ========================
def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMINS

def cleanup_files():
    """Clean up all temporary files"""
    temp_files = [
        'temp.mp4', 'preview.mp4', 'collage.jpg', 'watermarked.mp4', 
        '_download_temp.py', 'temp_no_audio.mp4'
    ]
    
    # Also clean up files matching patterns
    import glob
    temp_patterns = [
        'temp_*.mp4', 'temp_*.txt', 'temp_*.jpg', 'temp_*.png',
        'preview_*.mp4', 'collage_*.jpg', 'watermarked_*.mp4', 
        'download_*.mp4', 'temp_clip_*.mp4', '*_temp.mp4',
        '*.part*', 'temp.mp4.part*', '*.pyc'
    ]
    
    for pattern in temp_patterns:
        for file in glob.glob(pattern):
            temp_files.append(file)
    
    # Clean up __pycache__ directory
    import shutil
    if os.path.exists('__pycache__'):
        try:
            shutil.rmtree('__pycache__')
            logger.info("🗑️ Removed __pycache__ directory")
        except Exception as e:
            logger.error(f"❌ Failed to remove __pycache__: {e}")
    
    # Remove all temp files
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                logger.info(f"🗑️ Removed {temp_file}")
            except Exception as e:
                logger.error(f"❌ Failed to remove {temp_file}: {e}")

# ======================== DOWNLOAD FUNCTIONS ========================
def download_file_parallel(url, destination, num_connections=8, chunk_size=1024*1024):
    """
    Download file using multiple parallel connections for maximum speed
    
    Args:
        url: File URL to download
        destination: Path to save the file
        num_connections: Number of parallel connections (default: 8)
        chunk_size: Size of each chunk in bytes (default: 1MB)
    """
    temp_files = []
    
    try:
        logger.info(f"🚀 Starting parallel download with {num_connections} connections...")
        start_time = time.time()
        
        # Get file size
        response = requests.head(url, timeout=10)
        file_size = int(response.headers.get('content-length', 0))
        
        if file_size == 0:
            logger.warning("⚠️ Could not determine file size, using single connection")
            response = requests.get(url, stream=True, timeout=30)
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        
        logger.info(f"📦 File size: {file_size / (1024*1024):.2f} MB")
        
        # Calculate chunk size per connection
        part_size = file_size // num_connections
        
        def download_part(part_num, start_byte, end_byte):
            """Download a specific part of the file"""
            temp_file = f"{destination}.part{part_num}"
            temp_files.append(temp_file)
            
            headers = {'Range': f'bytes={start_byte}-{end_byte}'}
            try:
                response = requests.get(url, headers=headers, stream=True, timeout=60)
                with open(temp_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                logger.info(f"✅ Part {part_num+1}/{num_connections} downloaded ({(end_byte-start_byte)/(1024*1024):.2f} MB)")
                return True
            except Exception as e:
                logger.error(f"❌ Error downloading part {part_num}: {e}")
                return False
        
        # Download all parts in parallel
        with ThreadPoolExecutor(max_workers=num_connections) as executor:
            futures = []
            for i in range(num_connections):
                start_byte = i * part_size
                end_byte = start_byte + part_size - 1 if i < num_connections - 1 else file_size - 1
                future = executor.submit(download_part, i, start_byte, end_byte)
                futures.append(future)
            
            # Wait for all downloads to complete
            for future in as_completed(futures):
                if not future.result():
                    raise Exception("Failed to download one or more parts")
        
        # Merge all parts
        logger.info("🔗 Merging downloaded parts...")
        with open(destination, 'wb') as output_file:
            for i in range(num_connections):
                temp_file = f"{destination}.part{i}"
                with open(temp_file, 'rb') as part_file:
                    output_file.write(part_file.read())
                os.remove(temp_file)
        
        elapsed_time = time.time() - start_time
        speed_mbps = (file_size / (1024*1024)) / elapsed_time
        logger.info(f"✅ Download completed in {elapsed_time:.2f}s ({speed_mbps:.2f} MB/s)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Parallel download failed: {e}")
        # Clean up partial files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
        return False

def download_with_pyrogram(chat_id, message_id, destination):
    """Download large files using Pyrogram with MTProto optimization"""
    try:
        import subprocess
        import sys
        
        abs_destination = os.path.abspath(destination)
        
        # Create optimized download script using Pyrogram
        script = f'''
import asyncio
from pyrogram import Client
import sys
import os
import time

API_ID = {API_ID}
API_HASH = "{API_HASH}"
TOKEN = "{BOT_TOKEN}"

downloaded_bytes = 0
total_size = 0
start_time = time.time()
last_update = 0

def progress(current, total):
    """Progress callback with speed calculation"""
    global downloaded_bytes, total_size, start_time, last_update
    downloaded_bytes = current
    total_size = total
    
    current_time = time.time()
    if current_time - last_update >= 2.0 or current == total:
        last_update = current_time
        
        percentage = (current / total) * 100
        elapsed = current_time - start_time
        speed_mbps = (current / (1024 * 1024)) / elapsed if elapsed > 0 else 0
        
        downloaded_mb = current / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        
        if speed_mbps > 0:
            remaining_mb = (total - current) / (1024 * 1024)
            eta_seconds = remaining_mb / speed_mbps
            eta_min = int(eta_seconds / 60)
            eta_sec = int(eta_seconds % 60)
            eta_str = f"ETA: {{eta_min}}m {{eta_sec}}s"
        else:
            eta_str = "ETA: calculating..."
        
        print(f"📥 {{percentage:.1f}}% | {{downloaded_mb:.1f}}/{{total_mb:.1f}} MB | {{speed_mbps:.2f}} MB/s | {{eta_str}}", flush=True)

async def download():
    try:
        app = Client(
            "bot_session", 
            api_id=API_ID, 
            api_hash=API_HASH, 
            bot_token=TOKEN,
            workdir="{os.path.dirname(abs_destination)}",
            sleep_threshold=60,
            max_concurrent_transmissions=16,
            no_updates=True
        )
        
        async with app:
            msg = await app.get_messages({chat_id}, {message_id})
            if msg and msg.video:
                print(f"📄 File: {{msg.video.file_name or 'video.mp4'}}", flush=True)
                print(f"📦 Size: {{msg.video.file_size / (1024*1024):.1f}} MB", flush=True)
                print(f"⚡ Starting optimized MTProto download...", flush=True)
                
                file_path = await app.download_media(
                    msg.video, 
                    file_name="{abs_destination}",
                    progress=progress,
                    block=True
                )
                
                print(f"\\n✅ Download completed!", flush=True)
                
                if os.path.exists('{abs_destination}'):
                    actual_size = os.path.getsize('{abs_destination}')
                    elapsed = time.time() - start_time
                    avg_speed = (actual_size / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                    elapsed_min = int(elapsed / 60)
                    elapsed_sec = int(elapsed % 60)
                    print(f"⏱️  Total: {{elapsed_min}}m {{elapsed_sec}}s | Speed: {{avg_speed:.2f}} MB/s", flush=True)
                
                return True
            else:
                print(f"❌ No video found", flush=True)
                return False
    except Exception as e:
        print(f"❌ Error: {{e}}", flush=True)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(download())
    sys.exit(0 if result else 1)
'''
        
        script_path = '_download_optimized.py'
        with open(script_path, 'w') as f:
            f.write(script)
        
        logger.info(f"📥 Starting optimized download for chat_id={chat_id}, message_id={message_id}")
        logger.info(f"📂 Destination: {abs_destination}")
        
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in iter(process.stdout.readline, ''):
            if line:
                logger.info(f"Download: {line.strip()}")
        
        process.wait(timeout=900)
        
        if os.path.exists(script_path):
            os.remove(script_path)
        
        if os.path.exists(abs_destination):
            file_size = os.path.getsize(abs_destination)
            logger.info(f"✅ Download verified: {file_size / (1024*1024):.2f} MB")
            return True
        else:
            logger.error("❌ Downloaded file not found")
            return False
        
    except Exception as e:
        logger.error(f"❌ Optimized download failed: {e}")
        return False

# ======================== WATERMARK FUNCTIONS ========================
def apply_watermark_to_video(input_path, output_path, watermark_text, position, opacity):
    """Apply watermark to video using OpenCV and FFmpeg"""
    import tempfile
    import subprocess
    
    cap = cv2.VideoCapture(input_path)
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    temp_video = tempfile.mktemp(suffix='.mp4')
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))
    
    # Font settings
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = height / 1000
    font_thickness = max(1, int(height / 400))
    
    (text_width, text_height), baseline = cv2.getTextSize(
        watermark_text, font, font_scale, font_thickness
    )
    
    # Calculate position
    margin = 20
    positions_map = {
        'top-left': (margin, margin + text_height),
        'top-center': ((width - text_width) // 2, margin + text_height),
        'top-right': (width - text_width - margin, margin + text_height),
        'center-left': (margin, (height + text_height) // 2),
        'center': ((width - text_width) // 2, (height + text_height) // 2),
        'center-right': (width - text_width - margin, (height + text_height) // 2),
        'bottom-left': (margin, height - margin),
        'bottom-center': ((width - text_width) // 2, height - margin),
        'bottom-right': (width - text_width - margin, height - margin)
    }
    text_position = positions_map.get(position, positions_map['bottom-right'])
    
    alpha = opacity
    
    logger.info(f"🎨 Processing {total_frames} frames for watermark...")
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        overlay = frame.copy()
        
        # Draw black outline
        outline_thickness = font_thickness + 2
        cv2.putText(overlay, watermark_text, text_position, font, 
                   font_scale, (0, 0, 0), outline_thickness, cv2.LINE_AA)
        
        # Draw white text
        cv2.putText(overlay, watermark_text, text_position, font, 
                   font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA)
        
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        out.write(frame)
        frame_count += 1
        
        if frame_count % 100 == 0:
            logger.info(f"🎨 Processed {frame_count}/{total_frames} frames")
    
    cap.release()
    out.release()
    
    logger.info("🔊 Merging audio with watermarked video...")
    
    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', temp_video, '-i', input_path,
            '-c:v', 'copy', '-c:a', 'aac', '-map', '0:v:0', '-map', '1:a:0?',
            '-shortest', output_path
        ], check=True, capture_output=True)
        logger.info("✅ Audio merged successfully")
    except subprocess.CalledProcessError as e:
        logger.warning(f"⚠️ FFmpeg audio merge failed: {e.stderr.decode()}")
        import shutil
        shutil.copy(temp_video, output_path)
    
    if os.path.exists(temp_video):
        os.remove(temp_video)
    
    return output_path

# ======================== COMMAND HANDLERS ========================
@bot.message_handler(commands=['start'])
def handle_start(message):
    """Handle /start command"""
    user_id = message.from_user.id
    logger.info(f"👤 Start command from user {user_id}")
    
    # Check if deep link payload provided
    if len(message.text.split()) > 1:
        payload = message.text.split()[1]
        logger.info(f"🔗 User {user_id} requesting payload: {payload}")
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_id, media_type, content_protection FROM media WHERE payload=?", 
            (payload,)
        )
        result = cursor.fetchone()
        
        if result:
            file_id, media_type, content_protection = result
            protect = bool(content_protection) if content_protection is not None else True
            
            logger.info(f"📤 Sending {media_type} to user {user_id} with protection: {protect}")
            
            if media_type == 'video':
                bot.send_video(message.chat.id, file_id, protect_content=protect)
            elif media_type == 'photo':
                bot.send_photo(message.chat.id, file_id, protect_content=protect)
            
            cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.chat.id,))
            conn.commit()
        else:
            logger.warning(f"⚠️ Invalid payload requested: {payload}")
            bot.reply_to(message, "❌ Invalid or expired link")
        
        conn.close()
    else:
        # Regular start command
        if is_admin(user_id):
            logger.info(f"👑 Admin {user_id} started bot")
            bot.reply_to(message, 
                "👋 Welcome, Admin!\n\n"
                "📤 Send media to generate links/previews\n\n"
                "⚙️ Settings Commands:\n"
                "• /settings - View current settings\n"
                "• /set_preview <seconds> - Set preview length (1-10)\n"
                "• /set_collage <frames> - Set collage frames (4, 6, or 9)\n"
                "• /set_description <text> - Set bot description\n\n"
                "📁 Management Commands:\n"
                "• /list_files - List stored media\n"
                "• /delete_file <payload> - Delete media\n"
                "• /broadcast <message> - Send to all users\n"
                "• /cleanup - Clean all temp files"
            )
        else:
            logger.info(f"👤 Public user {user_id} sent start without payload")
            bot.reply_to(message, CHANNEL_MESSAGE)

@bot.message_handler(commands=['help'])
def handle_help(message):
    """Handle /help command"""
    user_id = message.from_user.id
    
    if is_admin(user_id):
        bot.reply_to(message, 
            "👋 Admin Help:\n\n"
            "📤 Send media to generate links/previews\n\n"
            "⚙️ Settings Commands:\n"
            "• /settings - View current settings\n"
            "• /set_preview <seconds> - Set preview length (1-10)\n"
            "• /set_collage <frames> - Set collage frames (4, 6, or 9)\n"
            "• /set_description <text> - Set bot description\n\n"
            "📁 Management Commands:\n"
            "• /list_files - List stored media\n"
            "• /delete_file <payload> - Delete media\n"
            "• /broadcast <message> - Send to all users\n"
            "• /cleanup - Clean all temp files"
        )
    else:
        logger.info(f"👤 Public user {user_id} sent help command")
        bot.reply_to(message, CHANNEL_MESSAGE)

@bot.message_handler(commands=['settings'])
def show_settings(message):
    """Show current bot settings"""
    if not is_admin(message.from_user.id):
        logger.info(f"⚠️ Non-admin {message.from_user.id} tried to use /settings")
        bot.reply_to(message, CHANNEL_MESSAGE)
        return
    
    logger.info(f"⚙️ Admin {message.from_user.id} viewing settings")
    
    settings_text = (
        f"⚙️ Current Bot Settings:\n\n"
        f"🎬 Preview Length: {BOT_CONFIG['preview_length']} seconds\n"
        f"🖼️ Collage Frames: {BOT_CONFIG['collage_frames']} frames\n"
        f"📊 Collage Quality: {BOT_CONFIG['collage_quality']}%\n\n"
        f"📝 Bot Description:\n{BOT_CONFIG['bot_description']}"
    )
    
    bot.reply_to(message, settings_text)

@bot.message_handler(commands=['cleanup'])
def manual_cleanup(message):
    """Manual cleanup of temporary files"""
    if not is_admin(message.from_user.id):
        logger.warning(f"⚠️ Non-admin {message.from_user.id} tried to use /cleanup")
        bot.reply_to(message, CHANNEL_MESSAGE)
        return
    
    logger.info(f"🧹 Admin {message.from_user.id} manually triggering cleanup")
    bot.reply_to(message, "🧹 Starting cleanup...")
    cleanup_files()
    bot.send_message(message.chat.id, "✅ Cleanup completed! All temporary files removed.")

@bot.message_handler(commands=['list_files'])
def list_files(message):
    """List all stored media files"""
    if not is_admin(message.from_user.id):
        logger.warning(f"⚠️ Non-admin {message.from_user.id} tried to list files")
        bot.reply_to(message, CHANNEL_MESSAGE)
        return
    
    logger.info(f"📋 Admin {message.from_user.id} listing files")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT payload, media_type FROM media")
    results = cursor.fetchall()
    conn.close()
    
    if results:
        response = "📁 Stored Media:\n\n"
        for payload, media_type in results:
            icon = "🎬" if media_type == "video" else "🖼️"
            response += f"{icon} {payload} ({media_type})\n"
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "📭 No media stored.")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    """Broadcast message to all users"""
    if not is_admin(message.from_user.id):
        logger.warning(f"⚠️ Non-admin {message.from_user.id} tried to broadcast")
        bot.reply_to(message, CHANNEL_MESSAGE)
        return
    
    if len(message.text.split()) > 1:
        broadcast_msg = ' '.join(message.text.split()[1:])
        logger.info(f"📢 Admin {message.from_user.id} broadcasting message")
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        conn.close()
        
        sent_count = 0
        failed_count = 0
        
        for (user_id,) in users:
            try:
                bot.send_message(user_id, broadcast_msg)
                sent_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to send broadcast to {user_id}: {e}")
                failed_count += 1
        
        logger.info(f"📢 Broadcast sent to {sent_count} users, {failed_count} failed")
        bot.reply_to(message, f"✅ Broadcast sent to {sent_count} users\n⚠️ {failed_count} failed")
    else:
        bot.reply_to(message, "📢 Usage: /broadcast <message>")

# ======================== MEDIA UPLOAD HANDLERS ========================
@bot.message_handler(content_types=['video', 'photo'])
def handle_media(message):
    """Handle media uploads from admins"""
    if not is_admin(message.from_user.id):
        logger.warning(f"⚠️ Non-admin {message.from_user.id} tried to upload media")
        bot.reply_to(message, CHANNEL_MESSAGE)
        return
    
    logger.info(f"📤 Admin {message.from_user.id} uploading media")
    
    media_type = 'video' if message.video else 'photo'
    file_id = message.video.file_id if message.video else message.photo[-1].file_id
    
    # Store media info temporarily
    PENDING_UPLOADS[message.from_user.id] = {
        'file_id': file_id,
        'media_type': media_type,
        'message': message,
        'chat_id': message.chat.id,
        'message_id': message.message_id,
        'generate_preview': False,
        'generate_collage': False,
        'preview_length': None,
        'collage_frames': None,
        'watermark_enabled': False,
        'watermark_text': BOT_CONFIG['watermark_text'],
        'watermark_position': BOT_CONFIG['watermark_position'],
        'watermark_opacity': BOT_CONFIG['watermark_opacity'],
        'content_protection': True,
        'setup_step': 'all_options',
    }
    
    logger.info(f"📋 Showing all options menu to user {message.from_user.id}")
    show_all_options_menu(message.chat.id, message.from_user.id, media_type)

# ======================== MENU FUNCTIONS ========================
def show_all_options_menu(chat_id, user_id, media_type='video'):
    """Show all customization options at once"""
    if user_id not in PENDING_UPLOADS:
        return
    
    settings = PENDING_UPLOADS[user_id]
    
    # Get current settings
    preview_duration = settings.get('preview_length', None)
    collage_frames = settings.get('collage_frames', None)
    watermark_enabled = settings.get('watermark_enabled', False)
    content_protection = settings.get('content_protection', False)
    
    preview_text = f"{preview_duration}s" if preview_duration else "No"
    collage_text = f"{collage_frames} frames" if collage_frames else "No"
    watermark_text = "✅ On" if watermark_enabled else "❌ Off"
    protection_text = "🔒 On" if content_protection else "🔓 Off"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Video preview options (only for videos)
    if media_type == 'video':
        markup.row(types.InlineKeyboardButton(
            f"🎬 Preview: {preview_text}", 
            callback_data="menu_set_preview"
        ))
    
    # Collage options
    markup.row(types.InlineKeyboardButton(
        f"🖼️ Collage: {collage_text}", 
        callback_data="menu_set_collage"
    ))
    
    # Watermark
    markup.row(types.InlineKeyboardButton(
        f"💧 Watermark: {watermark_text}", 
        callback_data="menu_set_watermark"
    ))
    
    # Content protection
    markup.row(types.InlineKeyboardButton(
        f"🔐 Protection: {protection_text}", 
        callback_data="menu_toggle_protection"
    ))
    
    # Generate button
    markup.row(types.InlineKeyboardButton(
        "✅ Generate Deep Link", 
        callback_data="process_now"
    ))
    
    preview_line = f"🎬 *Preview:* {preview_text}\n" if media_type == 'video' else ""
    
    text = f"""⚙️ *Quick Settings* (Default: All OFF)

{preview_line}🖼️ *Collage:* {collage_text}
💧 *Watermark:* {watermark_text}
🔐 *Protection:* {protection_text}

💡 Click to customize or Generate to proceed."""
    
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

# ======================== CALLBACK HANDLERS ========================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Handle inline button callbacks"""
    if not is_admin(call.from_user.id):
        logger.warning(f"⚠️ Non-admin {call.from_user.id} tried to use callback")
        return
    
    user_id = call.from_user.id
    
    if user_id not in PENDING_UPLOADS:
        bot.answer_callback_query(call.id, "⚠️ Upload expired. Please send media again.")
        return
    
    settings = PENDING_UPLOADS[user_id]
    media_type = settings['media_type']
    
    # Preview settings
    if call.data == "menu_set_preview":
        markup = types.InlineKeyboardMarkup(row_width=4)
        markup.row(
            types.InlineKeyboardButton("3s", callback_data="set_preview_3"),
            types.InlineKeyboardButton("5s", callback_data="set_preview_5"),
            types.InlineKeyboardButton("7s", callback_data="set_preview_7"),
            types.InlineKeyboardButton("10s", callback_data="set_preview_10")
        )
        markup.row(types.InlineKeyboardButton("❌ Disable", callback_data="set_preview_no"))
        markup.row(types.InlineKeyboardButton("« Back", callback_data="back_to_menu"))
        bot.edit_message_text(
            "🎬 Select preview duration:", 
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)
    
    elif call.data.startswith("set_preview_"):
        if call.data == "set_preview_no":
            settings['preview_length'] = None
            settings['generate_preview'] = False
            bot.answer_callback_query(call.id, "✅ Preview disabled")
        else:
            duration = int(call.data.split("_")[-1])
            settings['preview_length'] = duration
            settings['generate_preview'] = True
            bot.answer_callback_query(call.id, f"✅ Preview: {duration}s")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        show_all_options_menu(call.message.chat.id, user_id, media_type)
    
    # Collage settings
    elif call.data == "menu_set_collage":
        markup = types.InlineKeyboardMarkup(row_width=4)
        markup.row(
            types.InlineKeyboardButton("4", callback_data="set_collage_4"),
            types.InlineKeyboardButton("6", callback_data="set_collage_6"),
            types.InlineKeyboardButton("9", callback_data="set_collage_9"),
            types.InlineKeyboardButton("12", callback_data="set_collage_12")
        )
        markup.row(types.InlineKeyboardButton("❌ Disable", callback_data="set_collage_no"))
        markup.row(types.InlineKeyboardButton("« Back", callback_data="back_to_menu"))
        bot.edit_message_text(
            "🖼️ Select number of frames:", 
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)
    
    elif call.data.startswith("set_collage_"):
        if call.data == "set_collage_no":
            settings['collage_frames'] = None
            settings['generate_collage'] = False
            bot.answer_callback_query(call.id, "✅ Collage disabled")
        else:
            frames = int(call.data.split("_")[-1])
            settings['collage_frames'] = frames
            settings['generate_collage'] = True
            bot.answer_callback_query(call.id, f"✅ Collage: {frames} frames")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        show_all_options_menu(call.message.chat.id, user_id, media_type)
    
    # Watermark settings
    elif call.data == "menu_set_watermark":
        markup = types.InlineKeyboardMarkup(row_width=1)
        if settings['watermark_enabled']:
            markup.row(types.InlineKeyboardButton(
                "❌ Disable Watermark", 
                callback_data="set_watermark_off"
            ))
            markup.row(types.InlineKeyboardButton(
                "📝 Change Text", 
                callback_data="watermark_text"
            ))
            markup.row(types.InlineKeyboardButton(
                "📍 Change Position", 
                callback_data="watermark_position"
            ))
            markup.row(types.InlineKeyboardButton(
                "💧 Change Opacity", 
                callback_data="watermark_opacity"
            ))
        else:
            markup.row(types.InlineKeyboardButton(
                "✅ Enable Watermark", 
                callback_data="set_watermark_on"
            ))
        markup.row(types.InlineKeyboardButton("« Back", callback_data="back_to_menu"))
        
        wm_text = f"Current: {settings['watermark_text']}" if settings['watermark_enabled'] else "Disabled"
        bot.edit_message_text(
            f"💧 Watermark Settings\n\n{wm_text}", 
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "set_watermark_on":
        settings['watermark_enabled'] = True
        bot.answer_callback_query(call.id, "✅ Watermark enabled")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        show_all_options_menu(call.message.chat.id, user_id, media_type)
    
    elif call.data == "set_watermark_off":
        settings['watermark_enabled'] = False
        bot.answer_callback_query(call.id, "❌ Watermark disabled")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        show_all_options_menu(call.message.chat.id, user_id, media_type)
    
    elif call.data == "watermark_text":
        bot.answer_callback_query(call.id, "Send watermark text...")
        settings['waiting_for'] = 'watermark_text'
        bot.send_message(
            call.message.chat.id, 
            "📝 Send the watermark text:\n\nExample: @YourChannel or YourName\n\nSend /cancel to cancel"
        )
    
    elif call.data == "watermark_position":
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.row(
            types.InlineKeyboardButton("↖️ Top-Left", callback_data="pos_top-left"),
            types.InlineKeyboardButton("⬆️ Top-Center", callback_data="pos_top-center"),
            types.InlineKeyboardButton("↗️ Top-Right", callback_data="pos_top-right")
        )
        markup.row(
            types.InlineKeyboardButton("⬅️ Center-Left", callback_data="pos_center-left"),
            types.InlineKeyboardButton("⏺️ Center", callback_data="pos_center"),
            types.InlineKeyboardButton("➡️ Center-Right", callback_data="pos_center-right")
        )
        markup.row(
            types.InlineKeyboardButton("↙️ Bottom-Left", callback_data="pos_bottom-left"),
            types.InlineKeyboardButton("⬇️ Bottom-Center", callback_data="pos_bottom-center"),
            types.InlineKeyboardButton("↘️ Bottom-Right", callback_data="pos_bottom-right")
        )
        markup.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_menu"))
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(
                "📍 Select watermark position:", 
                call.message.chat.id, 
                call.message.message_id, 
                reply_markup=markup
            )
        except:
            pass
    
    elif call.data.startswith("pos_"):
        position = call.data.replace("pos_", "")
        settings['watermark_position'] = position
        bot.answer_callback_query(call.id, f"✅ Position: {position}")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        show_all_options_menu(call.message.chat.id, user_id, media_type)
    
    elif call.data == "watermark_opacity":
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.row(
            types.InlineKeyboardButton("10%", callback_data="opacity_0.1"),
            types.InlineKeyboardButton("25%", callback_data="opacity_0.25"),
            types.InlineKeyboardButton("50%", callback_data="opacity_0.5")
        )
        markup.row(
            types.InlineKeyboardButton("75%", callback_data="opacity_0.75"),
            types.InlineKeyboardButton("90%", callback_data="opacity_0.9"),
            types.InlineKeyboardButton("100%", callback_data="opacity_1.0")
        )
        markup.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_menu"))
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(
                "💧 Select watermark opacity:", 
                call.message.chat.id, 
                call.message.message_id, 
                reply_markup=markup
            )
        except:
            pass
    
    elif call.data.startswith("opacity_"):
        opacity = float(call.data.replace("opacity_", ""))
        settings['watermark_opacity'] = opacity
        bot.answer_callback_query(call.id, f"✅ Opacity: {int(opacity*100)}%")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        show_all_options_menu(call.message.chat.id, user_id, media_type)
    
    # Protection toggle
    elif call.data == "menu_toggle_protection":
        settings['content_protection'] = not settings['content_protection']
        status = "🔒 On" if settings['content_protection'] else "🔓 Off"
        bot.answer_callback_query(call.id, f"Protection: {status}")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        show_all_options_menu(call.message.chat.id, user_id, media_type)
    
    # Back to menu
    elif call.data == "back_to_menu":
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        show_all_options_menu(call.message.chat.id, user_id, media_type)
    
    # Process now
    elif call.data == "process_now":
        bot.answer_callback_query(call.id, "🔄 Processing...")
        
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        process_media(call.message.chat.id, user_id)
        del PENDING_UPLOADS[user_id]

# Handle watermark text input
@bot.message_handler(func=lambda msg: is_admin(msg.from_user.id) and 
                     msg.from_user.id in PENDING_UPLOADS and 
                     PENDING_UPLOADS.get(msg.from_user.id, {}).get('waiting_for') == 'watermark_text')
def handle_watermark_text(message):
    """Handle watermark text input"""
    user_id = message.from_user.id
    
    if message.text == '/cancel':
        PENDING_UPLOADS[user_id].pop('waiting_for', None)
        bot.reply_to(message, "❌ Cancelled")
        show_all_options_menu(
            message.chat.id, 
            user_id, 
            PENDING_UPLOADS[user_id]['media_type']
        )
        return
    
    PENDING_UPLOADS[user_id]['watermark_text'] = message.text
    PENDING_UPLOADS[user_id].pop('waiting_for', None)
    bot.reply_to(message, f"✅ Watermark text set to: {message.text}")
    show_all_options_menu(
        message.chat.id, 
        user_id, 
        PENDING_UPLOADS[user_id]['media_type']
    )

# ======================== MEDIA PROCESSING ========================
def process_media(chat_id, user_id):
    """Process the media and generate previews/link"""
    settings = PENDING_UPLOADS[user_id]
    file_id = settings['file_id']
    media_type = settings['media_type']
    
    # Check if processing is needed
    needs_processing = (
        settings.get('generate_preview', False) or
        settings.get('generate_collage', False) or
        settings.get('watermark_enabled', False)
    )
    
    # Instant link generation if no processing needed
    if not needs_processing:
        logger.info(f"⚡ No processing needed for user {user_id}, generating instant deep link")
        
        status_msg = bot.send_message(chat_id, "⚡ Generating instant deep link...")
        
        payload = str(uuid.uuid4())[:12].replace('-', '')
        conn = get_db()
        cursor = conn.cursor()
        protection_int = 1 if settings['content_protection'] else 0
        cursor.execute(
            "INSERT INTO media (payload, file_id, media_type, content_protection) VALUES (?, ?, ?, ?)", 
            (payload, file_id, media_type, protection_int)
        )
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Instant link generated with payload: {payload}")
        deep_link = f"https://t.me/{bot.get_me().username}?start={payload}"
        
        bot.edit_message_text(
            f"✅ Instant Deep Link Generated!\n\n"
            f"🔗 Link:\n{deep_link}\n\n"
            f"📋 Payload: `{payload}`\n\n"
            f"⚡ No download needed - instant generation!\n"
            f"🔒 Protection: {'ON' if settings['content_protection'] else 'OFF'}\n\n"
            f"💡 Users will stream directly from Telegram.",
            chat_id, 
            status_msg.message_id,
            parse_mode='Markdown'
        )
        
        del PENDING_UPLOADS[user_id]
        return
    
    # Processing needed - download and process
    logger.info(f"🔄 Processing needed for user {user_id}, downloading file...")
    status_msg = bot.send_message(chat_id, "⏳ Processing your media...")
    
    if media_type == 'video':
        try:
            logger.info("📥 Downloading video file for processing...")
            bot.edit_message_text("⏳ Downloading video for processing...", chat_id, status_msg.message_id)
            
            # Try Bot API first
            try:
                file_info = bot.get_file(file_id)
                file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
                
                parallel_success = download_file_parallel(file_url, 'temp.mp4', num_connections=8)
                
                if not parallel_success:
                    file_path = file_info.file_path
                    downloaded_file = bot.download_file(file_path)
                    with open('temp.mp4', 'wb') as f:
                        f.write(downloaded_file)
                
                logger.info("✅ Video downloaded successfully")
            
            except Exception as e:
                if "file is too big" in str(e).lower():
                    logger.info("📦 File too large for Bot API, using MTProto...")
                    bot.edit_message_text(
                        "🚀 Downloading large video...\n\n⚡ Optimized MTProto\n📥 Please wait...", 
                        chat_id, 
                        status_msg.message_id
                    )
                    
                    message_obj = settings.get('message')
                    if not message_obj:
                        raise Exception("Message object not found for large file download")
                    
                    success = download_with_pyrogram(
                        message_obj.chat.id, 
                        message_obj.message_id, 
                        'temp.mp4'
                    )
                    
                    if not success:
                        raise Exception("Failed to download large file")
                    
                    logger.info("✅ Video downloaded via MTProto")
                else:
                    raise e
            
            # Apply watermark if enabled
            watermarked_video_path = 'temp.mp4'
            if settings['watermark_enabled'] and settings['watermark_text']:
                try:
                    logger.info("🎨 Applying watermark to video...")
                    bot.edit_message_text("⏳ Applying watermark...", chat_id, status_msg.message_id)
                    
                    watermarked_video_path = apply_watermark_to_video(
                        'temp.mp4',
                        'watermarked.mp4',
                        settings['watermark_text'],
                        settings['watermark_position'],
                        settings['watermark_opacity']
                    )
                    logger.info("✅ Watermark applied successfully")
                
                except Exception as e:
                    logger.error(f"❌ Watermark failed: {str(e)}")
                    bot.send_message(chat_id, f"⚠️ Watermark failed: {str(e)}")
                    watermarked_video_path = 'temp.mp4'
            
            # Generate preview if enabled
            if settings['generate_preview']:
                generate_video_preview(
                    chat_id, 
                    status_msg, 
                    watermarked_video_path, 
                    settings['preview_length']
                )
            
            # Generate collage if enabled
            if settings['generate_collage']:
                generate_video_collage(
                    chat_id, 
                    status_msg, 
                    watermarked_video_path, 
                    settings['collage_frames']
                )
        
        except Exception as e:
            logger.error(f"❌ Video processing error: {str(e)}")
            bot.edit_message_text(
                f"❌ Error processing video:\n\n{str(e)}\n\nGenerating link anyway...", 
                chat_id, 
                status_msg.message_id
            )
        
        finally:
            cleanup_files()
    
    # Generate deep link
    logger.info("🔗 Generating deep link...")
    bot.edit_message_text("⏳ Generating deep link...", chat_id, status_msg.message_id)
    
    payload = str(uuid.uuid4())[:12].replace('-', '')
    conn = get_db()
    cursor = conn.cursor()
    protection_int = 1 if settings['content_protection'] else 0
    cursor.execute(
        "INSERT INTO media (payload, file_id, media_type, content_protection) VALUES (?, ?, ?, ?)", 
        (payload, file_id, media_type, protection_int)
    )
    conn.commit()
    conn.close()
    
    logger.info(f"✅ Media saved with payload: {payload}")
    deep_link = f"https://t.me/{bot.get_me().username}?start={payload}"
    
    bot.edit_message_text(
        f"✅ Done!\n\n"
        f"🔗 Deep link:\n{deep_link}\n\n"
        f"📋 Payload: `{payload}`\n\n"
        f"Paste the link in your ad site.",
        chat_id, 
        status_msg.message_id,
        parse_mode='Markdown'
    )
    
    logger.info(f"🎉 Deep link generated: {deep_link}")

def generate_video_preview(chat_id, status_msg, source_video, preview_length):
    """Generate video preview with random clips"""
    try:
        logger.info(f"🎬 Generating {preview_length}s preview...")
        bot.edit_message_text(
            f"⏳ Generating {preview_length}s preview...", 
            chat_id, 
            status_msg.message_id
        )
        
        import subprocess
        import tempfile
        
        # Get video duration
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', source_video
        ], capture_output=True, text=True)
        
        video_duration = float(result.stdout.strip())
        logger.info(f"📊 Video duration: {video_duration}s")
        
        if video_duration <= preview_length:
            import shutil
            shutil.copy(source_video, 'preview.mp4')
            logger.info("📋 Video shorter than preview, copied entire video")
        else:
            # Generate random clips
            clip_duration = 2
            num_clips = int(preview_length / clip_duration)
            available_duration = video_duration - clip_duration
            random_starts = sorted([random.uniform(0, available_duration) for _ in range(num_clips)])
            
            logger.info(f"🎲 Extracting {num_clips} clips at: {[f'{t:.2f}s' for t in random_starts]}")
            
            temp_clips = []
            concat_file = tempfile.mktemp(suffix='.txt')
            
            for i, start_time in enumerate(random_starts):
                temp_clip = f'temp_clip_{i}.mp4'
                temp_clips.append(temp_clip)
                
                subprocess.run([
                    'ffmpeg', '-y', '-ss', str(start_time), '-i', source_video,
                    '-t', str(clip_duration), 
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                    '-c:a', 'aac', '-b:a', '128k',
                    temp_clip
                ], capture_output=True, text=True, check=True)
                
                logger.info(f"✂️ Extracted clip {i+1}/{num_clips}")
            
            # Create concat file
            with open(concat_file, 'w') as f:
                for clip in temp_clips:
                    f.write(f"file '{os.path.abspath(clip)}'\n")
            
            logger.info(f"🔗 Concatenating {len(temp_clips)} clips...")
            
            # Concatenate clips
            subprocess.run([
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_file,
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                '-c:a', 'aac', '-b:a', '128k',
                'preview.mp4'
            ], capture_output=True, text=True, check=True)
            
            logger.info("✅ Preview concatenated successfully")
            
            # Cleanup
            for temp_clip in temp_clips:
                if os.path.exists(temp_clip):
                    os.remove(temp_clip)
            if os.path.exists(concat_file):
                os.remove(concat_file)
        
        # Send preview
        with open('preview.mp4', 'rb') as prev:
            bot.send_video(
                chat_id, 
                prev, 
                caption=f"🎬 {preview_length}s preview (random clips)"
            )
        
        logger.info("✅ Preview sent successfully")
        
        if os.path.exists('preview.mp4'):
            os.remove('preview.mp4')
    
    except Exception as e:
        logger.error(f"❌ Preview generation failed: {str(e)}")
        bot.send_message(chat_id, f"⚠️ Preview generation failed: {str(e)}")

def generate_video_collage(chat_id, status_msg, source_video, collage_frames):
    """Generate collage from video frames"""
    try:
        logger.info(f"🖼️ Generating {collage_frames}-frame collage...")
        bot.edit_message_text(
            f"⏳ Generating {collage_frames}-frame collage...", 
            chat_id, 
            status_msg.message_id
        )
        
        import subprocess
        
        # Get video duration
        duration_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                       '-of', 'default=noprint_wrappers=1:nokey=1', source_video]
        duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
        
        try:
            video_duration = float(duration_result.stdout.strip())
        except:
            video_duration = 60
        
        logger.info(f"📊 Video duration: {video_duration:.2f}s, extracting {collage_frames} frames")
        
        # Generate random timestamps
        if video_duration < 1:
            random_times = [0.5]
            collage_frames = 1
        elif video_duration < collage_frames:
            actual_frames = max(1, int(video_duration))
            collage_frames = actual_frames
            random_times = [video_duration * (i + 0.5) / actual_frames for i in range(actual_frames)]
        elif video_duration > 10:
            safe_duration = video_duration - 10
            random_times = sorted([5 + random.random() * safe_duration for _ in range(collage_frames)])
        else:
            margin = video_duration * 0.1
            safe_duration = video_duration - (2 * margin)
            random_times = sorted([margin + random.random() * safe_duration for _ in range(collage_frames)])
        
        logger.info(f"🎲 Timestamps: {[f'{t:.2f}s' for t in random_times]}")
        
        # Extract frames
        frames = []
        for idx, timestamp in enumerate(random_times):
            frame_file = f'frame_{idx}.jpg'
            
            extract_cmd = [
                'ffmpeg', '-ss', str(timestamp),
                '-i', source_video,
                '-vframes', '1',
                '-q:v', '2',
                '-y', frame_file
            ]
            
            result = subprocess.run(extract_cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(frame_file):
                try:
                    frame_img = Image.open(frame_file)
                    frames.append(frame_img)
                    logger.debug(f"✅ Extracted frame {idx+1}/{collage_frames}")
                except Exception as e:
                    logger.error(f"❌ Failed to load frame {idx}: {e}")
                finally:
                    if os.path.exists(frame_file):
                        os.remove(frame_file)
            else:
                logger.error(f"❌ Frame extraction failed at {timestamp:.2f}s")
        
        if len(frames) >= collage_frames:
            logger.info(f"✅ Extracted {len(frames)} frames successfully")
            
            # Resize frames
            target_width = 640
            target_height = 480
            frames_resized = []
            for frame in frames:
                frame_resized = frame.resize((target_width, target_height), Image.Resampling.LANCZOS)
                frames_resized.append(frame_resized)
            
            # Create collage grid
            if collage_frames == 4:
                grid_cols, grid_rows = 2, 2
            elif collage_frames == 6:
                grid_cols, grid_rows = 3, 2
            elif collage_frames == 9:
                grid_cols, grid_rows = 3, 3
            elif collage_frames == 12:
                grid_cols, grid_rows = 4, 3
            else:
                grid_cols, grid_rows = 2, 2
            
            collage_width = target_width * grid_cols
            collage_height = target_height * grid_rows
            collage = Image.new('RGB', (collage_width, collage_height), (0, 0, 0))
            
            for idx, frame in enumerate(frames_resized[:collage_frames]):
                row = idx // grid_cols
                col = idx % grid_cols
                x = col * target_width
                y = row * target_height
                collage.paste(frame, (x, y))
            
            collage.save('collage.jpg', quality=BOT_CONFIG['collage_quality'])
            
            # Send collage
            with open('collage.jpg', 'rb') as coll:
                bot.send_photo(
                    chat_id, 
                    coll, 
                    caption=f"🖼️ {collage_frames}-frame collage (random shots)"
                )
            
            logger.info("✅ Collage sent successfully")
            
            if os.path.exists('collage.jpg'):
                os.remove('collage.jpg')
        else:
            logger.warning(f"⚠️ Not enough frames: {len(frames)}/{collage_frames}")
            bot.send_message(chat_id, f"⚠️ Only extracted {len(frames)} frames, skipping collage")
    
    except Exception as e:
        logger.error(f"❌ Collage generation failed: {str(e)}")

# ======================== OTHER MESSAGE HANDLERS ========================
@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    """Handle all other messages"""
    if not is_admin(message.from_user.id):
        logger.info(f"👤 Non-admin {message.from_user.id} sent message")
        bot.reply_to(message, CHANNEL_MESSAGE)
    else:
        logger.info(f"⚠️ Unknown command from admin {message.from_user.id}: {message.text}")
        bot.reply_to(message, "❓ Unknown command. Type /start to see available commands.")

# ======================== MAIN EXECUTION ========================
if __name__ == "__main__":
    # Initialize database
    init_database()
    
    # Load configuration
    load_config()
    
    # Clean up old files
    logger.info("🧹 Cleaning up old temporary files...")
    cleanup_files()
    
    # Log bot info
    logger.info("=" * 60)
    logger.info("🤖 Telegram Media Deep Link Bot")
    logger.info("👨‍💻 Author: Miyuru Dilakshan")
    logger.info("🌐 Website: miyuru.dev")
    logger.info("=" * 60)
    logger.info(f"✅ Bot username: @{bot.get_me().username}")
    logger.info(f"👑 Admins: {ADMINS}")
    logger.info("🚀 Bot is ready! Press Ctrl+C to stop.")
    logger.info("=" * 60)
    
    try:
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        logger.info("\n⏹️ Bot stopped by user")
        logger.info("🧹 Final cleanup...")
        cleanup_files()
        logger.info("👋 Goodbye!")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
        logger.info("🧹 Crash cleanup...")
        cleanup_files()
