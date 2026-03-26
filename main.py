from dotenv import load_dotenv
load_dotenv()

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from app.services import bot
from agno.agent import Agent, Message

# 1. Setup Configuration
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# If using ngrok, this would be: "https://xxxx-xxxx.ngrok-free.app/webhook"
SERVICE_BASE_URL = os.getenv("SERVICE_PUBLIC_URL")
WEBHOOK_URL = f"{SERVICE_BASE_URL}/webhook"

# 2. Define your Bot Logic (The 'Receiver')
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        user_text = update.message.text
        print(f"Received message: {user_text}")
        await update.message.reply_text(f"I received your message dsasd: {user_text}")

# 3. Initialize the Application
ptb_app = Application.builder().token(TOKEN).build()
ptb_app.add_handler(CommandHandler("start", start))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return # If either is missing, stop here and do nothing.
    
    if update.message:
        user_id = update.effective_user.id
        first_name = update.effective_user.first_name
        username = update.effective_user.username
        text = update.message.text
        print(f"Received normal message: {text} from :: {first_name} user id {user_id}")
        if not text:
            await update.message.reply_text(f"Echo: {text}")
            return
            
        msg = [Message(content=text, role="user")]
        res_msg = bot.talk_to_v_gf(msg)
        
        for msg in res_msg:
            if not msg:
                continue
            if isinstance(msg.content, list):
                for cur_content in msg.content:
                    if not cur_content:
                        continue
                    # await update.message.reply_text(cur_content)
                    await update.message.reply_photo(
                        photo=cur_content,
                    )
            
            if isinstance(msg.content, str):
                # print(f"[{msg.role}] -> {str(msg.content)}")
                await update.message.reply_text(msg.content)

ptb_app.add_handler(MessageHandler(filters.TEXT, handle_message))

# 4. The Lifespan: This starts the bot when FastAPI starts
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the bot and set the webhook address
    await ptb_app.initialize()
    await ptb_app.bot.set_webhook(url=WEBHOOK_URL)
    await ptb_app.start()
    print(f"Webhook set to {WEBHOOK_URL}")
    yield
    # Clean shutdown
    await ptb_app.stop()
    await ptb_app.shutdown()

# Pass the lifespan to FastAPI
app = FastAPI(lifespan=lifespan)

# 5. The Webhook Endpoint
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, ptb_app.bot)
        # This sends the update to your 'start' handler
        await ptb_app.process_update(update)
    except Exception as e:
        print(f"Error processing update: {e}")
    
    return {"status": "ok"}

@app.get("/")
def read_root():
    return {"Hello": "World"}