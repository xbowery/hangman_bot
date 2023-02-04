import logging
import os

from dotenv import load_dotenv
from pymongo import MongoClient
from random_word import RandomWords
from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          ConversationHandler, Filters, CallbackContext, CallbackQueryHandler)


r = RandomWords()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

load_dotenv("./.env")
TOKEN = os.getenv("token")
MONGOURL = os.getenv("mongourl")
client = MongoClient(MONGOURL)

db = client["hangman_bot"]
USER_DB = db["users"]
STATS_DB = db["stats"]

HANGMANPICS = ['''
  +------+
  |     |
        |
        |
        |
        |
=========''', '''
  +------+
  |     |
  O     |
        |
        |
        |
=========''', '''
  +------+
  |     |
  O     |
  |     |
        |
        |
=========''', '''
  +------+
  |     |
  O     |
 /|     |
        |
        |
=========''', '''
  +------+
  |     |
  O     |
 /|\    |
        |
        |
=========''', '''
  +------+
  |     |
  O     |
 /|\    |
 /      |
        |
=========''', '''
  +------+
  |     |
  O     |
 /|\    |
 / \    |
        |
=========''']

NO_OF_LIVES = 6
VALID_ALPHABETS = 'qwertyuiopasdfghjklzxcvbnm'

KEYBOARD = [
    [
        InlineKeyboardButton(VALID_ALPHABETS[0], callback_data=VALID_ALPHABETS[0]),
        InlineKeyboardButton(VALID_ALPHABETS[1], callback_data=VALID_ALPHABETS[1]),
        InlineKeyboardButton(VALID_ALPHABETS[2], callback_data=VALID_ALPHABETS[2]),
        InlineKeyboardButton(VALID_ALPHABETS[3], callback_data=VALID_ALPHABETS[3]),
        InlineKeyboardButton(VALID_ALPHABETS[4], callback_data=VALID_ALPHABETS[4]),
        InlineKeyboardButton(VALID_ALPHABETS[5], callback_data=VALID_ALPHABETS[5]),
        InlineKeyboardButton(VALID_ALPHABETS[6], callback_data=VALID_ALPHABETS[6]),
    ],
    [
        InlineKeyboardButton(VALID_ALPHABETS[7], callback_data=VALID_ALPHABETS[7]),
        InlineKeyboardButton(VALID_ALPHABETS[8], callback_data=VALID_ALPHABETS[8]),
        InlineKeyboardButton(VALID_ALPHABETS[9], callback_data=VALID_ALPHABETS[9]),
        InlineKeyboardButton(VALID_ALPHABETS[10], callback_data=VALID_ALPHABETS[10]),
        InlineKeyboardButton(VALID_ALPHABETS[11], callback_data=VALID_ALPHABETS[11]),
        InlineKeyboardButton(VALID_ALPHABETS[12], callback_data=VALID_ALPHABETS[12]),
        InlineKeyboardButton(VALID_ALPHABETS[13], callback_data=VALID_ALPHABETS[13]),
    ],
    [
        InlineKeyboardButton(VALID_ALPHABETS[14], callback_data=VALID_ALPHABETS[14]),
        InlineKeyboardButton(VALID_ALPHABETS[15], callback_data=VALID_ALPHABETS[15]),
        InlineKeyboardButton(VALID_ALPHABETS[16], callback_data=VALID_ALPHABETS[16]),
        InlineKeyboardButton(VALID_ALPHABETS[17], callback_data=VALID_ALPHABETS[17]),
        InlineKeyboardButton(VALID_ALPHABETS[18], callback_data=VALID_ALPHABETS[18]),
        InlineKeyboardButton(VALID_ALPHABETS[19], callback_data=VALID_ALPHABETS[19]),
    ],
    [
        InlineKeyboardButton(VALID_ALPHABETS[20], callback_data=VALID_ALPHABETS[20]),
        InlineKeyboardButton(VALID_ALPHABETS[21], callback_data=VALID_ALPHABETS[21]),
        InlineKeyboardButton(VALID_ALPHABETS[22], callback_data=VALID_ALPHABETS[22]),
        InlineKeyboardButton(VALID_ALPHABETS[23], callback_data=VALID_ALPHABETS[23]),
        InlineKeyboardButton(VALID_ALPHABETS[24], callback_data=VALID_ALPHABETS[24]),
        InlineKeyboardButton(VALID_ALPHABETS[25], callback_data=VALID_ALPHABETS[25]),
    ]
]

REPLY_MARKUP = InlineKeyboardMarkup(KEYBOARD)


def init_user(update: Update):
    data = {
        "_id": update.effective_user.id,
        "First Name": update.effective_user.first_name,
        "Last Name": update.effective_user.last_name,
        "Username": update.effective_user.username,
        "In Game": False,
    }

    update_data_obj = {"$set": data}

    USER_DB.update_one(
        {"_id": update.effective_user.id},
        update_data_obj,
        upsert=True
    )

    stats_data = STATS_DB.find_one(
        {"_id": update.effective_user.id}
    )

    if stats_data is not None:
        return

    stats_data = {
        "_id": update.effective_user.id,
        "Games Played": 0,
        "Games Won": 0,
    }

    update_stats_data = {"$set": stats_data}

    STATS_DB.update_one(
        {"_id": update.effective_user.id},
        update_stats_data,
        upsert=True
    )


def start(update: Update, context: CallbackContext):
    init_user(update)

    if update.message.chat.type == "private":
        update.message.reply_text(
            "Hi! Thanks for using the Hangman Bot!\n\n"
            "Please press /game to start a game of Hangman!",
            reply_markup=None
        )
    else:
        update.message.reply_text(
            "Hi! Thanks for using the Hangman Bot!\n\n"
            "Please press /game to start a game of Hangman!\n\n"
            "Take note that this command only works in private message!",
            reply_markup=None
        )


def init_game(update: Update, context: CallbackContext):
    user_data = USER_DB.find_one(
        {"_id": update.effective_user.id}
    )

    if user_data is None:
        init_user(update)

    if update.message.chat.type != "private":
        return

    stats_data = STATS_DB.find_one(
        {"_id": update.effective_user.id}
    )

    if user_data["In Game"]:
        context.bot.send_message(
            chat_id=update.effective_user.id,
            text="You have a previous game in progress! Please complete that game first before starting a new one!",
        )

        return

    stats_data["Games Played"] += 1
    user_data["In Game"] = True

    update_data_obj = {"$set": stats_data}
    update_user_data = {"$set": user_data}

    STATS_DB.update_one(
        {"_id": update.effective_user.id},
        update_data_obj,
        upsert=True
    )

    USER_DB.update_one(
        {"_id": update.effective_user.id},
        update_user_data,
        upsert=True
    )

    word = r.get_random_word()

    while len(word) < 8:
        word = r.get_random_word()

    word_status = []

    for num in range(len(word)):
        word_status.append(False)

    init_data = {
        "user_id": update.effective_user.id,
        "Lives": NO_OF_LIVES,
        "Word": word,
        "Guesses": [],
        "Status": word_status,
    }

    context.chat_data["Game State"] = init_data

    msg = HANGMANPICS[0]
    msg += "\n\n<b>Guess the Word!</b>\n\n"
    msg += (len(word) * "_ ")
    msg += f"\n\n<b>No. of Lives Remaining:\n❤️❤️❤️❤️❤️❤️ ({NO_OF_LIVES})</b>"

    update.message.reply_text(msg, reply_markup=REPLY_MARKUP, parse_mode=ParseMode.HTML)

    return 1


def game(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    guess = query['data']

    game_state = context.chat_data["Game State"]
    actual_word = game_state["Word"]
    word_status = game_state["Status"]

    user_data = USER_DB.find_one(
        {"_id": game_state["user_id"]}
    )

    if guess not in game_state['Guesses']:
        game_state['Guesses'].append(guess)

        if guess not in actual_word:
            game_state["Lives"] -= 1
        else:
            to_change = [pos for pos, char in enumerate(actual_word) if char == guess]

            for num in to_change:
                game_state["Status"][num] = True

        game_won = True

        for entries in game_state["Status"]:
            if not entries:
                game_won = False

        context.chat_data["Game State"] = game_state

        emojis = "💔" * (NO_OF_LIVES - game_state['Lives']) + "❤️" * game_state['Lives']

        msg = HANGMANPICS[NO_OF_LIVES - game_state["Lives"]]

        if game_state["Lives"] == 0:
            msg += f"\n\n<b>No. of Lives Remaining:\n{emojis} (0)</b>"
            msg += "\n\n<b>Game Over! You lost! 😰😰😰</b>"
            msg += f"\n\nThe actual word was: <b>{actual_word}</b>"

            query.edit_message_text(
                text=msg,
                reply_markup=None,
                parse_mode=ParseMode.HTML
            )

            user_data["In Game"] = False
            update_user_data = {"$set": user_data}
            USER_DB.update_one(
                {"_id": game_state["user_id"]},
                update_user_data,
                upsert=True
            )

            context.bot.send_message(
                chat_id=game_state["user_id"],
                text="Thank you for playing the game!\n\nPress /game for another round!"
            )

            return ConversationHandler.END

        if game_won:
            msg += f"<b>No. of Lives Remaining:\n{emojis} ({game_state['Lives']})</b>"
            msg += "\n\n<b>Game Over! You won! 🏆🏆🏆</b>"
            msg += f"\n\nThe actual word was: <b>{actual_word}</b>"

            query.edit_message_text(
                text=msg,
                reply_markup=None,
                parse_mode=ParseMode.HTML
            )

            user_data["In Game"] = False
            update_user_data = {"$set": user_data}
            USER_DB.update_one(
                {"_id": game_state["user_id"]},
                update_user_data,
                upsert=True
            )

            context.bot.send_message(
                chat_id=game_state["user_id"],
                text="Thank you for playing the game!\n\nPress /game for another round!"
            )

            user_data = STATS_DB.find_one(
                {"_id": game_state["user_id"]}
            )

            user_data["Games Won"] += 1

            update_data_obj = {"$set": user_data}

            STATS_DB.update_one(
                {"_id": game_state["user_id"]},
                update_data_obj,
                upsert=True
            )

            return ConversationHandler.END

        past_guesses = str(game_state['Guesses']).replace('\'', '')

        msg += f"\n\nPast Guesses: {past_guesses}"

        msg += "\n\n<b>Guess the Word!</b>\n\n"

        for i in range(len(word_status)):
            if word_status[i]:
                msg += actual_word[i] + " "
            else:
                msg += "_ "

        msg += f"\n\n<b>No. of Lives Remaining:\n{emojis} ({game_state['Lives']})</b>"

        query.edit_message_text(
            text=msg,
            reply_markup=REPLY_MARKUP,
            parse_mode=ParseMode.HTML
        )

        return 1
    else:
        emojis = "💔" * (NO_OF_LIVES - game_state['Lives']) + "❤️" * game_state['Lives']

        msg = HANGMANPICS[NO_OF_LIVES - game_state["Lives"]]
        msg += "\n\nSorry, you have already chosen this letter. Please select another letter."

        past_guesses = str(game_state['Guesses']).replace('\'', '')

        msg += f"\n\nPast Guesses: {past_guesses}"
        msg += "\n\n<b>Guess the Word!</b>\n\n"

        for i in range(len(word_status)):
            if word_status[i]:
                msg += actual_word[i] + " "
            else:
                msg += "_ "

        msg += f"\n\n<b>No. of Lives Remaining:\n{emojis} ({game_state['Lives']})</b>"

        query.edit_message_text(
            text=msg,
            reply_markup=REPLY_MARKUP,
            parse_mode=ParseMode.HTML
        )

        return 1


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Action Cancelled!")

    return ConversationHandler.END

def end(update: Update, context: CallbackContext):
    update.message.reply_text("Action Cancelled!")

    return ConversationHandler.END


def show_stats(update: Update, context: CallbackContext):
    init_user(update)

    data = STATS_DB.find_one(
        {"_id": update.effective_user.id}
    )

    first_name = update.effective_user.first_name
    first_name = first_name if first_name is not None else "User"

    last_name = update.effective_user.last_name
    last_name = last_name if last_name is not None else ""

    total_no = data["Games Played"]
    win_no = data["Games Won"]

    update.message.reply_text(
        f"*Statistics for {first_name + ' ' + last_name} (@{update.effective_user.username}):*\n\n"
        f"Total Games Played: {total_no}\n"
        f"Total Games Won: {win_no}\n"
        f"Win Percentage: {round((win_no / total_no) * 100, 2)}%",
        parse_mode=ParseMode.MARKDOWN
    )


def main():
    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))

    game_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("game", init_game)],
        states = {
            1: [
                CommandHandler("end", end),
                CallbackQueryHandler(game, pattern="a"),
                CallbackQueryHandler(game, pattern="b"),
                CallbackQueryHandler(game, pattern="c"),
                CallbackQueryHandler(game, pattern="d"),
                CallbackQueryHandler(game, pattern="e"),
                CallbackQueryHandler(game, pattern="f"),
                CallbackQueryHandler(game, pattern="g"),
                CallbackQueryHandler(game, pattern="h"),
                CallbackQueryHandler(game, pattern="i"),
                CallbackQueryHandler(game, pattern="j"),
                CallbackQueryHandler(game, pattern="k"),
                CallbackQueryHandler(game, pattern="l"),
                CallbackQueryHandler(game, pattern="m"),
                CallbackQueryHandler(game, pattern="n"),
                CallbackQueryHandler(game, pattern="o"),
                CallbackQueryHandler(game, pattern="p"),
                CallbackQueryHandler(game, pattern="q"),
                CallbackQueryHandler(game, pattern="r"),
                CallbackQueryHandler(game, pattern="s"),
                CallbackQueryHandler(game, pattern="t"),
                CallbackQueryHandler(game, pattern="u"),
                CallbackQueryHandler(game, pattern="v"),
                CallbackQueryHandler(game, pattern="w"),
                CallbackQueryHandler(game, pattern="x"),
                CallbackQueryHandler(game, pattern="y"),
                CallbackQueryHandler(game, pattern="z"),
                CallbackQueryHandler(game, pattern=" "),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    dispatcher.add_handler(game_conv_handler)

    dispatcher.add_handler(CommandHandler("stats", show_stats))

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()
