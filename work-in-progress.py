#!/usr/bin/env python
# pylint: disable=C0116,W0613
import json
import logging, os
from peewee import *
from datetime import datetime
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, Update
import cv2

# System libraries
import os
from os import listdir
from os.path import isfile, join

from io import BytesIO
from PIL import Image
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from playhouse.db_url import connect
# stringa di connessione al database
db = connect('mysql://root:Pass1234@localhost:3306/prova')
token="1999421296:AAEyNoV8fpxrUwKzihFGbUx26oyzYe9yLwA"



# dichiaro le classi corrispondenti alle tabelle del DB
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
    idlocale = IntegerField()
    idfamiglia = IntegerField()
    apparato = CharField(200)
    ip = CharField(200)


class Famigliaapparato(BaseModel):
    id = IntegerField()
    idmacro = IntegerField()
    famiglia = CharField(200)


class Macrofamiglia(BaseModel):
    id = IntegerField()
    macrofamiglia = CharField(200)
    status = CharField(200)
    exporder = IntegerField()


class Criticità(BaseModel):
    id = IntegerField()
    label = CharField(200)


class Causa_evento(BaseModel):
    id = IntegerField()
    label = CharField(200)


class Tipo_guasto(BaseModel):
    id = IntegerField()
    label = CharField(200)
    idfamiglia = IntegerField()


class Stato(BaseModel):
    id = IntegerField()
    stato_ticket = CharField(200)


class Ticket(BaseModel):
    id = IntegerField()
    dtp = CharField(200)
    impianto = CharField(200)
    tipo_sistema = CharField(200)
    criticita = IntegerField()
    causa_evento = IntegerField()
    stato = IntegerField()


class Guasto(BaseModel):
    id = IntegerField()
    ticket_id = IntegerField()
    locale = CharField(200)
    sottosistema = CharField(200)
    apparato = CharField(200)
    tipo_guasto = CharField(200)
    tipo_guasto_altro = CharField(200)
    note = CharField(200)
    tag_1 =CharField(200)
    tag_2 = CharField(200)
    tag_3 = CharField(200)
    apparato_altro = CharField(200)
    famigliaapparato = CharField(200)
    stato_guasto = IntegerField()


class Chiamata(BaseModel):
    id= IntegerField()
    idticket = IntegerField()
    idguasto = IntegerField()
    after_sales_engineer = CharField(200)
    manutentore = CharField(200)
    data = CharField(200)
    durata = CharField(200)
    descrizione = CharField(200)
    analisi_soluzione = CharField(200)
    numero_manutentore = CharField(200)
    tipologia = IntegerField()
    reperibilita = IntegerField()
    cliente = IntegerField()
    reperibilita_intrinseca = IntegerField()


class Manutentore(BaseModel):
    id = IntegerField()
    nome = CharField(200)
    iddtp = IntegerField()
    numero = CharField(200)


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)


logger = logging.getLogger(__name__)


# dichiaro variabili globali
msg = ""
msg2 = ""
dtp = ""
imp = ""
loc = ""
dtpname = ""
impname = ""
locname = ""
sysname = ""
appname = ""
famapp= ""
macrofam = ""
dtp=""
imp=""
loc=""
crit = ""
causa = ""
tipoguasto = ""
stato = ""
nome_man=""
numero_man=""
dataora=""
descr=""
idfamapp=""
iddtp=""
tg=""
k=0

# dichiaro nomi degli stati che serviranno per il conversation handler
DTP, IMPIANTO, QRCODE, LOCALE, APPARATO, CRITICITA, CAUSAEVENTO, TIPOGUASTO, INSERIMENTO , CHIAMATA, MANUTENTORE, DATAORA, DESCRIZIONE, UPDATE, SCELTA, NUOVO_MAN, NOME_MAN, NUMERO_MAN, SCELTA_MAN, TICKET = range(20)

# funzione start con menu di riepilogo
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Usa /ricerca per ricercare degli apparati e i loro dettagli.\n"
        "Usa /ticketc per creare un nuovo ticket cliente.\n"
        "Usa /aggiungi_chiamata per aggiungere una chiamata ad un guasto già presente.\n"
        "Usa /cancel per uscire in qualsiasi momento.\n"
    )

def scelta(update: Update, context: CallbackContext) -> int:
    toShow = "Scegliere se inserire campi manualmente o tramite QR Code\n, altrimenti clicca su /start per ricominciare o /cancel per uscire"
    reply_keyboard = [['Tastiera', 'QR Code']]
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='tipo inserimeto'
        ),
    )
    return SCELTA


# bot ricerca con i 2 diversi casi
def ricerca(update: Update, context: CallbackContext) -> int:
    global msg

    msg = update.message.text
    if(msg== "Tastiera"):
        db.connect()
        dtps = Dtp.select()
        toShow = "DTP disponibili:\n\n"
        for dtp in dtps:
            toShow += "ID: " + str(dtp.id) + " - sede: " + dtp.sede + "\n"
        toShow += "\nDigita un ID presente nella lista e invialo, altrimenti clicca su /start per ricominciare o /cancel per uscire"
        update.message.reply_text(
            toShow,
            reply_markup=ReplyKeyboardRemove(),
        )
        db.close()
        return DTP
    else:
        toShow="Inserire QR Code, altrimenti clicca su /start per ricominciare o /cancel per uscire"
        update.message.reply_text(
            toShow,
            reply_markup=ReplyKeyboardRemove(),
        )
        return QRCODE

# scelta dtp e visualizzazione risultati
def dtpr(update: Update, context: CallbackContext) -> int:
    global msg

    msg = update.message.text
    db.connect()
    try:
        dtps = Dtp.get(Dtp.id == msg)
    except Dtp.DoesNotExist:
        update.message.reply_text(
            'Errore, id non presente, riprova o clicca su /start per ricominciare o /cancel per uscire', reply_markup=ReplyKeyboardRemove()
        )
        db.close()
        return DTP

    impianti = Impianti.select().join(Dtp, on=(Impianti.iddtp == Dtp.id)).where(Dtp.id == msg)
    toShow = "Impianti disponibili:\n\n"
    for impianto in impianti:
        toShow += "ID: " + str(impianto.id) + " - impianto: " + impianto.impianto + "\n"
    toShow += "\nDigita un ID presente nella lista e invialo, altrimenti clicca su /start per ricominciare o /cancel per uscire"
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()
    return IMPIANTO


# scelta impianto e visualizzazione risultati
def impiantor(update: Update, context: CallbackContext) -> int:
    global msg2
    msg2 = update.message.text
    db.connect()
    try:
        imp = Impianti.get((Impianti.iddtp == msg) & (Impianti.id == msg2))
    except Impianti.DoesNotExist:
        update.message.reply_text(
            'Errore, id non presente, riprova o clicca su /start per ricominciare o /cancel per uscire', reply_markup=ReplyKeyboardRemove()
        )
        db.close()

        return IMPIANTO
    locali = Locale.select().join(Impianti, on=(Impianti.id == Locale.idimpianto)) \
        .join(Dtp, on=(Impianti.iddtp == Dtp.id)).where((Dtp.id == msg) & (Impianti.id == msg2))
    toShow = "Locali disponibili:\n\n"
    for locale in locali:
        toShow += "ID: " + str(locale.id) + " - locale: " + locale.locale + "\n"
    toShow += "\nDigita un ID presente nella lista e invialo, altrimenti clicca su /start per ricominciare o /cancel per uscire"
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()
    return LOCALE


# scelta locale e visualizzazione risultati
def localer(update: Update, context: CallbackContext) -> int:
    msg3 = update.message.text
    db.connect()
    try:
        loc = Locale.get((Locale.iddtp == msg) & (Locale.idimpianto == msg2) & (Locale.id == msg3))
    except Locale.DoesNotExist:
        update.message.reply_text(
            'Errore, id non presente, riprova o clicca su /start per ricominciare o /cancel per uscire', reply_markup=ReplyKeyboardRemove()
        )
        db.close()

        return LOCALE
    apparati = Apparato.select().join(Locale, on=(Locale.id == Apparato.idlocale)).join(Impianti, on=(
                Impianti.id == Locale.idimpianto)) \
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
    return ConversationHandler.END # fine funzione ricerca
    
#funzione che decodifica il qr ricevuto dall'utente e stampa i relativi apparati
def qrricerca(update: Update, context: CallbackContext) -> int:
    id_img = update.message.photo[-1].file_id
    foto = context.bot.getFile(id_img)
    new_file = context.bot.get_file(foto.file_id)
    new_file.download('qrcode.png')
    inputImage = cv2.imread('qrcode.png')
    qrDecoder = cv2.QRCodeDetector()
    try:
        data, _, _ = qrDecoder.detectAndDecode(inputImage)
    except:
        update.message.reply_text(
            'Errore, riprova o clicca su /start per ricominciare o /cancel per uscire', reply_markup=ReplyKeyboardRemove()
        )
        return QRCODE
    res= format(data)
    os.remove('qrcode.png')
    try:
    	load=json.loads(res)
    except:
    	update.message.reply_text(
            'Errore, riprova o clicca su /start per ricominciare o /cancel per uscire', reply_markup=ReplyKeyboardRemove()
        );return QRCODE
    db.connect()
    try:
        loc = Locale.get((Locale.iddtp == load["iddtp"]) & (Locale.idimpianto == load["idimpianto"]) & (Locale.id == load["idlocale"]))
    except Locale.DoesNotExist:
        update.message.reply_text(
            'Errore, locale non presente, riprova o clicca su /start per ricominciare o /cancel per uscire', reply_markup=ReplyKeyboardRemove()
        )
        db.close()
        return QRCODE
    #query per mostrare i nomi relativi agli id contenuti nel qr (mostrato per chiarezza/controllo)
    x=Dtp.get(Dtp.id== load["iddtp"])
    y=Impianti.get(Impianti.id== load["idimpianto"])
    z=Locale.get(Locale.id == load ["idlocale"])
    toShow="Il qr code si riferisce a: "+x.sede+"   -   Imp: "+y.impianto+"  -   Loc: "+z.locale+"\n"
    apparati = Apparato.select().join(Locale, on=(Locale.id == Apparato.idlocale)).join(Impianti, on=(
            Impianti.id == Locale.idimpianto)) \
        .join(Dtp, on=(Impianti.iddtp == Dtp.id)).where((Dtp.id == load["iddtp"]) & (Impianti.id == load["idimpianto"]) & (Locale.id == load["idlocale"]))
    toShow += "Apparati disponibili:\n\n"
    for apparato in apparati:
        toShow += "ID: " + str(apparato.id) + " - IP: " + apparato.ip + "\n"
    toShow += "\nFine procedura, clicca su /start per ricominciare o /cancel per uscire"
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()
    return ConversationHandler.END  # fine funzione ricerca


# comando per inserimento ticket

def scelta2(update: Update, context: CallbackContext) -> int:
    toShow = "Scegliere se inserire campi manualmente o tramite QR Code\n"
    reply_keyboard = [['Tastiera', 'QR Code']]
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='tipo inserimento'
        ),
    )
    return SCELTA

#visualizzazione DTP
def ricercains(update: Update, context: CallbackContext) -> int:
    global msg

    msg = update.message.text
    if (msg == "Tastiera"):
        db.connect()
        dtps = Dtp.select()
        toShow = "DTP disponibili:\n\n"
        for dtp in dtps:
            toShow += "ID: " + str(dtp.id) + " - sede: " + dtp.sede + "\n"
        toShow += "\nDigita un ID presente nella lista e invialo. \nDigita nuovamente /start per ricominciare o /cancel per uscire"
        update.message.reply_text(
            toShow,
            reply_markup=ReplyKeyboardRemove(),
        )
        db.close()
        return DTP
    else:
        toShow="Inserire QR Code"
        update.message.reply_text(
            toShow,
            reply_markup=ReplyKeyboardRemove(),
        )
        return QRCODE

# inserimento dtp e visualizzazione risultati
def dtptc(update: Update, context: CallbackContext) -> int:
    global dtp
    dtp = update.message.text
    db.connect()
    try:
        dtps = Dtp.get(Dtp.id == dtp)
    except Dtp.DoesNotExist:
        update.message.reply_text(
            'Errore, id non presente, riprova o clicca su /start per ricominciare o /cancel per uscire', reply_markup=ReplyKeyboardRemove()
        )
        db.close()

        return DTP
    dtps = Dtp.get(Dtp.id == dtp)
    global dtpname
    dtpname = dtps.sede
    impianti = Impianti.select().join(Dtp, on=(Impianti.iddtp == Dtp.id)).where(Dtp.sede == dtpname)
    toShow = "Impianti disponibili:\n\n"
    for impianto in impianti:
        toShow += "ID: " + str(impianto.id) + " - impianto: " + impianto.impianto + "\n"
    toShow += "\nDigita un ID presente nella lista e invialo, altrimenti clicca su /start per ricominciare o /cancel per uscire"
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()
    return IMPIANTO

# inserimento impianto e visualizzazione risultati
def impiantotc(update: Update, context: CallbackContext) -> int:
    global imp
    imp = update.message.text
    db.connect()
    try:
        imps = Impianti.get((Impianti.iddtp == dtp) & (Impianti.id == imp))
    except Impianti.DoesNotExist:
        update.message.reply_text(
            'Errore, id non presente, riprova o clicca su /start per ricominciare o /cancel per uscire', reply_markup=ReplyKeyboardRemove()
        )
        db.close()

        return IMPIANTO
    imps = Impianti.get(Impianti.id == imp)
    global impname, sysname
    impname = imps.impianto
    locali = Locale.select().join(Impianti, on=(Impianti.id == Locale.idimpianto)) \
        .join(Dtp, on=(Impianti.iddtp == Dtp.id)).where((Dtp.sede == dtpname) & (Impianti.impianto == impname))

    toShow = "Locali disponibili:\n\n"
    for locale in locali:
        toShow += "ID: " + str(locale.id) + " - locale: " + locale.locale + "\n"
        sysname = locale.tecnologia
    toShow += "\nTipo sistema: " + sysname + "\nDigita un ID presente nella lista e invialo, altrimenti clicca su /start per ricominciare o /cancel per uscire"
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()

    return LOCALE


# inserimento locale e visualizzazione risultati
def localetc(update: Update, context: CallbackContext) -> int:
    global loc
    loc = update.message.text
    db.connect()
    try:
        locs = Locale.get((Locale.iddtp == dtp) & (Locale.idimpianto == imp) & (Locale.id == loc))
    except Locale.DoesNotExist:
        update.message.reply_text(
            'Errore, id non presente, riprova o clicca su /start per ricominciare o /cancel per uscire', reply_markup=ReplyKeyboardRemove()
        )
        db.close()

        return LOCALE
    locs = Locale.get(Locale.id == loc)
    global locname
    locname = locs.locale
    apparati = Apparato.select().join(Locale, on=(Locale.id == Apparato.idlocale)).join(Impianti, on=(
                Impianti.id == Locale.idimpianto)) \
        .join(Dtp, on=(Impianti.iddtp == Dtp.id)).where(
        (Dtp.sede == dtpname) & (Impianti.impianto == impname) & (Locale.locale == locname))
    toShow = "Apparati disponibili:\n\n"
    for apparato in apparati:
        toShow += "ID: " + str(apparato.id) + " - APPARATO: " + apparato.apparato + "\n"
    toShow += "\nDigita un ID presente nella lista e invialo, altrimenti clicca su /start per ricominciare o /cancel per uscire"
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()
    return APPARATO


# inserimento apparato
def apparatotc(update: Update, context: CallbackContext) -> int:
    app = update.message.text
    db.connect()
    try:
        a = Apparato.get((Apparato.iddtp == dtp) & (Apparato.idimpianto == imp) & (Apparato.idlocale == loc) & (Apparato.id == app))
    except Apparato.DoesNotExist:
        update.message.reply_text(
            'Errore, id non presente, riprova o clicca su /start per ricominciare o /cancel per uscire', reply_markup=ReplyKeyboardRemove()
        )
        db.close()

        return APPARATO
    apps = Apparato.get(Apparato.id == app)
    global appname
    appname = apps.apparato
    family = Famigliaapparato.select().join(Apparato, on=(Apparato.idfamiglia == Famigliaapparato.id)).where(
        Apparato.id == app).limit(1)
    sottosys = Macrofamiglia.select().join(Famigliaapparato, on=(Famigliaapparato.idmacro == Macrofamiglia.id)).join(
        Apparato, on=(Apparato.idfamiglia == Famigliaapparato.id)).where(Apparato.id == app).limit(1)
    global famapp, macrofam
    q1=family.get()
    famapp=q1.famiglia
    toShow = "Famiglia apparato: " + famapp + "\n\n" #inserimento famiglia apparato
    q2=sottosys.get()
    macrofam=q2.macrofamiglia
    toShow += "Sottosistema: " + macrofam + "\n\n" #inserimento sottosistema (cioè la macrofamiglia)
    crit = Criticità.select()

    toShow += "elenco criticità':\n\n"
    opz = []

    for i in crit:
        toShow += "ID: " + str(i.id) + " - tipo: " + i.label + "\n"
        opz.append(i.label)
    toShow += "\nSchiaccia il pulsante corrispondente.\nAltrimenti clicca su /start per ricominciare o /cancel per uscire"
    reply_keyboard = [opz] #per inserimento criticità visualizzo opzioni su tastiera
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Seleziona criticità'
        ),
    )
    db.close()
    return CRITICITA

#inserimento qr con voci relative a dtp, impianto, locale, apparato
def qrins(update: Update, context: CallbackContext) -> int:
    id_img = update.message.photo[-1].file_id
    foto = context.bot.getFile(id_img)
    new_file = context.bot.get_file(foto.file_id)
    new_file.download('qrcode.png')
    inputImage = cv2.imread('qrcode.png')
    qrDecoder = cv2.QRCodeDetector()
    try:
        data, _, _ = qrDecoder.detectAndDecode(inputImage)
    except:
        update.message.reply_text(
            'Errore, riprova o clicca su /start per ricominciare o /cancel per uscire', reply_markup=ReplyKeyboardRemove()
        )
        return QRCODE
    res = format(data)
    os.remove('qrcode.png')
    try:
        load = json.loads(res)
    except:
        update.message.reply_text(
            'Errore, riprova o clicca su /start per ricominciare o /cancel per uscire', reply_markup=ReplyKeyboardRemove()
        )
        return QRCODE
    db.connect()
    try:
        app=Apparato.get(Apparato.id==load["idapparato"] & Apparato.idlocale==load["idlocale"] & Apparato.idimpianto==load["idimpianto"] & Apparato.iddtp==load["iddtp"])
    except Apparato.DoesNotExist:
        update.message.reply_text(
            'Errore, apparato non presente, riprova o clicca su /start per ricominciare o su /cancel per uscire', reply_markup=ReplyKeyboardRemove()
        )
        db.close()
        return QRCODE
    # query per mostrare i nomi relativi agli id contenuti nel qr (mostrato per chiarezza/controllo)
    x = Dtp.get(Dtp.id == load["iddtp"])
    y = Impianti.get(Impianti.id == load["idimpianto"])
    z = Locale.get(Locale.id == load["idlocale"])
    w = Apparato.get(Apparato.id == load["idapparato"])
    #adesso dagli id posso risalire ai nomi da salvare nelle tabelle
    global dtpname, impname, locname, appname
    dtpname = x.sede
    impname = y.impianto
    locname = z.locale
    appname = w.apparato
    toShow = "Il qr code si riferisce a: " + dtpname + "   -   Imp: " + impname + "  -   Loc: " + locname + "  -  App: " + appname + "\n"
    apparati = Apparato.select().join(Locale, on=(Locale.id == Apparato.idlocale)).join(Impianti, on=(
            Impianti.id == Locale.idimpianto)) \
        .join(Dtp, on=(Impianti.iddtp == Dtp.id)).where(
        (Dtp.id == load["iddtp"]) & (Impianti.id == load["idimpianto"]) & (Locale.id == load["idlocale"]))
    apps = Apparato.get(Apparato.id == app)
    appname = apps.apparato
    family = Famigliaapparato.select().join(Apparato, on=(Apparato.idfamiglia == Famigliaapparato.id)).where(
        Apparato.id == app).limit(1)
    sottosys = Macrofamiglia.select().join(Famigliaapparato, on=(Famigliaapparato.idmacro == Macrofamiglia.id)).join(
        Apparato, on=(Apparato.idfamiglia == Famigliaapparato.id)).where(Apparato.id == app).limit(1)
    global famapp, macrofam
    q1 = family.get()
    famapp = q1.famiglia
    toShow = "Famiglia apparato: " + famapp + "\n\n"  # inserimento famiglia apparato
    q2 = sottosys.get()
    macrofam = q2.macrofamiglia
    toShow += "Sottosistema: " + macrofam + "\n\n"  # inserimento sottosistema (cioè la macrofamiglia)
    crit = Criticità.select()
    toShow += "elenco criticità':\n\n"
    opz = []
    for i in crit:
        toShow += "ID: " + str(i.id) + " - tipo: " + i.label + "\n"
        opz.append(i.label)
    toShow += "\nSchiaccia il pulsante corrispondente, altrimenti clicca su /start per ricominciare o /cancel per uscire"
    reply_keyboard = [opz]  # per inserimento criticità visualizzo opzioni su tastiera
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Seleziona criticità'
        ),
    )
    db.close()
    return CRITICITA

#inserimento criticità
def criticitatc(update: Update, context: CallbackContext) -> int:
    global crit
    crit = update.message.text
    db.connect()
    try:
        c = Criticità.get(Criticità.label == crit)
    except Criticità.DoesNotExist:
        opz = []
        crt = Criticità.select()
        for i in crt:
            opz.append(i.label)
        reply_keyboard = [opz] #per inserimento criticità visualizzo opzioni su tastiera
        update.message.reply_text(
            "Errore, criticità non presente, riprova o clicca su /start per ricominciare o /cancel per uscire",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder='Seleziona criticita'
            ),
        )
        db.close()

        return CRITICITA
    crits = Criticità.get(Criticità.label == crit)
    crit = crits.id
    toShow = "Hai selezionato l'opzione: " + str(crit) + "\n\n"
    causae = Causa_evento.select()
    toShow += "elenco cause evento:\n\n"
    opz = []
    for i in causae:
        toShow += "ID: " + str(i.id) + "    - tipo: " + i.label + "\n"
        opz.append(i.id)
    toShow += "\nSeleziona un evento presente nella lista e invialo.\nAltrimenti clicca su /start per ricominciare o /cancel per uscire"
    reply_keyboard = [opz] #per inserimento cause visualizzo opzioni su tastiera
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Seleziona causa evento'
        ),
    )
    db.close()

    return CAUSAEVENTO

#inserimento cause
def causaevtc(update: Update, context: CallbackContext) -> int:
    global causa
    causa = update.message.text
    db.connect()
    try:
        cause = Causa_evento.get(Causa_evento.id == causa)
    except Causa_evento.DoesNotExist:
        update.message.reply_text(
            'Errore, causa non presente, riprova o clicca su /start per ricominciare o /cancel per uscire', reply_markup=ReplyKeyboardRemove()
        )
        db.close()

        return CAUSAEVENTO
    global famapp,idfamapp
    causas = Causa_evento.get(Causa_evento.id == causa)
    toShow = "Hai selezionato l'opzione: " + str(causas.label) + "\n\n"
    filtro = Famigliaapparato.get(Famigliaapparato.famiglia==famapp)
    idfamapp=filtro.id
    tipog = Tipo_guasto.select().where(Tipo_guasto.idfamiglia==idfamapp).order_by(Tipo_guasto.label.asc())
    toShow += "elenco tipologie guasto:\n\n"
    for i in tipog:
        toShow += "ID: " + str(i.id) + "    - tipo: " + i.label + "\n"
    toShow += "\nDigita l'ID di un tipo di guasto presente nella lista e invialo.\nAltrimenti clicca su /start per ricominciare o /cancel per uscire"
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()

    return TIPOGUASTO

#inserimento tipo guasto e stato ticket
def tipogtc(update: Update, context: CallbackContext) -> int:
    global tipoguasto, stato, famapp,idfamapp
    tipoguasto = update.message.text
    db.connect()

    try:
        t = Tipo_guasto.get((Tipo_guasto.id == tipoguasto) & (Tipo_guasto.idfamiglia==idfamapp))

    except Tipo_guasto.DoesNotExist:
        update.message.reply_text(
            'Errore, tipo guasto non presente, riprova o clicca su /start per ricominciare o /cancel per uscire', reply_markup=ReplyKeyboardRemove()
        )
        db.close()

        return TIPOGUASTO
    tipi = Tipo_guasto.get(Tipo_guasto.id == tipoguasto)
    toShow = "Hai selezionato l'opzione: " + str(tipi.label) + "\n\n"
    statotc = Stato.get(Stato.stato_ticket == "Aperto dal cliente")
    stato = statotc.id
    toShow += "Stato guasto: " + statotc.stato_ticket + "\n"
    # Query restituisce informazioni relative a Ticket della chiamata richiesta dell'utente
    chiam = Ticket.select().join(Chiamata, on=(Ticket.id == Chiamata.idticket)).where(Chiamata.id == msg).execute()
    # seleziono DTP corretto
    dtps = Dtp.get(Dtp.sede == dtpname)
    man=Manutentore.select().where(Manutentore.iddtp==dtps.id)
    if (man.exists()):
        toShow = "Manutentori disponibili per " + dtpname + ":\n"
        for i in man:
            toShow += "ID: " + str(i.id) + " - nome: " + i.nome + " - Telefono: " + i.numero + "\n"
        toShow += "\nScegli dalla lista l'id del manutentore per questa chiamata oppure aggiungi un nuovo manutentore schiacciando l'apposito pulsante."
        toShow +="\nAltrimenti clicca su /start per ricominciare o /cancel per uscire"
    else:
        toShow = "Non ci sono manutentori disponibili. Clicca aggiungi per inserire un nuovo manuntentore o digita /cancel per uscire\n\n"
    reply_keyboard = [['Aggiungi']]
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Aggiungi o scegli manutentore'
        ),
    )
    db.close()
    return MANUTENTORE

#inserimento nuovo manutentore nel DB oppure scelta di uno esistente
def manut(update: Update, context: CallbackContext) -> int:
    global msg
    msg = update.message.text
    if(msg=="Aggiungi"):
        toShow= "Inserire nome e cognome del nuovo manuntentore.\nAltrimenti clicca su /start per ricominciare o /cancel per uscire"
        update.message.reply_text(
            toShow,
            reply_markup=ReplyKeyboardRemove(),
        )
        return NOME_MAN
    else:
        global nome_man, numero_man
        db.connect()
        try:
            variabile = Manutentore.get(Manutentore.id == msg)
        except Manutentore.DoesNotExist:
            update.message.reply_text(
                'Errore, id non presente, riprova o clicca su /start per ricominciare o /cancel per uscire',
                reply_markup=ReplyKeyboardRemove()
            )
            db.close()
            return MANUTENTORE
        manut_scelto = Manutentore.get(Manutentore.id == msg)
        nome_man = manut_scelto.nome
        numero_man = manut_scelto.numero
        toShow = "Inserisci data e ora di inizio della chiamata nel formato dd/mm/yyyy hh:mm oppure schiaccia sul pulsante per selezionare la data e l'ora attuali.\nAltrimenti clicca su /start per ricominciare o /cancel per uscire\n"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M")
        reply_keyboard = [[dt_string]]
        update.message.reply_text(
            toShow,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder='Conferma o rifiuta'
            ),
        )
        db.close()

        return DATAORA

#inserimento nome manutentore
def nome_manut(update: Update, context: CallbackContext) -> int:
    global iddtp, nome_man
    nome_man = update.message.text
    dtp=Dtp.get(Dtp.sede==dtpname)
    iddtp=dtp.id
    toShow = "Inserire numero di telefono.\nAltrimenti clicca su /start per ricominciare o /cancel per uscire"
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    return NUMERO_MAN

#inserimento numero manutentore
def numero_manut(update: Update, context: CallbackContext) -> int:
    global numero_man
    numero_man = update.message.text
    toShow = "Digita conferma per procedere con l'inserimento del manutentore oppure rifiuta per uscire\n"
    reply_keyboard = [['Conferma', 'Rifiuta']]
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Conferma o rifiuta'
        ),
    )
    return SCELTA_MAN

#conferma inserimento manutentore
def man_conferma(update: Update, context: CallbackContext) -> int:
    msg = update.message.text
    if (msg =="Conferma"):
        manutentore= Manutentore(nome=nome_man, iddtp=iddtp, numero=numero_man)
        manutentore.save()
        toShow = "Inserisci data e ora di inizio della chiamata nel formato dd/mm/yyyy hh:mm oppure schiaccia sul pulsante per selezionare la data e l'ora attuali.\nAltrimenti clicca su /start per ricominciare o /cancel per uscire\n"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M")
        reply_keyboard = [[dt_string]]
        update.message.reply_text(
            toShow,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder='Conferma o rifiuta'
            ),
        )
        db.close()
        return DATAORA
    else:
        toShow = "Inserimento annullato\nDigita /start per ricominciare o /cancel per uscire\n"
        update.message.reply_text(
            toShow,
            reply_markup=ReplyKeyboardRemove(),
        )
        return NUOVO_MAN

# inserimento di data e ora
def ins_dataora(update: Update, context: CallbackContext) -> int:
    global dataora
    dataora = update.message.text
    toShow = "Inserisci una descrizione del problema riscontrato,\naltrimenti clicca su /start per ricominciare o /cancel per uscire"
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    return DESCRIZIONE

#inserimento descrizione
def ins_descr(update: Update, context: CallbackContext) -> int:
    global descr
    descr = update.message.text
    if(k==0):
        toShow = "Digita conferma per procedere con l'inserimento del ticket oppure rifiuta per uscire\n"
    else:
        toShow = "Digita conferma per procedere con l'inserimento della chiamata oppure rifiuta per uscire\n"
    reply_keyboard = [['Conferma', 'Rifiuta']]
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Conferma o rifiuta'
        ),
    )

    return INSERIMENTO

#opzioni per confermare o rifiutare l'inserimento
def inserttc(update: Update, context: CallbackContext) -> int:
    global ticket,guasto
    scelta = update.message.text
    if (scelta == "Conferma"):
        db.connect()
        if(k==0):
            #inserimento nella tabella ticket
            ticket = Ticket(dtp=dtpname, impianto=impname, tipo_sistema=sysname, criticita=crit, causa_evento=causa, stato=stato)
            ticket.save()
            last=Ticket.select().order_by(Ticket.id.desc()).limit(1)
            last_ticket = last.get()
            ticket=last_ticket.id
            #inserimento nella tabella guasto
            guasto = Guasto(ticket_id=last_ticket.id, locale=locname, sottosistema=macrofam, apparato=appname, tipo_guasto=tipoguasto, tipo_guasto_altro="guasto noto", famigliaapparato=famapp, stato_guasto=stato)
            guasto.save()
            last = Guasto.select().order_by(Guasto.id.desc()).limit(1)
            last_guasto = last.get()
            guasto=last_guasto.id
        #inserimento nella tabella chiamata
        chiamata = Chiamata(idticket=ticket, idguasto=guasto, manutentore=nome_man, data=dataora, descrizione=descr, numero_manutentore=numero_man)
        chiamata.save()
        last = Chiamata.select().order_by(Chiamata.id.desc()).limit(1)
        last_chiamata = last.get()
        chiamata = last_chiamata.id
        if(k==0):
            toShow = "Inserimento ticket avvenuto correttamente\n"
            toShow2 = "Riepilogo informazioni Ticket:\nID:    "+str(ticket)+"\ndtp:    "+dtpname+"\nImpianto:    " + impname+ "\nTipo_sistema:    " + sysname+ "\nCriticita:    " + str(crit)+ "\nCausa_evento:    " + str(causa) + "\nStato:    " + str(stato)
            toShow2 +="\n\nRiepilogo informazioni Guasto:\nID:    " + str(guasto) + "\nLocale:     " + locname + "\nSottosistema:    "+macrofam + "\nApparato:   " + appname + "\nTipo_guasto:   " + tipoguasto + "\nFamiglia_apparato:     " + famapp
            toShow2 +="\n\nRiepilogo informazioni Chiamata:\nID:    " + str(chiamata) + "\nManuntentore:     " + nome_man + "\nData:     " + dataora + "\nDescrizione:    " + descr + "\nNumero_manuntentore:    " + numero_man + "\n"
            toShow3 = "/start per ricominciare\n/cancel per uscire"

        else:
            info_guasto=Guasto.get(Guasto.id==guasto)
            chiamate = Chiamata.select().where(Chiamata.idticket==ticket)
            toShow = "Inserimento chiamata avvenuta correttamente\n"
            toShow2 = "ID Ticket:" +str(ticket)+"\nInformazione guasto   :\nLocale:"+ info_guasto.locale +"\nSottosistema:   "+ info_guasto.sottosistema +"\nApparato:   "+info_guasto.apparato+"\nTipo guasto:   "+ info_guasto.tipo_guasto+"\nAltro:   "  + info_guasto.tipo_guasto_altro +  "\nFamiglia apparato:  " + info_guasto.famigliaapparato + "\nStato guasto" + str(info_guasto.stato_guasto)
            toShow2 += "\n\nRiepilogo informazioni chiamate:"
            for i in chiamate:
                toShow2 += "\n\nManutentore:  " + i.manutentore + "\nData:  " + str(i.data) + "\nDescrizione:  " + i.descrizione + "\nNumero Manutentore:  " + str(i.numero_manutentore)
            toShow3 = "/start per ricominciare\n/cancel per uscire"
        update.message.reply_text(
            toShow,
            reply_markup=ReplyKeyboardRemove(),
        )
        update.message.reply_text(
            toShow2,
            reply_markup=ReplyKeyboardRemove(),
        )
        update.message.reply_text(
            toShow3,
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        toShow = "Inserimento annullato\nDigita /start per ricominciare o /cancel per uscire\n"
        update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
        )
    db.close()
    return ConversationHandler.END

#mostra gli impianti per i quali c'è almeno un guasto aperto
def filtro_imp(update: Update, context: CallbackContext) -> int:
    db.connect()
    guasti_aperti= Impianti.select().join(Ticket, on=(Impianti.impianto==Ticket.impianto)).join(Guasto, on=(Ticket.id == Guasto.ticket_id)).where((Ticket.stato==0) | (Ticket.stato==3)).group_by(Impianti.id)
    toShow = "Elenco impianti con almeno un guasto aperto:\n\n"
    for i in guasti_aperti:
        toShow += "ID: " + str(i.id) + " - impianto: " + i.impianto + "\n"
    toShow += "\nDigita un ID presente nella lista e invialo, altrimenti clicca su /start per ricominciare o /cancel per uscire"
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()
    return IMPIANTO

#deve mostrare i tipi di guasto possibili tra i guasti aperti per l'impianto appena scelto
def filtro_tg(update: Update, context: CallbackContext) -> int:
    global imp
    imp = update.message.text
    db.connect()
    controllo = Impianti.select().join(Ticket, on=(Impianti.impianto == Ticket.impianto)).join(Guasto, on=(
    Ticket.id == Guasto.ticket_id)).where(((Ticket.stato == 0) | (Ticket.stato == 3)) & (Impianti.id==imp))
    #verifico se la query di controllo è vuota
    if(not(controllo.exists())):
        update.message.reply_text(
            'Errore, id non presente, riprova o clicca su /start per ricominciare o /cancel per uscire',
            reply_markup=ReplyKeyboardRemove()
        )
        db.close()
        return IMPIANTO

    imp_scelto = Impianti.get(Impianti.id == imp)
    imp=imp_scelto.impianto
    guasti_aperti= Tipo_guasto.select().join(Guasto, on=(Guasto.tipo_guasto == Tipo_guasto.id)).join(Ticket, on=(Ticket.id == Guasto.ticket_id)).where(((Ticket.stato==0) | (Ticket.stato==3)) & (Ticket.impianto==imp)).group_by(Tipo_guasto.id)
    toShow = "Elenco tipologie guasto per le quali è presente almeno un guasto aperto:\n\n"
    for i in guasti_aperti:
        toShow += "ID: " + str(i.id) + " - tipo guasto: " + i.label + "\n"
    toShow += "\nDigita un ID presente nella lista e invialo, altrimenti clicca su /start per ricominciare o /cancel per uscire"
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()
    return TIPOGUASTO

#mostra i ticket aperti sulla base di impianto e tipo guasto
def ticket_aperti(update: Update, context: CallbackContext) -> int:
    global tg
    tg = update.message.text
    db.connect()
    ticket_aperti = Ticket.select().join(Guasto, on=(Ticket.id == Guasto.ticket_id)).where(
        ((Ticket.stato == 0) | (Ticket.stato == 3)) & (Ticket.impianto == imp) & (Guasto.tipo_guasto == tg))
    # verifico se la query di controllo è vuota
    if (not(ticket_aperti.exists())):
        update.message.reply_text(
            'Errore, id non presente, riprova o clicca su /start per ricominciare o /cancel per uscire',
            reply_markup=ReplyKeyboardRemove()
        )
        db.close()
        return IMPIANTO
    tipoguasto=Tipo_guasto.get(Tipo_guasto.id==tg)
    toShow = "Elenco ticket aperti per l'impianto " + imp + " con tipo guasto " + tipoguasto.label + ":\n\n"
    for i in ticket_aperti:
        crit=Criticità.get(Criticità.id==i.criticita)
        causaev=Causa_evento.get(Causa_evento.id==i.causa_evento)
        stato=Stato.get(Stato.id==i.stato)
        toShow += "ID: " + str(i.id) + "\nDTP: " + i.dtp + "\nTipo sistema: " + i.tipo_sistema + "\nCriticità: " + crit.label + "\nCausa_evento: " + causaev.label + "\nStato: " + stato.stato_ticket + "\n\n"
    toShow += "\nDigita un ID presente nella lista e invialo, altrimenti clicca su /start per ricominciare o /cancel per uscire"
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()
    return TICKET

def agg_chiam(update: Update, context: CallbackContext) -> int:
    global ticket, guasto
    ticket = update.message.text
    db.connect()
    riga_guasto = Guasto.get(Guasto.ticket_id==ticket)
    guasto = riga_guasto.id
    controllo = Ticket.select().join(Guasto, on=(Ticket.id == Guasto.ticket_id)).where(((Ticket.stato == 0) | (Ticket.stato == 3)) & (Ticket.impianto == imp) & (Guasto.tipo_guasto == tg) & (Ticket.id == ticket))
    # verifico se la query di controllo è vuota
    if (not(controllo.exists())):
        update.message.reply_text(
            'Errore, id non presente, riprova o clicca su /start per ricominciare o /cancel per uscire',
            reply_markup=ReplyKeyboardRemove()
        )
        db.close()
        return IMPIANTO
    toShow = "Digita conferma per procedere con l'aggiunta di una nuova chiamata oppure rifiuta per uscire\n"
    reply_keyboard = [['Conferma', 'Rifiuta']]
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Conferma o rifiuta'
        ),
    )
    db.close()
    return SCELTA

def nuova_call(update: Update, context: CallbackContext) -> int:
    global k, dtpname
    msg = update.message.text
    if(msg == "Conferma"):
        db.connect()
        k=1
        imp_scelto = Impianti.get(Impianti.impianto == imp)
        elenco = Manutentore.select().where(Manutentore.iddtp == imp_scelto.iddtp)
        dtp_scelto=Dtp.get(Dtp.id==imp_scelto.iddtp)
        dtpname = dtp_scelto.sede
        if (elenco.exists()):
            toShow = "Manutentori disponibili per " + dtpname + ":\n"
            for i in elenco:
                toShow += "ID: " + str(i.id) + " - nome: " + i.nome + " - Telefono:" + i.numero + "\n"
            toShow += "\nScegli dalla lista l'id del manutentore per questa chiamata oppure aggiungi un nuovo manutentore schiacciando l'apposito pulsante."
            toShow += "\nAltrimenti clicca su /start per ricominciare o /cancel per uscire"
        else:
            toShow = "Non ci sono manutentori disponibili. Clicca aggiungi per inserire un nuovo manuntentore."
            toShow += "\nAltrimenti clicca su /start per ricominciare o /cancel per uscire\n\n"
        reply_keyboard = [['Aggiungi']]
        update.message.reply_text(
            toShow,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder='Aggiungi o scegli manutentore'
            ),
        )
        db.close()
        return MANUTENTORE
    else:
        toShow = "Inserimento annullato\nDigita /start per ricominciare o /cancel per uscire\n"
        update.message.reply_text(
            toShow,
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
 
#terminazione della conversazione
def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    update.message.reply_text(
        'Comando cancel, termine bot', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    #gestione della conversazione ricerca con uso di stati
    conv_handlerr = ConversationHandler(
        entry_points=[CommandHandler('ricerca', scelta)],
        states={
            SCELTA: [MessageHandler(Filters.text & ~Filters.command, ricerca)],
            QRCODE: [MessageHandler(Filters.photo & ~Filters.command, qrricerca)],
            DTP: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, dtpr)],
            IMPIANTO: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, impiantor)],
            LOCALE: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, localer)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
    )
    #gestione della conversazione inserimento con uso di stati
    conv_handlertc = ConversationHandler(
        entry_points=[CommandHandler('ticketc', scelta2)],
        states={
            SCELTA: [MessageHandler(Filters.text & ~Filters.command, ricercains)],
            QRCODE: [MessageHandler(Filters.photo & ~Filters.command, qrins)],
            DTP: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, dtptc)],
            IMPIANTO: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, impiantotc)],
            LOCALE: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, localetc)],
            APPARATO: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, apparatotc)],
            CRITICITA: [MessageHandler(Filters.text & ~Filters.command, criticitatc)],
            CAUSAEVENTO: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, causaevtc)],
            TIPOGUASTO: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, tipogtc)],
            MANUTENTORE: [MessageHandler(Filters.text & ~Filters.command, manut)],
            NOME_MAN: [MessageHandler(Filters.text & ~Filters.command, nome_manut)],
            NUMERO_MAN: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, numero_manut)],
            SCELTA_MAN: [MessageHandler(Filters.text & ~Filters.command, man_conferma)],
            DATAORA: [MessageHandler(Filters.text & ~Filters.command, ins_dataora)],
            DESCRIZIONE: [MessageHandler(Filters.text & ~Filters.command, ins_descr)],
            INSERIMENTO: [MessageHandler(Filters.text & ~Filters.command, inserttc)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
    )

    #gestione della conversazione aggiungi_chiamata con uso di stati
    conv_handlerc = ConversationHandler(
        entry_points=[CommandHandler('aggiungi_chiamata', filtro_imp)],
        states={
            IMPIANTO: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, filtro_tg)],
            TIPOGUASTO: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, ticket_aperti)],
            TICKET: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, agg_chiam)],
            SCELTA: [MessageHandler(Filters.text & ~Filters.command, nuova_call)],
            MANUTENTORE: [MessageHandler(Filters.text & ~Filters.command, manut)],
            NOME_MAN: [MessageHandler(Filters.text & ~Filters.command, nome_manut)],
            NUMERO_MAN: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, numero_manut)],
            SCELTA_MAN: [MessageHandler(Filters.text & ~Filters.command, man_conferma)],
            DATAORA: [MessageHandler(Filters.text & ~Filters.command, ins_dataora)],
            DESCRIZIONE: [MessageHandler(Filters.text & ~Filters.command, ins_descr)],
            INSERIMENTO: [MessageHandler(Filters.text & ~Filters.command, inserttc)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
    )

    dispatcher.add_handler(CommandHandler("start", start))

    dispatcher.add_handler(conv_handlerr)
    dispatcher.add_handler(conv_handlertc)
    dispatcher.add_handler(conv_handlerc)

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
