import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackContext
)
import sqlite3
import re
import os

# Configuration - Replace with your details
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN')
CHANNEL_LINK = "https://t.me/tactical_osint"
GROUP_LINK = "https://t.me/iFROGYOUofiicial"
TWITTER_LINK = "https://x.com/salejames299"
ADMIN_ID = 123456789  # Your Telegram User ID

# Database setup
conn = sqlite3.connect('airdrop.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id INTEGER PRIMARY KEY, 
              wallet TEXT,
              completed INTEGER DEFAULT 0)''')
conn.commit()

# Bot setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# SOL address validation
def is_valid_sol_address(address):
    return re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', address) is not None

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    welcome_msg = (
        "🌟 Welcome to Mr Kay's Airdrop Campaign! 🌟\n\n"
        "To qualify for the airdrop:\n"
        "1. Join our Telegram Channel: @tactical_osint\n"
        "2. Join our Telegram Group: @iFROGYOUofiicial\n"
        "3. Follow our Twitter: @salejames299\n"
        "4. Submit your SOL wallet address\n\n"
        "Click the button below when you've completed all tasks!"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ VERIFY TASKS", callback_data="verify_tasks")]
    ]
    await update.message.reply_text(
        welcome_msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )

# Verification handler
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "verify_tasks":
        # Mark tasks as completed without verification
        c.execute('''INSERT OR IGNORE INTO users (user_id) VALUES (?)''', (user_id,))
        c.execute('''UPDATE users SET completed = 1 WHERE user_id = ?''', (user_id,))
        conn.commit()
        
        # Check if wallet already submitted
        c.execute('''SELECT wallet FROM users WHERE user_id = ?''', (user_id,))
        wallet = c.fetchone()[0]
        
        if wallet:
            # All tasks complete
            await query.edit_message_text(
                "🎉 Congratulations! You've passed Mr Kay's Airdrop!\n"
                "100 SOL will be sent to your wallet soon!\n\n"
                "Note: This is a test bot - no actual SOL will be sent."
            )
        else:
            # Request wallet
            await query.edit_message_text(
                "📋 All social tasks verified!\n\n"
                "Please send your SOL wallet address now:"
            )
            context.user_data["awaiting_wallet"] = True

# Wallet submission handler
async def wallet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    wallet_address = update.message.text.strip()
    
    if not context.user_data.get("awaiting_wallet"):
        return
    
    if is_valid_sol_address(wallet_address):
        # Save wallet and mark as complete
        c.execute('''UPDATE users SET wallet = ? WHERE user_id = ?''', (wallet_address, user_id))
        conn.commit()
        
        # Send success message
        await update.message.reply_text(
            "congratulations 10 sol is en it way to your add\n\n"
            "Note: This is a test bot - no actual SOL will be sent."
        )
        
        # Send final confirmation
        await update.message.reply_text(
            "🎉 Congratulations! You've passed Mr Kay's Airdrop!\n"
            "100 SOL will be sent to your wallet soon!"
        )
        
        context.user_data["awaiting_wallet"] = False
    else:
        await update.message.reply_text("❌ Invalid SOL address. Please send a valid SOL wallet address:")

# Export data command
async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command")
        return
    
    c.execute('''SELECT * FROM users''')
    all_users = c.fetchall()
    
    with open('airdrop_data.csv', 'w') as f:
        f.write("User ID,Wallet,Completed\n")
        for user in all_users:
            f.write(f"{user[0]},{user[1]},{user[2]}\n")
    
    await update.message.reply_document(document=open('airdrop_data.csv', 'rb'))

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

# Main function
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_handler))
    application.add_handler(CommandHandler("export", export_data))
    application.add_error_handler(error_handler)
    
    application.run_polling()

if __name__ == "__main__":
    main()
