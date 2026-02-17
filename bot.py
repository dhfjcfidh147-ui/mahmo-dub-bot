import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp

TOKEN = "8257471551:AAHYerzMpmkB11P-hStgyrGq-0TgXEdxj7o"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("📥 تحميل فيديو", callback_data="download"),
         InlineKeyboardButton("🌍 ترجمة", callback_data="dub")],
        [InlineKeyboardButton("🤖 مساعدة", callback_data="help")],
    ]
    await update.message.reply_text(
        f"👋 أهلاً {user.first_name}!\n\n🎬 *مدبلج الأفلام الذكي*\n\nاختار من القائمة 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "download":
        await query.edit_message_text("📥 ابعتلي رابط الفيديو من يوتيوب أو تيك توك أو انستجرام!")
        context.user_data['mode'] = 'download'
    elif query.data == "dub":
        await query.edit_message_text("🌍 ابعتلي النص اللي عايز تترجمه!")
        context.user_data['mode'] = 'translate'
    elif query.data == "help":
        await query.edit_message_text(
            "🤖 *المساعدة*\n\n/start - القائمة الرئيسية\n/download - تحميل فيديو\n/translate - ترجمة نص",
            parse_mode="Markdown"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if any(d in text for d in ['youtube.com','youtu.be','tiktok.com','instagram.com','facebook.com','fb.watch']):
        await handle_download(update, context, text)
        return
    if context.user_data.get('mode') == 'translate':
        await handle_translate(update, context, text)
        return
    keyboard = [[InlineKeyboardButton("📥 تحميل", callback_data="download"), InlineKeyboardButton("🌍 ترجمة", callback_data="dub")]]
    await update.message.reply_text("اضغط /start أو اختار 👇", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    msg = await update.message.reply_text("⏳ جاري التحميل...")
    try:
        ydl_opts = {'format': 'best[filesize<50M]/best', 'outtmpl': '/tmp/%(title)s.%(ext)s', 'noplaylist': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            title = info.get('title', 'فيديو')
        await msg.edit_text(f"✅ تم! جاري الإرسال...\n📹 {title}")
        with open(file_path, 'rb') as f:
            await update.message.reply_video(video=f, caption=f"🎬 {title}", supports_streaming=True)
        await msg.delete()
        os.remove(file_path)
    except Exception as e:
        logger.error(e)
        await msg.edit_text("❌ فشل التحميل! تأكد من الرابط وإن الفيديو عام وأقل من 50MB")

async def handle_translate(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    msg = await update.message.reply_text("🌍 جاري الترجمة...")
    try:
        url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text)}&langpair=auto|ar"
        data = requests.get(url, timeout=10).json()
        if data['responseStatus'] == 200:
            await msg.edit_text(f"✅ *الترجمة:*\n\n{data['responseData']['translatedText']}", parse_mode="Markdown")
        else:
            await msg.edit_text("❌ فشلت الترجمة!")
    except Exception as e:
        logger.error(e)
        await msg.edit_text("❌ حدث خطأ!")
    context.user_data['mode'] = 'chat'

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("download", lambda u,c: u.message.reply_text("ابعتلي رابط الفيديو!")))
    app.add_handler(CommandHandler("translate", lambda u,c: u.message.reply_text("ابعتلي النص!")))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("البوت شغال!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
