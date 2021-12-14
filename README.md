# Alstom-bot
Prerequisiti
Su Windows installare python versione 3.9 cercando “python 3.9” su Microsoft store, con questo comando viene installato anche il pacchetto pip.
Su Linux usare comando:
sudo apt install python3

installare peewee con comando:
pip install peewee

installare pacchetti telegram con comando:
pip install python-telegram-bot

installare pacchetto per lettura qr code con comando:
pip install opencv-python

installare pacchetto per gestione delle immagini con comando:
pip install pillow

installare pacchetto per data e ora con comando:
pip install datetime


Se si hanno dei problemi di conflitto con altre librerie presenti nella macchina si può creare e utilizzare un virtualenv.
Configurazione bot
Modificare la stringa di connessione al database, presente alla riga 27 alla voce 
db=connect(mysql://root:Password1234@localhost:3306/prova)

la stringa deve avere il seguente formato: 	        mysql://nomeutente:password@host:port/nomedatabase
Per la creazione e configurazione di un nuovo bot:
andare al seguente link:Telegram: Contact @BotFather
lanciare il comando : /newbot
inserire nome e successivamente l’username (che deve terminare con bot  per esempio: TetrisBot or tetris_bot)
salvare token univoco generato e inserirlo alla riga 28 del codice (token=".....")
Configurazione peewee
Ciascuna tabella di cui il bot fa utilizzo dev’essere dichiarata come classe prevedendo l’iniziale maiuscola (es. da riga 30 a 150 circa), tutti i campi che saranno utilizzati vanno dichiarati all’interno di ciascuna classe con il loro formato (noi abbiamo utilizzato le tabelle ridotte che ci avete fornito, mentre per voi risulta necessario adattarlo modificando i vari oggetti di database in modo che corrispondano a quelli presenti realmente sul db).
Esecuzione del bot
Per eseguire il bot lanciare il comando: 
python3 nomefile.py

