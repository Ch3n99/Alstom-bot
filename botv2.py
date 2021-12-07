#!/usr/bin/env python
# pylint: disable=C0116,W0613

import logging, os
import mysql.connector
from peewee import *
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from playhouse.db_url import connect


db = connect('mysql://root:Pass1234@localhost:3306/prova')

class BaseModel(Model):
    class Meta:
        database = db

class Dtp(BaseModel):
    id = IntegerField()
    sede = CharField(200)

class Impianti(BaseModel):
    id = IntegerField()
    iddtp = IntegerField()
    impianto = CharField(200)

class Locale(BaseModel):
    id = IntegerField()
    iddtp = IntegerField()
    idimpianto = IntegerField()
    locale = CharField(200)
    tecnologia = CharField(200)
    
class Apparato(BaseModel):
    id = IntegerField()
    iddtp = IntegerField()
    idimpianto = IntegerField()
    idlocale =IntegerField()
    idfamiglia = IntegerField()
    apparato=CharField(200)
    ip=CharField(200)


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)
msg = "temp"
msg2= "temp"
DTP, IMPIANTO, LOCALE = range(3)

def start(update: Update, context: CallbackContext) -> None:
    """Displays info on how to use the bot."""
    update.message.reply_text(
        "Usa /ricerca per ricercare degli apparati e i loro dettagli.\n"
        "Usa --- ancora da fare"
    )

def ricerca(update: Update, context: CallbackContext) -> int:
    db.connect()
    dtps=Dtp.select()
    toShow="DTP disponibili:\n\n"
    for dtp in dtps:
        toShow+="ID: "+str(dtp.id)+" - sede: "+dtp.sede+"\n"
    toShow+="\nDigita un ID presente nella lista e invialo. \nDigita nuovamente /start se vuoi ricominciare."
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )

    db.close()

    return DTP
 
def dtp(update: Update, context: CallbackContext) -> int:
    global msg
    msg=update.message.text
    db.connect()
    try:
        dtps = Dtp.get(Dtp.id == msg)
    except Dtp.DoesNotExist:
        update.message.reply_text(
            'Errore, id non presente, riprova o clicca su /start per ricominciare', reply_markup=ReplyKeyboardRemove()
        )
        db.close()

        return DTP

    impianti = Impianti.select().join(Dtp, on=(Impianti.iddtp == Dtp.id)).where(Dtp.id == msg)
    toShow="Impianti disponibili:\n\n"
    for impianto in impianti:
        toShow+="ID: "+str(impianto.id)+" - impianto: "+impianto.impianto+"\n"
    toShow+="\nDigita un ID presente nella lista e invialo."
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()

    return IMPIANTO

def impianto(update: Update, context: CallbackContext) -> int:
    global msg2
    msg2 = update.message.text
    db.connect()
    try:
        imp = Impianti.get((Impianti.iddtp == msg) & (Impianti.id == msg2))
    except Impianti.DoesNotExist:
        update.message.reply_text(
            'Errore, id non presente, riprova o clicca su /start per ricominciare', reply_markup=ReplyKeyboardRemove()
        )
        db.close()

        return IMPIANTO
    locali = Locale.select().join(Impianti, on=(Impianti.id == Locale.idimpianto))\
        .join(Dtp, on=(Impianti.iddtp == Dtp.id)).where((Dtp.id == msg) & (Impianti.id == msg2))
    toShow = "Locali disponibili:\n\n"
    for locale in locali:
        toShow += "ID: " + str(locale.id) + " - locale: " + locale.locale + "\n"
    toShow += "\nDigita un ID presente nella lista e invialo."
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()

    return LOCALE

def locale(update: Update, context: CallbackContext) -> int:
    msg3 = update.message.text
    db.connect()
    try:
        loc = Locale.get((Locale.iddtp == msg) & (Locale.idimpianto == msg2) & (Locale.id == msg3))
    except Locale.DoesNotExist:
        update.message.reply_text(
            'Errore, id non presente, riprova o clicca su /start per ricominciare', reply_markup=ReplyKeyboardRemove()
        )
        db.close()

        return LOCALE
    apparati = Apparato.select().join(Locale, on=(Locale.id == Apparato.idlocale)).join(Impianti, on=(Impianti.id == Locale.idimpianto))\
        .join(Dtp, on=(Impianti.iddtp == Dtp.id)).where((Dtp.id == msg) & (Impianti.id == msg2) & (Locale.id == msg3))
    toShow = "Apparati disponibili:\n\n"
    for apparato in apparati:
        toShow += "ID: " + str(apparato.id) + " - IP: " + apparato.ip + "\n"
    toShow += "\nFine procedura, clicca su /start per ricominciare o /cancel per uscire"
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()

def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    update.message.reply_text(
        'Bye!', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def main() -> None:

    # Create the Updater and pass it your bot's token.
    updater = Updater("2020671779:AAEjtbOgJnJkcL6M7Ge8uhg7PY_AWX_whdE")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('ricerca', ricerca)],
        states={
            DTP: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, dtp)],
            IMPIANTO: [MessageHandler(Filters.text & ~Filters.command, impianto)],
            LOCALE: [MessageHandler(Filters.text & ~Filters.command, locale)],

        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
    )

    dispatcher.add_handler(CommandHandler("start", start))

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
