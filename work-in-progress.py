#!/usr/bin/env python
# pylint: disable=C0116,W0613
import json
import logging, os
import mysql.connector
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


# dichiaro variabili globali per ricerca e inserimento
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

# dichiaro nomi degli stati che serviranno per il conversation handler
DTP, IMPIANTO, QRCODE, LOCALE, APPARATO, CRITICITA, CAUSAEVENTO, TIPOGUASTO, INSERIMENTO , CHIAMATA, MANUTENTORE, DATAORA, DESCRIZIONE, UPDATE = range(14)
SCELTA= range(1)

# funzione start con menu di riepilogo
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Usa /ricerca per ricercare degli apparati e i loro dettagli.\n"
        "Usa /ticketc per creare un nuovo ticket cliente.\n"
        "Usa /inserimento_manutentore per assegnare un manutentore ad una chiamata.\n"
        "Usa --- da fare"
    )

def scelta(update: Update, context: CallbackContext) -> int:
    toShow = "Scegliere se inserire campi manualmente o tramite QR Code\n"
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
        toShow += "\nDigita un ID presente nella lista e invialo. \nDigita nuovamente /start se vuoi ricominciare."
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

# scelta dtp e visualizzazione risultati
def dtpr(update: Update, context: CallbackContext) -> int:
    global msg

    msg = update.message.text
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
    toShow = "Impianti disponibili:\n\n"
    for impianto in impianti:
        toShow += "ID: " + str(impianto.id) + " - impianto: " + impianto.impianto + "\n"
    toShow += "\nDigita un ID presente nella lista e invialo."
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
            'Errore, id non presente, riprova o clicca su /start per ricominciare', reply_markup=ReplyKeyboardRemove()
        )
        db.close()

        return IMPIANTO
    locali = Locale.select().join(Impianti, on=(Impianti.id == Locale.idimpianto)) \
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


# scelta locale e visualizzazione risultati
def localer(update: Update, context: CallbackContext) -> int:
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
    data,_,_ = qrDecoder.detectAndDecode(inputImage)
    res= format(data)
    os.remove('qrcode.png')
    try:
    	load=json.loads(res)
    except:
    	update.message.reply_text(
            'Errore, riprova o clicca su /ricerca per ricominciare', reply_markup=ReplyKeyboardRemove()
        );return QRCODE       
    db.connect()
    try:
        loc = Locale.get((Locale.iddtp == load["iddtp"]) & (Locale.idimpianto == load["idimpianto"]) & (Locale.id == load["idlocale"]))
    except Locale.DoesNotExist:
        update.message.reply_text(
            'Errore, id non presente, riprova o clicca su /ricerca per ricominciare', reply_markup=ReplyKeyboardRemove()
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
# bot ricerca
def ricercains(update: Update, context: CallbackContext) -> int:
    db.connect()
    dtps = Dtp.select()
    toShow = "DTP disponibili:\n\n"
    for dtp in dtps:
        toShow += "ID: " + str(dtp.id) + " - sede: " + dtp.sede + "\n"
    toShow += "\nDigita un ID presente nella lista e invialo. \nDigita nuovamente /start se vuoi ricominciare."
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()
    return DTP

# inserimento dtp e visualizzazione risultati
def dtptc(update: Update, context: CallbackContext) -> int:
    global dtp
    dtp = update.message.text
    db.connect()
    try:
        dtps = Dtp.get(Dtp.id == dtp)
    except Dtp.DoesNotExist:
        update.message.reply_text(
            'Errore, id non presente, riprova o clicca su /start per ricominciare', reply_markup=ReplyKeyboardRemove()
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
    toShow += "\nDigita un ID presente nella lista e invialo."
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
            'Errore, id non presente, riprova o clicca su /start per ricominciare', reply_markup=ReplyKeyboardRemove()
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
    toShow += "\nTipo sistema: " + sysname + "\nDigita un ID presente nella lista e invialo."
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
            'Errore, id non presente, riprova o clicca su /start per ricominciare', reply_markup=ReplyKeyboardRemove()
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
    toShow += "\nDigita un ID presente nella lista e invialo."
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
            'Errore, id non presente, riprova o clicca su /start per ricominciare', reply_markup=ReplyKeyboardRemove()
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
    toShow += "\nSchiaccia il pulsante corrispondente"
    reply_keyboard = [opz] #per inserimento criticità visualizzo opzioni su tastiera
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
            "Errore, criticità non presente, riprova o clicca su /start per ricominciare",
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
    toShow += "\nSeleziona un evento presente nella lista e invialo."
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
            'Errore, causa non presente, riprova o clicca su /start per ricominciare', reply_markup=ReplyKeyboardRemove()
        )
        db.close()

        return CAUSAEVENTO
    causas = Causa_evento.get(Causa_evento.id == causa)
    toShow = "Hai selezionato l'opzione: " + str(causas.label) + "\n\n"
    tipog = Tipo_guasto.select().order_by(Tipo_guasto.label.asc())
    toShow += "elenco tipologie guasto:\n\n"
    for i in tipog:
        toShow += "ID: " + str(i.id) + "    - tipo: " + i.label + "\n"
    toShow += "\nDigita un tipo di guasto presente nella lista e invialo."
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()

    return TIPOGUASTO

#inserimento tipo guasto e stato ticket
def tipogtc(update: Update, context: CallbackContext) -> int:
    global tipoguasto, stato
    tipoguasto = update.message.text
    db.connect()
    try:
        t = Tipo_guasto.get(Tipo_guasto.id == tipoguasto)
    except Tipo_guasto.DoesNotExist:
        update.message.reply_text(
            'Errore, tipo guasto non presente, riprova o clicca su /start per ricominciare', reply_markup=ReplyKeyboardRemove()
        )
        db.close()

        return TIPOGUASTO
    tipi = Tipo_guasto.get(Tipo_guasto.id == tipoguasto)
    toShow = "Hai selezionato l'opzione: " + str(tipi.label) + "\n\n"
    statotc = Stato.get(Stato.stato_ticket == "Aperto dal cliente")
    stato = statotc.id
    toShow += "Stato guasto: " + statotc.stato_ticket + "\n"
    toShow += "Digita conferma per procedere con l'inserimento del ticket oppure rifiuta per uscire\n"
    reply_keyboard = [['Conferma', 'Rifiuta']]
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Conferma o rifiuta'
        ),
    )
    db.close()

    return INSERIMENTO

#opzioni per confermare o rifiutare l'inserimento
def inserttc(update: Update, context: CallbackContext) -> int:
    scelta = update.message.text
    if (scelta == "Conferma"):
        db.connect()
        #inserimento nella tabella ticket
        ticket = Ticket(dtp=dtpname, impianto=impname, tipo_sistema=sysname, criticita=crit, causa_evento=causa, stato=stato)
        ticket.save();
        last=Ticket.select().order_by(Ticket.id.desc()).limit(1)
        last_ticket = last.get()
        #inserimento nella tabella guasto
        guasto = Guasto(ticket_id=last_ticket.id, locale=locname, sottosistema=macrofam, apparato=appname, tipo_guasto=tipoguasto, tipo_guasto_altro="guasto noto", famigliaapparato=famapp, stato_guasto=stato)
        guasto.save()
        #inserimento nella tabella chiamata
        chiamata = Chiamata(idticket=last_ticket.id, idguasto=guasto.id)
        chiamata.save()
        toShow = "Inserimento ticket avvenuto correttamente\nDigita /start per ricominciare\n"
    else:
        toShow = "Inserimento annullato\nDigita /start per ricominciare\n"
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()
    return ConversationHandler.END

# comando per successivo inserimento manutentore
# funzione per selezionare chiamate attualmente senza manutentore
def rchiamata(update: Update, context: CallbackContext) -> int:
    db.connect()
    chiamata = Chiamata.select().where((Chiamata.manutentore.is_null())|(Chiamata.manutentore=="")).order_by(Chiamata.id.desc())
    toShow = "Chiamate attive:\n\n"
    for i in chiamata:
        toShow += "ID: " + str(i.id) + " - Descrizione: " + i.descrizione + "\n"
    toShow += "\nDigita un ID presente nella lista e invialo. \nDigita nuovamente /start se vuoi ricominciare."
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )

    db.close()

    return CHIAMATA

# funzione per cercare i manutentori disponibili per il dtp del ticket relativo alla chiamata
def ric_man(update: Update, context: CallbackContext) -> int:
    global msg
    msg = update.message.text
    db.connect()
    try:
        variabile = Chiamata.get(Chiamata.id == msg)
    except Chiamata.DoesNotExist:
        update.message.reply_text(
            'Errore, id non presente, riprova o clicca su /start per ricominciare', reply_markup=ReplyKeyboardRemove()
        )
        db.close()

        return CHIAMATA
    # Query restituisce informazioni relative a Ticket della chiamata richiesta dell'utente
    chiam=Ticket.select().join(Chiamata, on=(Ticket.id==Chiamata.idticket)).where(Chiamata.id==msg).execute()
    sededtp=""
    for i in chiam:
        sededtp = i.dtp
    if(sededtp==""):
    	toShow = "Non ci sono manutentori disponibili\n\n"
    	update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    	)
    	db.close()
    	return ConversationHandler.END
    # ottenuta riga dtp relativo alla chiamata scelta dell'utente
    dtps=Dtp.get(Dtp.sede==sededtp)
    man= Manutentore.select().where(Manutentore.iddtp==dtps.id)
    toShow = "Manutentori disponibili:\n\n"
    for i in man:
        toShow += "ID: " + str(i.id) + " - nome: " + i.nome + " - Telefono:"+ i.numero +"\n"
    toShow += "\nScegli dalla lista l'id del manutentore per questa chiamata"
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()

    return MANUTENTORE

# inserimento del manutentore scelto dall'utente
def ins_man(update: Update, context: CallbackContext) -> int:
    global nome_man,numero_man
    msg = update.message.text
    db.connect()
    try:
        variabile = Manutentore.get(Manutentore.id == msg)
    except Manutentore.DoesNotExist:
        update.message.reply_text(
            'Errore, id non presente, riprova o clicca su /start per ricominciare', reply_markup=ReplyKeyboardRemove()
        )
        db.close()

        return MANUTENTORE
    manut_scelto = Manutentore.get(Manutentore.id == msg)
    nome_man = manut_scelto.nome
    numero_man = manut_scelto.numero
    toShow = "Inserisci data e ora di inizio della chiamata nel formato dd/mm/yyyy hh:mm oppure schiaccia sul pulsante per selezionare la data e l'ora attuali\n"
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

# inserimento di data e ora
def ins_dataora(update: Update, context: CallbackContext) -> int:
    global dataora
    dataora = update.message.text
    toShow = "Inserisci una descrizione del problema riscontrato\n"
    update.message.reply_text(
        toShow,        
        reply_markup=ReplyKeyboardRemove(),
    )
    return DESCRIZIONE

#inserimento descrizione
def ins_descr(update: Update, context: CallbackContext) -> int:
    global descr
    descr = update.message.text
    toShow = "Digita conferma per procedere con l'inserimento del ticket oppure rifiuta per uscire\n"
    reply_keyboard = [['Conferma', 'Rifiuta']]
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Conferma o rifiuta'
        ),
    )
    return UPDATE

#opzioni per confermare o rifiutare l'update della chiamata con le nuove informazioni inserite
def update_chiam(update: Update, context: CallbackContext) -> int:
    scelta = update.message.text
    if (scelta == "Conferma"):
        db.connect()
        #update della tabella chiamata
        var=Chiamata.update(manutentore=nome_man, numero_manutentore=numero_man, data=dataora, descrizione=descr).where(Chiamata.id==msg)
        var.execute()
        toShow = "Aggiornamento chiamata avvenuto correttamente\nDigita /start per ricominciare\n"
    else:
        toShow = "Aggiornamento annullato\nDigita /start per ricominciare\n"
    update.message.reply_text(
        toShow,
        reply_markup=ReplyKeyboardRemove(),
    )
    db.close()
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
    updater = Updater("1999421296:AAEyNoV8fpxrUwKzihFGbUx26oyzYe9yLwA")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    #gestione della conversazione ricerca con uso di stati
    conv_handlerr = ConversationHandler(
        entry_points=[CommandHandler('ricerca', scelta)],
        states={
            SCELTA:[MessageHandler(Filters.text & ~Filters.command, ricerca)],
            QRCODE: [MessageHandler(Filters.photo & ~Filters.command, qrricerca)],
            DTP: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, dtpr)],
            IMPIANTO: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, impiantor)],
            LOCALE: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, localer)],

        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
    )
    #gestione della conversazione inserimento con uso di stati
    conv_handlertc = ConversationHandler(
        entry_points=[CommandHandler('ticketc', ricercains)],
        states={
            DTP: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, dtptc)],
            IMPIANTO: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, impiantotc)],
            LOCALE: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, localetc)],
            APPARATO: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, apparatotc)],
            CRITICITA: [MessageHandler(Filters.text & ~Filters.command, criticitatc)],
            CAUSAEVENTO: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, causaevtc)],
            TIPOGUASTO: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, tipogtc)],
            INSERIMENTO: [MessageHandler(Filters.text & ~Filters.command, inserttc)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
    )
    #gestione conversazione per inserimento voci manutentore
    conv_handlerm = ConversationHandler(
        entry_points=[CommandHandler('inserimento_manutentore', rchiamata)],
        states={
            CHIAMATA: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, ric_man)],
            MANUTENTORE: [MessageHandler(Filters.regex('^[0-9]*$') & ~Filters.command, ins_man)],
            DATAORA: [MessageHandler(Filters.text & ~Filters.command, ins_dataora)],
            DESCRIZIONE: [MessageHandler(Filters.text & ~Filters.command, ins_descr)],
            UPDATE: [MessageHandler(Filters.text & ~Filters.command, update_chiam)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
    )

    dispatcher.add_handler(CommandHandler("start", start))

    dispatcher.add_handler(conv_handlerr)
    dispatcher.add_handler(conv_handlertc)
    dispatcher.add_handler(conv_handlerm)

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()