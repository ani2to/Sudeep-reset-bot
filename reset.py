import os
import uuid
import random
import logging
import requests
import sqlite3
import time
import threading
from threading import Thread
from datetime import datetime
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable not set!")
    exit(1)

# Configuration
CHANNEL_LINK = "https://t.me/Aniredirect"
BOT_REDIRECT_LINK = "https://t.me/SPBotz"
ADMIN_IDS = [6302016869]
DATABASE_NAME = "bot_users.db"

bot = telebot.TeleBot(BOT_TOKEN)

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Check if users table exists and has the correct structure
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Create users table if it doesn't exist or add missing columns
    if 'users' not in [table[0] for table in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
        cursor.execute('''
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                date_added TEXT
            )
        ''')
    else:
        # Add missing columns if they don't exist
        if 'date_added' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN date_added TEXT')
    
    # Create usage_stats table if it doesn't exist
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
    
    # Create persistent_stats table if it doesn't exist
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

class PasswordReset:
    def __init__(self, target):
        self.target = target.strip()
        self.start_time = time.time()
        # List of free proxies (replace with your own or use a paid proxy service)
        self.proxies = [
            {"http": "http://195.154.222.103:5836", "https": "https://195.154.222.103:5836"},
            {"http": "http://45.95.147.106:8080", "https": "https://45.95.147.106:8080"},
            {"http": "http://45.136.21.678:8080", "https": "https://45.136.21.678:8080"},
            # Add more proxies as needed
        ]
        
    def send_password_reset(self):
        try:
            # Select a random proxy
            proxy = random.choice(self.proxies) if self.proxies else None
            
            url = "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/"
            
            # Updated headers and cookies from RESET.py
            cookies = {
                'csrftoken': 'umwHlWf6r3AGDowkZQb47m',
                'datr': '_D1dZ0DhNw8dpOJHN-59ONZI',
                'ig_did': 'C0CBB4B6-FF17-4C4A-BB83-F3879B996720',
                'mid': 'Z109_AALAAGxFePISIe2H_ZcGwTD',
                'wd': '1157x959'
            }
            
            headers = {
                "authority": "www.instagram.com",
                "method": "POST",
                "scheme": "https",
                "accept": "*/*",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "en-US,en;q=0.7",
                "content-type": "application/x-www-form-urlencoded",
                "origin": "https://www.instagram.com",
                "referer": "https://www.instagram.com/accounts/password/reset/?source=fxcal&hl=en",
                "sec-ch-ua": '"Brave";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                "sec-ch-ua-full-version-list": '"Brave";v="131.0.0.0", "Chromium";v="131.0.0.0", "Not_A Brand";v="24.0.0.0"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-model": '""',
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua-platform-version": '"10.0.0"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "sec-gpc": "1",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "x-asbd-id": "129477",
                "x-csrftoken": "umwHlWf6r3AGDowkZQb47m",
                "x-ig-app-id": "936619743392459",
                "x-ig-www-claim": "0",
                "x-instagram-ajax": "1018880011",
                "x-requested-with": "XMLHttpRequest",
                "x-web-session-id": "ag36cv:1ko17s:9bxl9b"
            }

            data = {
                "email_or_username": self.target,
                "flow": "fxcal"
            }

            session = requests.Session()
            # Set cookies from RESET.py
            session.cookies.update(cookies)
            
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            if proxy:
                response = session.post(url, headers=headers, data=data, timeout=8, proxies=proxy)
            else:
                response = session.post(url, headers=headers, data=data, timeout=8)
                
            end_time = time.time()
            self.time_taken = round(end_time - self.start_time, 2)
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("status") == "ok":
                    obfuscated_email = response_data.get("obfuscated_email", "")
                    return {
                        "success": True,
                        "email": obfuscated_email,
                        "time_taken": self.time_taken
                    }
                else:
                    error_type = response_data.get("error_type", "")
                    if error_type == "rate_limit_error":
                        error_msg = "Rate limited. Try using VPN or try again later."
                    else:
                        error_msg = response_data.get("message", "Unknown error")
                    
                    return {
                        "success": False,
                        "error": error_msg,
                        "time_taken": self.time_taken
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP Error: {response.status_code}",
                    "time_taken": self.time_taken
                }
                
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "time_taken": round(end_time - self.start_time, 2)
            }

# Store new user in database with error handling
def store_user(user):
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user.id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # Update existing user
            cursor.execute('''
                UPDATE users 
                SET username = ?, first_name = ?, last_name = ?
                WHERE user_id = ?
            ''', (user.username, user.first_name, user.last_name, user.id))
        else:
            # Insert new user
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, date_added)
                VALUES (?, ?, ?, ?, datetime('now'))
            ''', (user.id, user.username, user.first_name, user.last_name))
            
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Database error in store_user: {e}")
        # Try to recreate the table if there's a schema issue
        if "no such column" in str(e):
            init_db()
            store_user(user)  # Retry

# Get total user count
def get_user_count():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# Track command usage in database
def track_usage(user_id, command, target=None):
    try:
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
    except sqlite3.Error as e:
        logger.error(f"Database error in track_usage: {e}")

# Get persistent stat value
def get_persistent_stat(stat_name):
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT stat_value FROM persistent_stats WHERE stat_name = ?
        ''', (stat_name,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0
    except sqlite3.Error as e:
        logger.error(f"Database error in get_persistent_stat: {e}")
        return 0

# Safe function to send messages with error handling
def safe_send_message(chat_id, text, reply_markup=None, parse_mode=None, reply_to_message_id=None):
    try:
        if reply_to_message_id:
            return bot.send_message(chat_id, text, reply_markup=reply_markup, 
                                   parse_mode=parse_mode, reply_to_message_id=reply_to_message_id)
        else:
            return bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        # Try without reply if that was the issue
        if "message to be replied not found" in str(e):
            return bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
        return None

# Check if user is a member of required channels
def check_membership(user_id):
    try:
        # Check main channel
        try:
            main_chat_member = bot.get_chat_member("@Aniredirect", user_id)
            if main_chat_member.status not in ['member', 'administrator', 'creator']:
                return False
        except telebot.apihelper.ApiTelegramException as e:
            if "bot was kicked" in str(e) or "CHAT_NOT_FOUND" in str(e):
                # If bot can't access the channel, skip this check
                logger.warning(f"Bot cannot access main channel: {e}")
                # Return True to allow users to continue without channel check
                return True
            raise e
            
        # Check bot redirect channel
        try:
            backup_chat_member = bot.get_chat_member("@ScammerFuk", user_id)
            if backup_chat_member.status not in ['member', 'administrator', 'creator']:
                return False
        except telebot.apihelper.ApiTelegramException as e:
            if "bot was kicked" in str(e) or "CHAT_NOT_FOUND" in str(e):
                # If bot can't access the channel, skip this check
                logger.warning(f"Bot cannot access backup channel: {e}")
                # Return True to allow users to continue without channel check
                return True
            raise e
            
        return True
    except Exception as e:
        logger.error(f"Error checking membership: {e}")
        # Allow access on error to prevent bot from breaking
        return True

# Loading animation function
def update_loading_message(bot, chat_id, message_id, progress, total, current_item=None):
    percentage = int((progress / total) * 100)
    bars = int(percentage / 5)  # 20 bars total
    loading_bar = "[" + "█" * bars + "░" * (20 - bars) + "]"
    
    if current_item:
        text = f"🔄 Processing... {loading_bar} {percentage}%\n\n📋 Current: {current_item}\n📊 Progress: {progress}/{total}"
    else:
        text = f"🔄 Processing your request... {loading_bar} {percentage}%"
    
    try:
        bot.edit_message_text(text, chat_id, message_id)
    except:
        pass  # Ignore message not modified errors

# Start Command with improved design
@bot.message_handler(commands=['start'])
def start(message):
    store_user(message.from_user)
    
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("📢 Main Channel", url=CHANNEL_LINK))
    keyboard.row(InlineKeyboardButton("🤖 Bot Redirect", url=BOT_REDIRECT_LINK))
    keyboard.row(InlineKeyboardButton("✅ I've Joined", callback_data='joined'))
    
    text = (
        f"✨ *Welcome {message.from_user.first_name}!* ✨\n\n"
        "🔐 *Instagram Pass Reset Bot*\n\n"
        "📋 *How to use:*\n"
        "1. Join our channels below\n"
        "2. Click 'I've Joined' to verify\n"
        "3. Use /help commands\n\n"
        "⚡ Fast & Efficient Pass Reset Bot"
    )
    safe_send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=keyboard)

# Button Handler
@bot.callback_query_handler(func=lambda call: True)
def button_handler(call):
    if call.data == "joined":
        if check_membership(call.from_user.id):
            try:
                bot.edit_message_text(
                    "✅ *Verification Successful!*\n\n"
                    "You can now use all bot features:\n"
                    "• /reset - Reset single account\n"
                    "• /bulk - Reset multiple accounts\n"
                    "• /help - Show all commands/uses",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="Markdown"
                )
            except:
                # If message editing fails, send a new message
                safe_send_message(
                    call.message.chat.id,
                    "✅ *Verification Successful!*\n\nYou can now use all bot features!",
                    parse_mode="Markdown"
                )
        else:
            try:
                bot.answer_callback_query(
                    call.id,
                    "❌ Please join both channels first!",
                    show_alert=True
                )
            except:
                pass  # Ignore callback errors

# Improved Help Command
@bot.message_handler(commands=['help'])
def help_command(message):
    if not check_membership(message.from_user.id):
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("📢 Main Channel", url=CHANNEL_LINK))
        keyboard.row(InlineKeyboardButton("🤖 Bot Redirect", url=BOT_REDIRECT_LINK))
        safe_send_message(message.chat.id, "❌ Please join our channels first to use this bot!", reply_markup=keyboard)
        return
        
    help_text = """
🔧 *Instagram Reset Bot - Help* 🔧

*Available Commands:*
🔹 /start - Initialize the bot
🔹 /reset - Reset password for single account
🔹 /bulk - Reset multiple accounts at once
🔹 /help - Show this help message

*Usage Instructions:*
📝 For single account: /reset then send username/email
📝 For multiple accounts: /bulk then send list (one per line)

*Note:* 
• Usernames should be without @ symbol
• Use responsibly and ethically

*Developer:* [#𝐒𝐔𝐃𝐄𝐄𝐏</>](tg://user?id=6302016869)
"""
    safe_send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['reset'])
def reset_command(message):
    if not check_membership(message.from_user.id):
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("📢 Main Channel", url=CHANNEL_LINK))
        keyboard.row(InlineKeyboardButton("🤖 Bot Redirect", url=BOT_REDIRECT_LINK))
        safe_send_message(message.chat.id, "❌ Please join our channels first to use this bot!", reply_markup=keyboard)
        return
        
    store_user(message.from_user)
    track_usage(message.from_user.id, '/reset')
    msg = safe_send_message(message.chat.id, "📩 Send Instagram username or email:")
    if msg:
        bot.register_next_step_handler(msg, process_reset_step)

def process_reset_step(message):
    target = message.text.strip()
    if target.startswith('@'):
        target = target[1:]
    
    # Show processing message with loading animation
    processing_msg = safe_send_message(message.chat.id, "🔄 Processing your request... [░░░░░░░░░░░░░░░░░░░░] 0%")
    
    if not processing_msg:
        # If we couldn't send the processing message, just proceed
        result = PasswordReset(target).send_password_reset()
        send_reset_result(message, result, target)
        return
    
    # Start a thread to update the loading animation
    stop_loading = threading.Event()
    
    def loading_animation():
        progress = 0
        while not stop_loading.is_set() and progress < 95:
            progress += random.randint(5, 15)
            if progress > 95:
                progress = 95
            update_loading_message(bot, message.chat.id, processing_msg.message_id, progress, 100)
            time.sleep(0.3)
    
    loading_thread = threading.Thread(target=loading_animation)
    loading_thread.start()
    
    # Send reset request
    result = PasswordReset(target).send_password_reset()
    
    # Stop the loading animation
    stop_loading.set()
    loading_thread.join()
    
    send_reset_result(message, result, target, processing_msg.message_id)

def send_reset_result(message, result, target, message_id=None):
    if result["success"]:
        track_usage(message.from_user.id, '/reset_success', target)
        
        # Format the success response
        response_text = f"""```json
🔐 Instagram Reset By @Sudeephu

👤 Username - {target}
📧 Mail - {result['email']}
⏱️ Time taken : {result['time_taken']}s

✅ Reset sent successfully```
        
Dev: [#𝐒𝐔𝐃𝐄𝐄𝐏</>](tg://user?id=6302016869)"""
        
        if message_id:
            try:
                bot.edit_message_text(
                    response_text,
                    message.chat.id,
                    message_id,
                    parse_mode="Markdown"
                )
            except:
                safe_send_message(message.chat.id, response_text, parse_mode="Markdown")
        else:
            safe_send_message(message.chat.id, response_text, parse_mode="Markdown")
    else:
        track_usage(message.from_user.id, '/reset_failed', target)
        
        # Format the error response
        error_msg = result["error"]
        if "429" in error_msg or "rate limit" in error_msg.lower():
            error_msg = "Instagram is rate limiting our requests. Please:\n1. Wait a few minutes\n2. Try using a VPN\n3. Try again later"
        elif "user" in error_msg.lower():
            error_msg = "Invalid username or email"
        elif "account" in error_msg.lower():
            error_msg = "Account not found"
        
        response_text = f"""```json
🔐 Instagram Reset By @Sudeephu

❌ {error_msg}

Status: Failed```
        
Dev: [#𝐒𝐔𝐃𝐄𝐄𝐏</>](tg://user?id=6302016869)"""
        
        if message_id:
            try:
                bot.edit_message_text(
                    response_text,
                    message.chat.id,
                    message_id,
                    parse_mode="Markdown"
                )
            except:
                safe_send_message(message.chat.id, response_text, parse_mode="Markdown")
        else:
            safe_send_message(message.chat.id, response_text, parse_mode="Markdown")

# Bulk Command with improved interface
@bot.message_handler(commands=['bulk'])
def bulk_command(message):
    if not check_membership(message.from_user.id):
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("📢 Main Channel", url=CHANNEL_LINK))
        keyboard.row(InlineKeyboardButton("🤖 Bot Redirect", url=BOT_REDIRECT_LINK))
        safe_send_message(message.chat.id, "❌ Please join our channels first to use this bot!", reply_markup=keyboard)
        return
        
    store_user(message.from_user)
    track_usage(message.from_user.id, '/bulk')
    msg = safe_send_message(message.chat.id, "📨 Send multiple usernames/emails (one per line):")
    if msg:
        bot.register_next_step_handler(msg, process_bulk_step)

def process_bulk_step(message):
    targets = [t.strip() for t in message.text.split("\n") if t.strip()]
    targets = [t[1:] if t.startswith('@') else t for t in targets]
    
    processing_msg = safe_send_message(message.chat.id, f"🔄 Processing {len(targets)} accounts... [░░░░░░░░░░░░░░░░░░░░] 0%")
    
    success_count = 0
    failed_count = 0
    failed_targets = []
    start_time = time.time()
    
    for i, target in enumerate(targets):
        try:
            if processing_msg:
                update_loading_message(bot, message.chat.id, processing_msg.message_id, i+1, len(targets), target)
            
            result = PasswordReset(target).send_password_reset()
            if result["success"]:
                success_count += 1
                track_usage(message.from_user.id, '/bulk_success', target)
            else:
                failed_count += 1
                failed_targets.append(f"❌ {target} - {result.get('error', 'Unknown error')}")
                track_usage(message.from_user.id, '/bulk_failed', target)
                
        except Exception as e:
            failed_count += 1
            failed_targets.append(f"❌ {target} - Error: {str(e)}")
            logger.error(f"Error processing {target}: {e}")
    
    total_time = round(time.time() - start_time, 2)
    track_usage(message.from_user.id, '/bulk_completed', f"processed {len(targets)} accounts")
    
    if success_count > 0:
        response_text = f"""```json
🔐 Instagram Reset By @Sudeephu

📊 Bulk Processing Complete

✅ Successful: {success_count}
❌ Failed: {failed_count}
⏱️ Time taken: {total_time}s

✅ Done```
        
"""
        
        if failed_targets:
            response_text += "\n*Failed Accounts:*\n"
            
            for failed in failed_targets[:5]:
                response_text += f"{failed}\n"
            if len(failed_targets) > 5:
                response_text += f"... and {len(failed_targets) - 5} more\n"
        
        response_text += "\nDev: [#𝐒𝐔𝐃𝐄𝐄𝐏</>](tg://user?id=6302016869)"
        
    else:
        response_text = f"""```json
🔐 Instagram Reset By @Sudeephu

📊 Bulk Processing Complete

❌ All requests failed
Possible reasons: 
- Invalid targets provided
- Instagram server issues
- Rate limiting

⏱️ Time taken: {total_time}s

❌ Failed```
        
Dev: [#𝐒𝐔𝐃𝐄𝐄𝐏</>](tg://user?id=6302016869)"""
    
    if processing_msg:
        try:
            bot.edit_message_text(
                response_text,
                message.chat.id,
                processing_msg.message_id,
                parse_mode="Markdown"
            )
        except:
            safe_send_message(message.chat.id, response_text, parse_mode="Markdown")
    else:
        safe_send_message(message.chat.id, response_text, parse_mode="Markdown")


@bot.message_handler(commands=['stats'])
def stats_command(message):
    if message.from_user.id not in ADMIN_IDS:
        safe_send_message(message.chat.id, "❌ Access denied")
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
    
    safe_send_message(message.chat.id, stats_text, parse_mode="Markdown")

# Admin: Broadcast Command
@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if message.from_user.id not in ADMIN_IDS:
        safe_send_message(message.chat.id, "❌ Access denied")
        return
    
    msg = safe_send_message(message.chat.id, "Send the message you want to broadcast to all users")
    if msg:
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
    
    safe_send_message(message.chat.id, f"📢 Broadcasting to {total} users...")
    
    for user in users:
        try:
            bot.copy_message(user[0], message.chat.id, message.message_id)
            success += 1
        except Exception as e:
            logger.error(f"Failed to send to {user[0]}: {e}")
            failed += 1
    
    safe_send_message(message.chat.id, f"📢 Broadcast completed!\nSuccess: {success}\nFailed: {failed}")

# Handle other messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not check_membership(message.from_user.id):
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("📢 Main Channel", url=CHANNEL_LINK))
        keyboard.row(InlineKeyboardButton("🤖 Bot Redirect", url=BOT_REDIRECT_LINK))
        safe_send_message(message.chat.id, "❌ Please join our channels first to use this bot!", reply_markup=keyboard)
        return
        
    safe_send_message(message.chat.id, "Use /help for commands")

# Flask App for keep-alive
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Bot is running!"

def run_flask():
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    # Start Flask in a separate thread
    Thread(target=run_flask).start()
    
    # Start the bot with error handling
    logger.info("Starting bot...")
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            logger.error(f"Bot crashed with error: {e}")
            logger.info("Restarting bot in 5 seconds...")
            time.sleep(5)