import re
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = "YOUR_BOT_TOKEN"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    # detect instagram reel link
    match = re.search(r"https://www\.instagram\.com/reel/[A-Za-z0-9_-]+", text)

    if not match:
        return

    url = match.group(0)

    await update.message.reply_text("Downloading reel...")

    ydl_opts = {
        "outtmpl": "video.%(ext)s",
        "format": "mp4"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    await update.message.reply_video(video=open("video.mp4", "rb"))


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

app.run_polling()
