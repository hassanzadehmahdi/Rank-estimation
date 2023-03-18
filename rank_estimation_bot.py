#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
from typing import Dict
import pickle

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

reply_keyboard = [
    [
        "باکس زبان",
        "باکس ریاضی",
    ],
    [
        "باکس نظریه",
        "باکس هوش مصنوعی",
    ],
    [
        "باکس مدار منطقی",
        "باکس سیستم عامل",
    ],
    ["معدل موثر", "محاسبه رتبه"],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])


async def rank_estimation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""
    context.user_data.clear()
    ConversationHandler.END
    await update.message.reply_text(
        "لطفا بعد از انتخاب هر باکس درصد اون رو وارد کن و در نهایت برای حساب کردن رتبه گزینه محاسبه رتبه رو بزن.",
        reply_markup=markup,
    )
    return CHOOSING


async def regular_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for info about the selected predefined choice."""
    text = update.message.text
    context.user_data["choice"] = text
    await update.message.reply_text(f"لطفا درصد {text} رو وارد کن.")

    return TYPING_REPLY


async def received_information(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Store info provided by user and ask for the next category."""
    user_data = context.user_data
    text = update.message.text
    category = user_data["choice"]
    user_data[category] = text
    del user_data["choice"]

    await update.message.reply_text(
        "خیلی خوب! لطفا بقیه باکس ها رو هم کامل کن اینا باکس هایی هستن که تا الان وارد کردی\n"
        + f"{facts_to_str(user_data)}"
        + "\nخب می تونی بقیه باکس هارو وارد کنی یا این که یه باکس رو اصلاح کنی یا اگه همه رو وارد کردی، محاسبه رتبه رو بزن تا رتبه رو حساب کنم",
        reply_markup=markup,
    )

    return CHOOSING


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the gathered info and end the conversation."""
    user_data = context.user_data
    if "choice" in user_data:
        del user_data["choice"]

    try:
        # calculate average percentage
        all_avg = avg(
            float(user_data["باکس زبان"]),
            float(user_data["باکس ریاضی"]),
            float(user_data["باکس نظریه"]),
            float(user_data["باکس هوش مصنوعی"]),
            float(user_data["باکس مدار منطقی"]),
            float(user_data["باکس سیستم عامل"]),
        )

        # calculate min medium percentage
        med_all_avg = (
            all_avg[0] - 1,
            all_avg[1] - 1,
            all_avg[2] - 1,
            all_avg[3] - 1,
        )

        # calculate min average percentage
        min_all_avg = (all_avg[0] - 2, all_avg[1] - 2, all_avg[2] - 2, all_avg[3] - 2)

        uni_avg = 17
        if user_data["معدل موثر"]:
            uni_avg = float(user_data["معدل موثر"])

        await update.message.reply_text(
            "لطفا کمی صبر کن، یکم طول میکشه نتیجه آماده بشه",
        )

        # load models
        ai_model = pickle.load(open("./models/ai_model.pickle", "rb"))
        logic_model = pickle.load(open("./models/logic_model.pickle", "rb"))
        network_model = pickle.load(open("./models/network_model.pickle", "rb"))
        software_model = pickle.load(open("./models/software_model.pickle", "rb"))

        # calculate ranks
        ai_rank = int(ai_model.predict([[uni_avg, all_avg[0]]])[0][0])
        network_rank = int(network_model.predict([[uni_avg, all_avg[1]]])[0][0])
        logic_rank = int(logic_model.predict([[uni_avg, all_avg[2]]])[0][0])
        software_rank = int(software_model.predict([[uni_avg, all_avg[3]]])[0][0])

        # calculate medium ranks
        med_ai_rank = int(ai_model.predict([[uni_avg, med_all_avg[0]]])[0][0])
        med_network_rank = int(network_model.predict([[uni_avg, med_all_avg[1]]])[0][0])
        med_logic_rank = int(logic_model.predict([[uni_avg, med_all_avg[2]]])[0][0])
        med_software_rank = int(
            software_model.predict([[uni_avg, med_all_avg[3]]])[0][0]
        )

        # calculate minimum ranks
        min_ai_rank = int(ai_model.predict([[uni_avg, min_all_avg[0]]])[0][0])
        min_network_rank = int(network_model.predict([[uni_avg, min_all_avg[1]]])[0][0])
        min_logic_rank = int(logic_model.predict([[uni_avg, min_all_avg[2]]])[0][0])
        min_software_rank = int(
            software_model.predict([[uni_avg, min_all_avg[3]]])[0][0]
        )

        message = (
            f"رتبه شبکه های کامپیوتری - {network_rank}\n"
            + f"رتبه هوش مصنوعی - {ai_rank}\n"
            + f"رتبه معماری - {logic_rank}\n"
            + f"رتبه نرم افزار - {software_rank}\n"
        )

        med_message = (
            f"رتبه شبکه های کامپیوتری - {med_network_rank}\n"
            + f"رتبه هوش مصنوعی - {med_ai_rank}\n"
            + f"رتبه معماری - {med_logic_rank}\n"
            + f"رتبه نرم افزار - {med_software_rank}\n"
        )

        min_message = (
            f"رتبه شبکه های کامپیوتری - {min_network_rank}\n"
            + f"رتبه هوش مصنوعی - {min_ai_rank}\n"
            + f"رتبه معماری - {min_logic_rank}\n"
            + f"رتبه نرم افزار - {min_software_rank}\n"
        )

        await update.message.reply_text(
            f"اگه بخوام خوش بینانه در نظر بگیرم این نتیجه به دست میاد:\n{message}\n"
            + f"می تونم واقع بینانه هم حساب کنم این طوری میشه:\n{med_message}\n"
            + f"اما میشه بدبینانه هم نگاه کرد:\n{min_message}",
            reply_markup=ReplyKeyboardRemove(),
        )

        with open("logs.txt", "a") as f:
            f.write(f"{update.message.from_user.username} - {user_data} - {all_avg}\n")

        f.close()

        user_data.clear()
        return ConversationHandler.END
    except:
        await update.message.reply_text(
            "لطفا تمام باکس ها و معدل موثر رو وارد کن.\nدقت کن که باید همشون عدد باشن.",
            reply_markup=markup,
        )

        return CHOOSING


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="سلام\nبه بات تخمین رتبه مهندسی کامپیوتر خوش اومدی.\nلطفا برای اطلاع از نحوه کارکرد بات از گزینه /help کمک بگیر.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="برای شروع از دستور /rank_estimation کمک بگیر.\nاگه دیدی ربات هنگ کرد از دستور /stop استفاده کن.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="ببخشید، این دستور رو پشتیبانی نمی کنم.",
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End Conversation by command."""
    context.user_data.clear()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="بای بای",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def avg(
    en: float = 0,
    math: float = 0,
    signal: float = 0,
    ai: float = 0,
    logic: float = 0,
    os: float = 0,
):

    ai_avg = ((en) + (math * 2) + (signal * 3) + (ai * 4) + (logic * 2) + (os * 3)) / 15
    network_avg = (
        (en) + (math * 2) + (signal * 2) + (ai * 3) + (logic * 3) + (os * 4)
    ) / 15
    logic_avg = (
        (en) + (math * 2) + (signal * 2) + (ai * 3) + (logic * 4) + (os * 3)
    ) / 15
    software_avg = (
        (en) + (math * 2) + (signal * 2) + (ai * 4) + (logic * 3) + (os * 3)
    ) / 15
    return (ai_avg, network_avg, logic_avg, software_avg)


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = (
        Application.builder()
        .token("6256343745:AAH9UzPvRWg_8rLPnb4jmKhkz9KuyWydAPw")
        .build()
    )

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    rank_estimation_handler = ConversationHandler(
        entry_points=[CommandHandler("rank_estimation", rank_estimation)],
        states={
            CHOOSING: [
                MessageHandler(
                    filters.Regex(
                        "^(باکس زبان|باکس ریاضی|باکس نظریه|باکس هوش مصنوعی|باکس مدار منطقی|باکس سیستم عامل|معدل موثر)$"
                    ),
                    regular_choice,
                ),
                # MessageHandler(filters.Regex("^Something else...$"), custom_choice),
            ],
            TYPING_CHOICE: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^محاسبه رتبه$")),
                    regular_choice,
                )
            ],
            TYPING_REPLY: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^محاسبه رتبه$")),
                    received_information,
                )
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^محاسبه رتبه$"), done),
            CommandHandler("stop", stop),
            CommandHandler("start", start),
            CommandHandler("rank_estimation", rank_estimation),
            CommandHandler("help", help),
        ],
    )
    start_handler = CommandHandler("start", start)
    help_handler = CommandHandler("help", help)
    stop_handler = CommandHandler("stop", stop)

    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(rank_estimation_handler)
    application.add_handler(stop_handler)

    # Other handlers
    unsupported_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unsupported_handler)
    unknown_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), unknown)
    application.add_handler(unknown_handler)
    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
