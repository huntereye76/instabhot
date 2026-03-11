import re
import os
import time
import asyncio
import yt_dlp
from collections import defaultdict
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Allowed groups
ALLOWED_GROUPS = [
    -1001234567890,  # replace with your group ID
]

GROUP_LINK = "https://t.me/yourgroup"

# Rate limit per user (seconds)
RATE_LIMIT = 60

last_request = defaultdict(float)

# Download queue
download_queue = asyncio.Queue()


# DM start message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.type == "private":

        await update.message.reply_text(
            f"This bot works only in groups.\n\n"
            f"Join the group and send Instagram reel links:\n{GROUP_LINK}"
        )


# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    text = update.message.text or ""

    # Only allow specific groups
    if chat_id not in ALLOWED_GROUPS:
        return

    # Detect reel link
    match = re.search(r"https://www\.instagram\.com/reel/[A-Za-z0-9_-]+", text)

    if not match:
        return

    # Rate limit
    now = time.time()
    if now - last_request[user_id] < RATE_LIMIT:
        await update.message.reply_text(
            "Please wait before sending another link."
        )
        return

    last_request[user_id] = now

    url = match.group(0)

    # Add to queue
    await download_queue.put((update, context, url))

    position = download_queue.qsize()

    await update.message.reply_text(
        f"Added to queue.\nPosition: {position}"
    )


# Worker function
async def worker(worker_id):

    while True:

        update, context, url = await download_queue.get()

        try:

            await update.message.reply_text(
                f"Worker {worker_id} downloading..."
            )

            ydl_opts = {
                "outtmpl": "video.%(ext)s",
                "format": "mp4",
                "max_filesize": 50 * 1024 * 1024,
                "quiet": True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            await update.message.reply_video(
                video=open("video.mp4", "rb")
            )

            os.remove("video.mp4")

        except Exception as e:

            await update.message.reply_text(
                "Failed to download this reel."
            )

        finally:

            download_queue.task_done()


async def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Start 3 workers
    asyncio.create_task(worker(1))
    asyncio.create_task(worker(2))
    asyncio.create_task(worker(3))

    await app.run_polling()


asyncio.run(main())
