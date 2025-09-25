import os
import uuid
import string
import random
import logging
import requests
import sqlite3
from threading import Thread
from datetime import datetime
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
CHANNEL_LINK = "https://t.me/Aniredirect"
BACKUP_CHANNEL_LINK = "https://t.me/ScammerFuk"
ADMIN_IDS = [6302016869]  # Replce with your admin user ID(s)
DATABASE_NAME = "bot_users.db"

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable not set!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
# Initialize database with enhanced tables
def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Users table (unchanged)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            date_added TEXT
        )
    ''')
    
    # New table for tracking usage statistics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            command_used TEXT,
            target TEXT,
            timestamp TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    
    # New table for persistent counters
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS persistent_stats (
            stat_name TEXT PRIMARY KEY,
            stat_value INTEGER
        )
    ''')
    
    # Initialize persistent stats if not exists
    cursor.execute('''
        INSERT OR IGNORE INTO persistent_stats (stat_name, stat_value)
        VALUES ('total_resets', 0)
    ''')
    
    cursor.execute('''
        INSERT OR IGNORE INTO persistent_stats (stat_name, stat_value)
        VALUES ('total_bulk_operations', 0)
    ''')
    
    conn.commit()
    conn.close()

init_db()

# Instagram Password Reset Logic (unchanged)
class PasswordReset:
    def __init__(self, target):
        self.target = target.strip()
        self.data = {
            "_csrftoken": "".join(random.choices(string.ascii_letters + string.digits, k=32)),
            "guid": str(uuid.uuid4()),
            "device_id": str(uuid.uuid4())
        }
        if "@" in self.target:
            self.data["user_email"] = self.target
        else:
            self.data["username"] = self.target

    def send_password_reset(self):
        try:
            r = requests.post(
                "https://i.instagram.com/api/v1/accounts/send_password_reset/",
                headers={"user-agent": "Instagram 150.0.0.0.000 Android"},
                data=self.data,
                timeout=10
            )
            return r.text
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return "error"

# Store new user in database (unchanged)
def store_user(user):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, date_added)
        VALUES (?, ?, ?, ?, datetime('now'))
    ''', (user.id, user.username, user.first_name, user.last_name))
    conn.commit()
    conn.close()

# Get total user count (unchanged)
def get_user_count():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# Track command usage in database
def track_usage(user_id, command, target=None):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Record the usage
    cursor.execute('''
        INSERT INTO usage_stats (user_id, command_used, target, timestamp)
        VALUES (?, ?, ?, datetime('now'))
    ''', (user_id, command, target))
    
    # Update persistent counters for certain commands
    if command == '/reset':
        cursor.execute('''
            UPDATE persistent_stats SET stat_value = stat_value + 1 
            WHERE stat_name = 'total_resets'
        ''')
    elif command == '/bulk':
        cursor.execute('''
            UPDATE persistent_stats SET stat_value = stat_value + 1 
            WHERE stat_name = 'total_bulk_operations'
        ''')
    
    conn.commit()
    conn.close()

# Get persistent stat value
def get_persistent_stat(stat_name):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT stat_value FROM persistent_stats WHERE stat_name = ?
    ''', (stat_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

# Start Command (unchanged)
@bot.message_handler(commands=['start'])
def start(message):
    store_user(message.from_user)
    
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("📢 Main Channel", url=CHANNEL_LINK))
    keyboard.row(InlineKeyboardButton("🔄 Backup Channel", url=BACKUP_CHANNEL_LINK))
    keyboard.row(InlineKeyboardButton("✅ I've Joined", callback_data='joined'))
    
    text = (
        f"👋 Welcome *{message.from_user.first_name}*!\n\n"
        "🔹 Join our main or backup channel.\n"
        "🔹 Then click *I've Joined*."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=keyboard)

# Button Handler (unchanged)
@bot.callback_query_handler(func=lambda call: True)
def button_handler(call):
    if call.data == "joined":
        bot.edit_message_text(
            "🎉 Thanks for joining! Use /help for commands.",
            call.message.chat.id,
            call.message.message_id
        )

# Help Command (unchanged)
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message,
        "🔹 *Available Commands* 🔹\n\n"
        "/start - Start bot\n/reset - Reset one account\n/bulk - Reset multiple accounts",
        parse_mode="Markdown"
    )

# Reset Command (modified to track usage)
@bot.message_handler(commands=['reset'])
def reset_command(message):
    store_user(message.from_user)
    track_usage(message.from_user.id, '/reset')
    msg = bot.reply_to(message, "Send Instagram username or email")
    bot.register_next_step_handler(msg, process_reset_step)

def process_reset_step(message):
    target = message.text
    if target.startswith('@'):
        bot.reply_to(message, "❌ Username without '@'")
        return
    
    result = PasswordReset(target).send_password_reset()
    if "obfuscated_email" in result:
        track_usage(message.from_user.id, '/reset_success', target)
        bot.reply_to(message, "✅ Reset link sent!")
    else:
        track_usage(message.from_user.id, '/reset_failed', target)
        bot.reply_to(message, "❌ Failed to send link")

# Bulk Command (modified to track usage)
@bot.message_handler(commands=['bulk'])
def bulk_command(message):
    store_user(message.from_user)
    track_usage(message.from_user.id, '/bulk')
    msg = bot.reply_to(message, "Send multiple usernames/emails (one per line)")
    bot.register_next_step_handler(msg, process_bulk_step)

def process_bulk_step(message):
    targets = [t.strip() for t in message.text.split("\n") if t.strip()]
    bot.reply_to(message, f"⏳ Processing {len(targets)} accounts...")
    
    success_count = 0
    for t in targets:
        if not t.startswith('@'):
            result = PasswordReset(t).send_password_reset()
            if "obfuscated_email" in result:
                success_count += 1
                track_usage(message.from_user.id, '/bulk_success', t)
            else:
                track_usage(message.from_user.id, '/bulk_failed', t)
    
    track_usage(message.from_user.id, '/bulk_completed', f"processed {len(targets)} accounts")
    bot.reply_to(message, f"✅ Bulk processing completed\nSuccess: {success_count}\nFailed: {len(targets) - success_count}")

# Enhanced Admin: Stats Command
@bot.message_handler(commands=['stats'])
def stats_command(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Access denied")
        return
    
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Get total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    # Get active users (used commands)
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM usage_stats")
    active_users = cursor.fetchone()[0]
    
    # Get total reset operations
    total_resets = get_persistent_stat('total_resets')
    
    # Get total bulk operations
    total_bulk = get_persistent_stat('total_bulk_operations')
    
    # Get recent activity
    cursor.execute('''
        SELECT command_used, COUNT(*) as count 
        FROM usage_stats 
        WHERE timestamp > datetime('now', '-1 day')
        GROUP BY command_used
    ''')
    daily_activity = cursor.fetchall()
    
    conn.close()
    
    # Format stats message
    stats_text = f"""
📊 *Bot Statistics* 📊

👥 *Users:*
- Total: {total_users}
- Active: {active_users}

⚙️ *Operations:*
- Total resets: {total_resets}
- Total bulk operations: {total_bulk}

📈 *Last 24h Activity:*
"""
    for command, count in daily_activity:
        stats_text += f"- {command}: {count}\n"
    
    bot.reply_to(message, stats_text, parse_mode="Markdown")

# Admin: Broadcast Command (unchanged)
@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Access denied")
        return
    
    msg = bot.reply_to(message, "Send the message you want to broadcast to all users")
    bot.register_next_step_handler(msg, process_broadcast_step)

def process_broadcast_step(message):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    
    total = len(users)
    success = 0
    failed = 0
    
    bot.reply_to(message, f"📢 Broadcasting to {total} users...")
    
    for user in users:
        try:
            bot.copy_message(user[0], message.chat.id, message.message_id)
            success += 1
        except Exception as e:
            logger.error(f"Failed to send to {user[0]}: {e}")
            failed += 1
    
    bot.reply_to(message, f"📢 Broadcast completed!\nSuccess: {success}\nFailed: {failed}")

# Handle other messages (unchanged)
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.reply_to(message, "Use /help for commands")

# Flask App for keep-alive (unchanged)
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Bot is running!"

def run_flask():
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    # Start Flask in a separate thread
    Thread(target=run_flask).start()
    
    # Start the bot
    logger.info("Starting bot...")
    bot.infinity_polling()
