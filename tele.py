import json, os
from datetime import datetime, time, timedelta
from telegram.ext import ApplicationBuilder, ContextTypes, JobQueue
import pytz
import asyncio
from telegram.ext import CommandHandler
from telegram import Update

LOG = "log.json"
BOT_TOKEN = ""  # Replace with your actual bot token
CHAT_ID = this id you would find in telegram  # Primary user's chat ID

# File to store authorized chat IDs
AUTH_FILE = "authorized_users.json"
classes = [[(16, 0),(17, 30)],[(17,35),(19,25)],[(19,25),(21,30)]]  # Class timings in IST
def convert_class_to_attendance_time(classes):
    table ={}
    for Class in classes:
        start, end = Class
        start_time = time(*start)
        end_time = time(*end)
        table[f"{start_time}–{end_time}"]=check_attendance_for_interval(pw_history, start_time, end_time)
    return table    

# Load or create authorized users list
def load_authorized_users():
    if not os.path.exists(AUTH_FILE):
        # Initialize with the primary CHAT_ID
        auth_data = {"authorized_users": [CHAT_ID]}
        save_authorized_users(auth_data)
        return auth_data
    with open(AUTH_FILE) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            auth_data = {"authorized_users": [CHAT_ID]}
            save_authorized_users(auth_data)
            return auth_data

def save_authorized_users(auth_data):
    with open(AUTH_FILE, 'w') as f:
        json.dump(auth_data, f, indent=2)

# Command to authorize a new user
async def authorize_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    app= ApplicationBuilder().token(BOT_TOKEN).build()
    await app.bot.delete_webhook(drop_pending_updates=True)
    # Only the primary user (CHAT_ID) can authorize others
    if update.effective_chat.id != CHAT_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ You are not authorized to add users."
        )
        return
        
    # Check if user provided a chat ID argument
    if not context.args or not context.args[0].isdigit():
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please provide a valid chat ID, e.g.: /authorize 123456789"
        )
        return
        
    new_chat_id = int(context.args[0])
    auth_data = load_authorized_users()
    
    if new_chat_id in auth_data["authorized_users"]:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"User with chat ID {new_chat_id} is already authorized."
        )
        return
        
    auth_data["authorized_users"].append(new_chat_id)
    save_authorized_users(auth_data)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"✅ User with chat ID {new_chat_id} has been authorized."
    )
    # Try to notify the newly authorized user
    try:
        await context.bot.send_message(
            chat_id=new_chat_id,
            text="You have been authorized to use this productivity bot. Try /report or /attendance commands."
        )
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Note: Could not notify the new user. Make sure they have started a chat with the bot first."
        )

def load():
    if not os.path.exists(LOG):
        return {"date": str(datetime.now().date()), "productive": 0, "unproductive": 0, "domains": {}, "productivity": 0, "last_timestamp": {}, "history": {}}
    with open(LOG) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {"date": str(datetime.now().date()), "productive": 0, "unproductive": 0, "domains": {}, "productivity": 0, "last_timestamp": {}, "history": {}}
    if data["date"] != str(datetime.now().date()):
        return {"date": str(datetime.now().date()), "productive": 0, "unproductive": 0, "domains": {}, "productivity": 0, "last_timestamp": {}, "history": {}}
    
    # Ensure last_timestamp and history exist
    if "last_timestamp" not in data:
        data["last_timestamp"] = {}
    if "history" not in data:
        data["history"] = {}
        
    return data

def format_timestamp(utc_str):
    if not utc_str or utc_str == "❌ No timestamp":
        return "❌ No timestamp"
        
    try:
        # Handle various timestamp formats
        if 'T' in utc_str:
            # ISO format with T separator
            if utc_str.endswith('Z'):
                # UTC format ending with Z
                utc_time = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
            else:
                # ISO format without Z
                utc_time = datetime.fromisoformat(utc_str)
        else:
            # Try simple format
            utc_time = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S")
            
        # Convert to IST
        ist_time = utc_time.astimezone(pytz.timezone("Asia/Kolkata"))
        return ist_time.strftime("%d-%m-%Y %H:%M:%S")
    except Exception as e:
        print(f"Error formatting timestamp '{utc_str}': {e}")
        return f"❌ Invalid timestamp: {utc_str}"

def convert_to_ist(utc_str):
    """Convert UTC timestamp string to IST datetime object"""
    try:
        if 'T' in utc_str:
            if utc_str.endswith('Z'):
                utc_time = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
            else:
                utc_time = datetime.fromisoformat(utc_str)
        else:
            utc_time = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S")
        
        ist_time = utc_time.astimezone(pytz.timezone("Asia/Kolkata"))
        return ist_time
    except Exception as e:
        print(f"Error converting timestamp '{utc_str}' to IST: {e}")
        return None

def check_attendance_for_interval(history, start_time, end_time) -> tuple[int, int]:
    """
    Check if total time spent during interval exceeds threshold.
    start_time and end_time are datetime.time objects for the interval boundaries in IST.
    """
    if not history:
        return False
    
    # Convert start and end times to datetime objects for today
    today = datetime.now(pytz.timezone("Asia/Kolkata")).date()
    interval_start = datetime.combine(today, start_time).astimezone(pytz.timezone("Asia/Kolkata"))
    interval_end = datetime.combine(today, end_time).astimezone(pytz.timezone("Asia/Kolkata"))
    
    # Calculate total interval duration in seconds
    interval_duration = (interval_end - interval_start).total_seconds()
    
    # Define attendance threshold (interval duration minus 20 minutes)
    threshold_seconds = interval_duration - (20 * 60)
    
    # Calculate time spent on pw.live during this interval
    time_spent_seconds = 0
    
    for entry in history:
        entry_time = convert_to_ist(entry["timestamp"])
        if entry_time and interval_start.time() <= entry_time.time() <= interval_end.time():
            time_spent_seconds += entry["seconds"]
    
    print(f"Interval {start_time}-{end_time}: spent {time_spent_seconds}s, threshold: {threshold_seconds}s")
    return time_spent_seconds , (int(time_spent_seconds-threshold_seconds))

def give_status(present, slot) -> str:
    now = datetime.now(pytz.timezone("Asia/Kolkata"))
    slot_start = datetime.strptime((slot.split("–")[0].strip()),"%H:%M")
    slot_end = datetime.strptime((slot.split("–")[1].strip()),"%H:%M")
    if now.time() < slot_start.time():
        return "⏳ Class not started yet"
    elif now.time() < slot_end.time():
        return "⏳ Class in progress"
    else:
        if present[0] >= present[1]:
            a= str(present[0]/3600)
            b= str((present[0]-present[1])/60)
            return f"✅ almost fully  Attended he attended class for {a} hours and miss {b} minutes"
        elif present[0] == 0:
            return "❌ very bad  Not Attended  even for a second "
        else:
            a= str(present[0]/3600)
            b= str((present[1]-present[0])/60)
            return f" 🤔 maybe Not Attended  he attended class for {a} hours and miss {b} minutes"

async def check_attendance_command(update, context):
    app= ApplicationBuilder().token(BOT_TOKEN).build()
    await app.bot.delete_webhook(drop_pending_updates=True)
    # Get the chat ID of the user who sent the command
    chat_id = update.effective_chat.id
    
    data = load()
    pw_history = data.get("history", {}).get("www.pw.live", [])

    # Define class intervals (in IST)
    attendance= convert_class_to_attendance_time(classes)
    msg = "📚 Live Class Attendance:\n\n"
    for slot, present in attendance.items():
        status = give_status(present,slot)
        msg += f"{slot} → {status}\n"

    await context.bot.send_message(chat_id=chat_id, text=msg)

async def check_attendance(context):
    app= ApplicationBuilder().token(BOT_TOKEN).build()
    await app.bot.delete_webhook(drop_pending_updates=True)
    data = load()
    pw_history = data.get("history", {}).get("www.pw.live", [])

    # Define class intervals (in IST)
    attendance =convert_class_to_attendance_time(classes)
    msg = "📚 Live Class Attendance:\n\n"
    for slot, present in attendance.items():
        status = give_status(present, slot)
        msg += f"{slot} → {status}\n"

    await context.bot.send_message(chat_id=CHAT_ID, text=msg)

def generate_daily_report(data):
    hours = lambda s: round(s / 3600, 2)
    message = (
        f"📊 पढ़ाई की रिपोर्ट ({data['date']}):\n\n"
        f"📗 कितना समय पढाई की: {hours(data['productive'])} घंटे\n"
        f"📕 Unproductive Time: {hours(data['unproductive'])} घंटे\n"
        f"📈 Productivity Score: {round(data.get('productivity', 0), 2)}%\n\n"
        f"🌐 Domains Used क्या देखा और आखिरी बार कब:\n"
    )
    
    last_seen = data.get("last_timestamp", {})

    # Debug - print what timestamps we're working with
    print(f"Last seen timestamps: {last_seen}")

    for domain, time_spent in data.get("domains", {}).items():
        ts = last_seen.get(domain)
        if ts:
            ts_str = format_timestamp(ts)
        else:
            ts_str = "❌ No timestamp"
        message += f"🔸 {domain}: {hours(time_spent)} घंटे (🕒 {ts_str})\n"
    return message

async def send_scheduled_message_command(update, context: ContextTypes.DEFAULT_TYPE):
    # Get the chat ID of the user who sent the command
    chat_id = update.effective_chat.id
    app= ApplicationBuilder().token(BOT_TOKEN).build()
    await app.bot.delete_webhook(drop_pending_updates=True)
    
    data = load()
    message = generate_daily_report(data)
    await context.bot.send_message(chat_id=chat_id, text=message)

async def send_scheduled_message(context: ContextTypes.DEFAULT_TYPE):
    app= ApplicationBuilder().token(BOT_TOKEN).build()
    await app.bot.delete_webhook(drop_pending_updates=True)
    
    data = load()
    message = generate_daily_report(data)
    await context.bot.send_message(chat_id=CHAT_ID, text=message)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    job_queue = app.job_queue
    app.add_handler(CommandHandler("attendance", check_attendance_command))
    app.add_handler(CommandHandler("report", send_scheduled_message_command))
  
    

    # Add handler for adding authorized users
    app.add_handler(CommandHandler("authorize", authorize_user_command))
    
    if job_queue is None:
        raise RuntimeError("JobQueue is not initialized.")

    job_queue.run_daily(send_scheduled_message, time=time(12, 30), data={"title": "🕧 दोपहर की रिपोर्ट"})  # 12:30 PM
    job_queue.run_daily(send_scheduled_message, time=time(21, 30), data={"title": "🌙 रात की रिपोर्ट"})     # 9:30 PM
    job_queue.run_daily(send_scheduled_message, time=time(23, 50), data={"title": "📅 अंतिम रिपोर्ट"})       # 11:50 PM
    job_queue.run_daily(check_attendance, time=time(16, 30), data={"title": "📚 क्लास उपस्थिति"})  # 4:30 PM
    job_queue.run_daily(check_attendance, time=time(18, 0), data={"title": "📚 क्लास उपस्थिति"})   # 6:00 PM
    job_queue.run_daily(check_attendance, time=time(19, 45), data={"title": "📚 क्लास उपस्थिति"})  # 7:45 PM 
    app.run_polling()

if __name__ == "__main__":
    print("app will start")
    main()
