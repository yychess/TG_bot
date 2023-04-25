import logging
import re
import sqlite3

from telegram.ext import Application, MessageHandler, filters
from telegram.ext import CommandHandler
import datetime as dt

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def start(update, context):
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}!\nЯ - твой помощник-календарик"
        f" Ты можешь написать мне дату мероприятия, я её запомню,"
        f" а если ты захочешь узнать все свои мероприятия на месяц, просто скажи мне об этом /my_plans,"
        f" и я тебе помогу\n\n"
        f"Пожалуйста, присылай даты в формате:\nдень.месяц название мероприятия "
        f"(обрати внимание, что день и месяц нужно заполнить в числовом формате)\n"
        f"\nПри необходимости воспользуйся помощью /help",
    )


async def help_command(update, context):
    await update.message.reply_text("Формат:\nдень.месяц название мероприятия "
                                    "(обрати внимание, что день и месяц нужно заполнить в числовом формате)")


async def add(update, context):
    text = str(update.message.text)
    if re.search(r"\d{2}[.]\d{2}\s", text):
        day = text[:2]
        month = text[3:5]
        event = text[6:]
        con = sqlite3.connect(f"calendar.sqlite")
        cur = con.cursor()
        cur.execute(f"insert into calendar values {(day, month, event)}")
        con.commit()
        await update.message.reply_text("Я записал дату\n" + text)
        con.close()
    else:
        await update.message.reply_text("Дата передана в неверном формате\n\n"
                                        "Верный: \nдень.месяц название мероприятия\n"
                                        "обрати внимание, что день и месяц нужно заполнить в числовом формате")


async def my_plans(update, context):
    con = sqlite3.connect(f"calendar.sqlite")
    cur = con.cursor()
    result = cur.execute("""SELECT * FROM calendar""").fetchall()
    await update.message.reply_text(result)
    con.close()


def main():
    application = Application.builder().token("6228401017:AAFtJTEFmLU-RxHu__tZG0v8B1qFR7y9uQI").build()

    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, add)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("my_plans", my_plans))
    application.add_handler(text_handler)

    application.run_polling()


if __name__ == '__main__':
    main()
