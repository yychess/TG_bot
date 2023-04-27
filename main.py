import logging
import re
import sqlite3

from telegram.ext import Application, MessageHandler, filters
from telegram.ext import CommandHandler
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
import datetime as dt

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

reply_keyboard = [['/start', '/help'],
                  ['/my_plans']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)


async def start(update, context):
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}!")
    await update.message.reply_text(
        "\nЯ - твой помощник-календарик"
        f" Ты можешь написать мне дату мероприятия, я её запомню,"
        f" а если ты захочешь узнать все свои мероприятия на месяц, просто скажи мне об этом /my_plans,"
        f" и я тебе помогу\n\n"
        f"Пожалуйста, присылай даты в формате:\nдень.месяц название мероприятия "
        f"(обрати внимание, что день и месяц нужно заполнить в числовом формате)\n"
        f"\nПри необходимости воспользуйся помощью /help",
        reply_markup=markup
    )


async def help_command(update, context):
    await update.message.reply_text("Формат:\nдень.месяц название мероприятия "
                                    "(обрати внимание, что день и месяц нужно заполнить в числовом формате)")


def correctness_check(day, month):
    today = dt.date.today()
    try:
        date = dt.date(today.year, month, day)
        if today > date:
            date = dt.date(today.year + 1, month, day)
            return date
        return date
    except ValueError:
        return False


async def add(update, context):
    mas = str(update.message.text).split("\n")
    for text in mas:
        if re.search(r"\d{2}[.]\d{2}\s", text):
            day = text[:2]
            month = text[3:5]
            event = text[6:]

            date = correctness_check(int(day), int(month))
            if not date:
                await update.message.reply_text("Такой даты не существует")
                continue

            con = sqlite3.connect(f"calendar.sqlite")
            cur = con.cursor()

            cur.execute(f"insert into calendar values {(date.day, date.month, date.year, event, update.message.chat_id)}")
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
    result = cur.execute(f"""SELECT day, month, year, event FROM calendar where user = {update.message.chat_id}""").fetchall()
    if result:
        plans = "Твои планы:\n"
        mas_plans = []
        for day, month, year, event in result:
            date = dt.date(int(year), int(month), int(day))
            if date < dt.date.today():
                cur.execute(f"delete from calendar where day = {day} and month = {month} and year = {year}")
                con.commit()
                continue
            mas_plans.append([date, event])
        mas_plans.sort()
        for plan in mas_plans:
            date, event = plan
            plans += f"{str(date.day).rjust(2, '0')}.{str(date.month).rjust(2, '0')} - {event}\n"
    else:
        plans = "Ты не записал ещё ничего"
    await update.message.reply_text(plans)
    con.close()


async def close_keyboard(update, context):
    await update.message.reply_text(
        "Ok",
        reply_markup=ReplyKeyboardRemove()
    )


def main():
    application = Application.builder().token("6228401017:AAFtJTEFmLU-RxHu__tZG0v8B1qFR7y9uQI").build()

    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, add)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("my_plans", my_plans))
    application.add_handler(CommandHandler("close", close_keyboard))
    application.add_handler(text_handler)

    application.run_polling()


if __name__ == '__main__':
    main()
