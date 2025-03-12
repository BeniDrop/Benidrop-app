from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BaseModel
import logging
from models import User, Badge, Task, CompletedTask
from sqlalchemy.orm import sessionmaker
from models import engine
import uuid

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database session
Session = sessionmaker(bind=engine)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    user = update.effective_user
    session = Session()
    
    # Check if user exists
    db_user = session.query(User).filter(User.telegram_id == str(user.id)).first()
    if not db_user:
        # Create new user
        referral_code = str(uuid.uuid4())[:8]
        db_user = User(
            telegram_id=str(user.id),
            username=user.username,
            referral_code=referral_code
        )
        session.add(db_user)
        session.commit()
    
    # Create main menu keyboard
    keyboard = [
        [InlineKeyboardButton("🎮 Open Mini App", web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}"))],
        [InlineKeyboardButton("📋 Tasks", callback_data="tasks")],
        [InlineKeyboardButton("👥 Invite Friends", callback_data="invite")],
        [InlineKeyboardButton("💰 My Balance", callback_data="balance")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"Welcome to BeniDrop Airdrop Bot! ✨\n\n"
        f"Complete tasks, invite friends, and earn tokens!\n"
        f"Don't forget to connect your MultiversX wallet to receive rewards."
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    session.close()

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    session = Session()
    
    try:
        if query.data == "tasks":
            # Show available tasks
            tasks_text = (
                "📋 Available Tasks:\n\n"
                f"1. Join Telegram Group ({settings.TELEGRAM_GROUP})\n"
                f"2. Join Telegram Channel ({settings.TELEGRAM_CHANNEL})\n"
                f"3. Follow on Twitter ({settings.TWITTER_PROFILE})\n"
                "4. Daily Check-in\n\n"
                "Complete all tasks to maximize your rewards! 🎁"
            )
            await query.message.edit_text(tasks_text, reply_markup=get_tasks_keyboard())
            
        elif query.data == "invite":
            # Show referral information
            user = session.query(User).filter(User.telegram_id == str(query.from_user.id)).first()
            invite_text = (
                "👥 Invite Friends & Earn Rewards!\n\n"
                f"Your referral code: `{user.referral_code}`\n"
                f"Share this link: t.me/{context.bot.username}?start={user.referral_code}\n\n"
                "Earn 5,000 tokens for each friend who joins! 🎁"
            )
            await query.message.edit_text(invite_text, parse_mode='Markdown')
            
        elif query.data == "balance":
            # Show user balance and badges
            user = session.query(User).filter(User.telegram_id == str(query.from_user.id)).first()
            balance_text = (
                "💰 Your PawCoin Balance\n\n"
                f"Total Tokens: {user.total_tokens:,}\n"
                f"Check-in Streak: {user.check_in_streak} days\n"
                f"Wallet: {user.wallet_address or 'Not connected'}\n\n"
                "Connect your MultiversX wallet to receive rewards! 🔗"
            )
            await query.message.edit_text(balance_text)
    
    finally:
        session.close()
        await query.answer()

def get_tasks_keyboard():
    """Create keyboard for tasks menu"""
    keyboard = [
        [InlineKeyboardButton("✅ Verify Tasks", callback_data="verify_tasks")],
        [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def setup_bot():
    """Setup and return the bot application"""
    app = Application.builder().token(settings.BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    return app

if __name__ == "__main__":
    app = setup_bot()
    app.run_polling()
