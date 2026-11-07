import os
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

def init_db():
    conn = sqlite3.connect("study_bot.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            name TEXT,
            questions_asked INTEGER DEFAULT 0,
            answers_given INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_user(uid, uname, fname):
    conn = sqlite3.connect("study_bot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?, ?, ?, 0, 0)", (uid, uname, fname))
    else:
        c.execute("UPDATE users SET username = ?, name = ? WHERE user_id = ?", (uname, fname, uid))
    conn.commit()
    conn.close()

async def handle_q(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.message.from_user
    save_user(u.id, u.username or "NoUsername", u.first_name)
    
    conn = sqlite3.connect("study_bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET questions_asked = questions_asked + 1 WHERE user_id = ?", (u.id,))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"📌 Question logged for {u.first_name}!")

async def handle_a(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.message.from_user
    save_user(u.id, u.username or "NoUsername", u.first_name)
    
    conn = sqlite3.connect("study_bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET answers_given = answers_given + 1 WHERE user_id = ?", (u.id,))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"💡 Answer logged for {u.first_name}!")

async def void_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_uid = update.message.from_user.id
    conn = sqlite3.connect("study_bot.db")
    c = conn.cursor()

    args = context.args
    target = args[0].lstrip("@") if args else None

    if target:
        c.execute("SELECT name, username, questions_asked, answers_given FROM users WHERE username = ?", (target,))
    else:
        c.execute("SELECT name, username, questions_asked, answers_given FROM users WHERE user_id = ?", (my_uid,))
    
    user_data = c.fetchone()
    if not user_data:
        await update.message.reply_text("❌ Profile not found! Type /Q or /A first.")
        conn.close()
        return

    name, username, q_asked, a_replies = user_data

    c.execute("SELECT user_id, (questions_asked + answers_given) as score FROM users ORDER BY score DESC")
    all_users = c.fetchall()
    conn.close()

    target_uid = my_uid
    if target:
        conn2 = sqlite3.connect("study_bot.db")
        c2 = conn2.cursor()
        match = c2.execute("SELECT user_id FROM users WHERE username = ?", (target,)).fetchone()
        conn2.close()
        if match:
            target_uid = match[0]

    rank = "Unranked"
    for idx, (u_id, score) in enumerate(all_users, 1):
        if u_id == target_uid:
            rank = f"#{idx}"
            break

    profile_text = (
        f"🛡️ **VOID PROFILE: @{username}** 🛡️\n"
        f"👤 **Name:** {name}\n"
        f"-----------------------------------\n"
        f"❓ **Q asked:** {q_asked}\n"
        f"💬 **Q replies:** {a_replies}\n"
        f"🏆 **Grp rank:** {rank}\n"
        f"-----------------------------------"
    )
    await update.message.reply_text(profile_text, parse_mode="Markdown")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("void", void_profile))
app.add_handler(CommandHandler("Q", handle_q))
app.add_handler(CommandHandler("A", handle_a))
print("🤖 Study Bot is up and running...")
app.run_polling()
  
