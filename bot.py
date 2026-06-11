import os
import base64
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8843314860:AAEohBPUXZ_8hkuAdIyPWakRyRyIEUu8y3M"
ANTHROPIC_API_KEY = "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"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """أنت محلل مالي خبير متخصص في تحليل الأسهم وعقود الأوبشن. عند استقبال صورة قدم:
1. تشخيص سريع لما تراه
2. التحليل الفني الكامل
3. اتجاه السهم مع نسبة الثقة
4. العقد الأنسب مع سعر التنفيذ وتاريخ الانتهاء
5. نقطة الدخول والخروج ووقف الخسارة
6. المخاطر المحتملة
الأسلوب: احترافي، دقيق، باللغة العربية."""

user_sessions = {}

def get_session(user_id):
    if user_id not in user_sessions:
        user_sessions[user_id] = []
    return user_sessions[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 مرحباً! أنا مستشارك المالي الذكي\n\n"
        "أرسل لي صورة مخطط السهم أو عقود الأوبشن وسأحللها فوراً!\n\n"
        "/clear لمسح المحادثة\n\n"
        "⚠️ للأغراض التعليمية فقط"
    )

async def clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_sessions[update.effective_user.id] = []
    await update.message.reply_text("✅ تم مسح المحادثة!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = get_session(user_id)
    text = update.message.text or update.message.caption or ""
    content_parts = []

    if update.message.photo:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        file_bytes = await file.download_as_bytearray()
        b64 = base64.b64encode(bytes(file_bytes)).decode()
        content_parts.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}})

    if text:
        content_parts.append({"type": "text", "text": text})
    elif content_parts:
        content_parts.append({"type": "text", "text": "حلل هذه الصورة واختر أفضل عقد أوبشن."})

    if not content_parts:
        await update.message.reply_text("أرسل صورة أو اكتب سؤالك 📊")
        return

    session.append({"role": "user", "content": content_parts})
    msg = await update.message.reply_text("⏳ جاري التحليل...")

    try:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=session
        )
        reply = response.content[0].text
        session.append({"role": "assistant", "content": reply})
        await msg.delete()
        for i in range(0, len(reply), 4000):
            await update.message.reply_text(reply[i:i+4000])
    except Exception as e:
        await msg.delete()
        await update.message.reply_text(f"⚠️ خطأ: {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_cmd))
    app.add_handler(MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), handle_message))
    print("✅ البوت يعمل!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
