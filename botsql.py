#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to send timed Telegram messages.

This Bot uses the Updater class to handle the bot and the JobQueue to send
timed messages.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Alarm Bot example, sends a message after a set time.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import mysql.connector
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

DTP, IMPIANTO, LOCALE = range(3)
a="temp"
b="temp"
mydb = mysql.connector.connect(
  	host="localhost",
  	user="root",
  	password="Pass1234",
  	database="prova"
	)
# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
# Best practice would be to replace context with an underscore,
# since context is an unused local variable.
# This being an example and not having context present confusing beginners,
# we decided to have it present as context.

def start(update: Update, context: CallbackContext) -> int:
    mycursor = mydb.cursor()
    sql="SELECT * FROM dtp"
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    update.message.reply_text(
        myresult,
        reply_markup=ReplyKeyboardRemove(),
    )

    return DTP
 
def dtp(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    global a
    a=update.message.text
    sede=(a,)
    mycursor = mydb.cursor()
    sql="SELECT impianti.* FROM impianti,dtp WHERE dtp.ID = impianti.IDdtp && dtp.sede =%s"
    mycursor.execute(sql,sede)
    myresult = mycursor.fetchall()
    update.message.reply_text(
        myresult,
        reply_markup=ReplyKeyboardRemove(),
    )

    return IMPIANTO

def impianto(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    global b
    b = update.message.text
    sede=(a,b, )
    mycursor = mydb.cursor()
    sql="SELECT locale.*" \
        "FROM (SELECT impianti.* FROM impianti,dtp WHERE dtp.ID = impianti.IDdtp && dtp.sede = %s) as q1, locale " \
        "WHERE locale.IDimpianto = q1.ID && q1.impianto =%s"
    mycursor.execute(sql,sede)
    myresult = mycursor.fetchall()
    update.message.reply_text(
        myresult,
        reply_markup=ReplyKeyboardRemove(),
    )

    return LOCALE

def locale(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user

    sede=(a,b,update.message.text, )
    mycursor = mydb.cursor()
    sql="SELECT apparato.apparato, apparato.IP" \
        " FROM (SELECT locale.* FROM (SELECT impianti.* FROM impianti,dtp WHERE dtp.ID = impianti.IDdtp && dtp.sede = %s) as q1, locale " \
        "WHERE locale.IDimpianto = q1.ID && q1.impianto =%s) as q2, apparato " \
        "WHERE apparato.IDlocale=q2.ID && q2.locale=%s"
    mycursor.execute(sql,sede)
    myresult = mycursor.fetchall()
    update.message.reply_text(
        myresult,
        reply_markup=ReplyKeyboardRemove(),
    )

def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    update.message.reply_text(
        'Bye!', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def main() -> None:

    # Create the Updater and pass it your bot's token.
    updater = Updater("2096033612:AAHfgsypvFVG2irYoPrOLNQFJ2TVnJHxlOk")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DTP: [MessageHandler(Filters.text & ~Filters.command,dtp)],
            IMPIANTO: [MessageHandler(Filters.text & ~Filters.command, impianto)],
            LOCALE: [MessageHandler(Filters.text & ~Filters.command, locale)],

        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
