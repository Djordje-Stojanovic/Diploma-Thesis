#Bewegungs_Sensor.py ist das Programm, welches für den PIR Motion Sensor geschrieben wurde.
#daraus wird die Funktion bewegungScannen() importiert.
from Bewegungs_Sensor import bewegungScannen

#DHT_Sensor ist das Programm welches für den DHT 11 Sensor geschrieben wurde.
#daraus wird die Funktion main() importiert
from DHT_Sensor import main

#Die restlichen Libraries und Frameworks werden hier importiert.
import threading
import cv2
from datetime import datetime
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
from flask import Flask, render_template, send_file, make_response, request, Response
import sqlite3

#Initialisierung der Flask App
app = Flask(__name__)

#Initialisierung der SQLite Datenbank
conn=sqlite3.connect('./Datenbank.db')
curs=conn.cursor()
 
 
def auslesenLetzterDaten():
    #Auslesen des letzten Eintrages der Datenbank, für alle drei Spalten,
    #durch den SQLite Query. Der LIMIT Befehl limitiert das Auslesen auf einen Eintrag,
    #somit wird nicht die komplette Tabelle ausgelesen, sondern nur die letzte Reihe.
    for spalte in curs.execute("SELECT * FROM Daten_Tabelle ORDER BY zeit DESC LIMIT 1"):
        zeit = str(spalte[0])
        temperatur = spalte[1]
        luftfeuchtigkeit = spalte[2]

    #Anschließendes Zurückgeben der Daten.
    return zeit, temperatur, luftfeuchtigkeit
 
 
def auslesenHistorischerDaten(anzahlAbtastungen):
    #Es werden historische Daten ausgelesen. 
    #"+str(anzahlAbtastungen))" bestimmt dabei wieviele Reihen (zeitlich
    #absteigend) insgesamt ausgelesen werden.
    curs.execute("SELECT * FROM Daten_Tabelle ORDER BY zeit DESC LIMIT "
        +str(anzahlAbtastungen))
        
    #alle ausgelesenen Daten werden auf die Variable daten zwischengespeichert.
    daten = curs.fetchall()
    
    #Initialisierung von Listen für die jeweiligen Spalten der Datentabelle.
    zeiten = []
    temperaturen = []
    luftfeuchtigkeiten = []
    
    #Befüllen der Listen mit ausgelesenen Daten.
    for spalte in reversed(daten):
        zeiten.append(spalte[0])
        temperaturen.append(spalte[1])
        luftfeuchtigkeiten.append(spalte[2])
        
        #Prüfung, ob sich die Werte im gewünschten Bereich befinden.
        temperaturen, luftfeuchtigkeiten = pruefeGrenzen(temperaturen, luftfeuchtigkeiten)
    
    #Rückgabe der Werte.
    return zeiten, temperaturen, luftfeuchtigkeiten
 
 
def pruefeGrenzen(temperaturen, luftfeuchtigkeiten):
    #Es wird die Länge der Liste "temperaturen" geholt.
    laenge = len(temperaturen)
    
    #Anschließend wird jeder Temperatur- und Luftfeuchtigkeitswert auf
    #die gewünschten Bereiche geprüft.
    #Für Temperatur: 0°C bis 50°C, da dies der Bereich ist, in dem der
    #DHT 11 Sensor noch einigermaßen plausible Werte messen kann.
    #Für Luftfeuchtigkeit werden alle Werte zwischen 0% und 100% 
    #als plausibel angenommen.
    
    #Sollten die Werte sich im ungewünschten Bereich befinden, so wird
    #dies als Messfehler interpretiert und der Messwert wird auf den, in der
    #Datenbank vorherigen Messwert gesetzt.
    
    #Dies dient zur Garantierung, dass auch bei Messfehlern ein sauberes 
    #grafisches Monitoring durchgeführt werden kann.
    for i in range(0, laenge-1):
        if (temperaturen[i] < 0 or temperaturen[i] >50):
            temperaturen[i] = temperaturen[i-1]
        if (luftfeuchtigkeiten[i] < 0 or luftfeuchtigkeiten[i] >100):
            luftfeuchtigkeiten[i] = luftfeuchtigkeiten[i-1]
    
    #Zuletzt erfolgt noch eine Rückgabe der Werte.
    return temperaturen, luftfeuchtigkeiten
   
   
def anzahlReihen():
    #Für die Temperaturspalte wird nachgezählt, wieviele Einträge vorhanden sind.
    for spalte in curs.execute("select COUNT(temperatur) from  Daten_Tabelle"):
        #Dies wird in die Variable reihenAnzahl eingeschrieben.
        reihenAnzahl=spalte[0]
        
    #Anschließend wird die Variable zurückgegeben.
    return reihenAnzahl
   
 
def abtastungsPeriode():
    #Mit der, in Listing 13, erklärten Funktion werden historische Daten ausgelesen.
    zeiten, temperaturen, luftfeuchtigkeiten = auslesenHistorischerDaten (2)
    
    #Anschließend wird die Variable "zeiteinheit" initialisiert.
    zeiteinheit = '%Y-%m-%d %H:%M:%S'
    
    #Periode 0 und Periode 1 werden definiert und anschließend voneinander subtrahiert.
    periode0 = datetime.strptime(zeiten[0], zeiteinheit)
    periode1 = datetime.strptime(zeiten[1], zeiteinheit)
    abtastung = periode1-periode0
    
    #Die Abtastungsperiode wird auf Sekunden heruntergerechnet und zurückgegeben.
    abtastung = int(round(abtastung.total_seconds()/60))
    return (abtastung)
   
 
#Es wird geprüft, ob bereits 60 oder mehr Einträge in der Datenbank vorhanden sind.
#Falls dies zutrifft, wird diese Variable auf 60 gesetzt.
global anzahlAbtastungen
anzahlAbtastungen = anzahlReihen()
if (anzahlAbtastungen >= 60):
    anzahlAbtastungen = 60
 
#Die Abtastungsperiode wird, mithilfe der in Listing 15
#implementierten Funktion, initialisiert.
global abtastungsPerioden
abtastungsPerioden = abtastungsPeriode()
 
#Dies ist die Variable, welche bestimmt, wieviele historische Werte ausgelesen
#und anschließend grafisch dargestellt werden.
global anzahlGeforderterWerte
anzahlGeforderterWerte = 15


 #Erstellen des Programmthreads
programmThread = threading.Thread(target = main)
#Flask Initialisierung der Front-Page.
@app.route("/")
def index():
    #Auslesen der letzten gemessenen Daten mittels auslesenLetzterDaten(),
    #siehe Listing 11.
    zeit, temperatur, luftfeuchtigkeit = auslesenLetzterDaten()
    
    #Erstellen einer Variable "datenVorlage" zur Datenausgabe.
    #datenVorlage wird dabei mit den vorher geholten Werten befüllt.
    datenVorlage = {
        'zeit' : zeit,
        'temperatur' : temperatur,
        'luftfeuchtigkeit' : luftfeuchtigkeit,
        'abtastung' : abtastungsPerioden,
        'anzahlGeforderterWerte' : anzahlGeforderterWerte
    }
    
    #Abfrage, ob Programmthread schon läuft. Falls nicht, wird dieser gestartet.
    if not programmThread.is_alive():
        programmThread.start()
        
    #Rendern der HTML-Page und Übergabe von "datenVorlage" an die HTML-Page. 
    return render_template('index.html', **datenVorlage)
 
 #Diese Funktion verwendet die HTTP-POST Methode. Die Methode dient dazu,
#Daten an den Server zu senden beziehungsweise die Webseite zu aktualisieren.
@app.route('/', methods=['POST'])
def my_form_post():
    #Initialisierung der bereits globalisierten verfügbaren Variablen
    global anzahlAbtastungen 
    global abtastungsPerioden
    global anzahlGeforderterWerte
    
    #Auslesen der, vom User geforderten, Anzahl an darzustellender historischen Werte.
    anzahlGeforderterWerte = int (request.form['anzahlGeforderterWerte'])
    
    #Wenn die Abtastungsperiode des DHT Sensors 2 Minuten ist und der User
    #als "anzahlGeforderterWerte" 1 eingibt entsteht ein Fehler. Dieser wird hier
    #behoben beziehungsweise wird es hiermit verhindert.
    if (anzahlGeforderterWerte < abtastungsPerioden):
        anzahlGeforderterWerte = abtastungsPerioden + 1
        
    #Errechnung der Anzahl der Abtastungen auf Basis der geforderten Werte
    #und der realen abtastungsPeriode des DHT 11 Sensors.
    anzahlAbtastungen = anzahlGeforderterWerte//abtastungsPerioden
    numMaxPerioden = anzahlReihen()
    
    #Schutz vor dem Fall, dass der User mehr Werte darstellen will, als in der
    #Datenbank verfügbar.
    if (anzahlAbtastungen > numMaxPerioden):
        anzahlAbtastungen = (numMaxPerioden-1)
    
    #Auslesen letzter Daten
    zeit, temperatur, luftfeuchtigkeit = auslesenLetzterDaten()
    
    #Erstellen einer Datenvorlage für das Frontend
    datenVorlage = {
        'zeit' : zeit,
        'temperatur' : temperatur,
        'luftfeuchtigkeit' : luftfeuchtigkeit,
        'abtastung' : abtastungsPerioden,
        'anzahlGeforderterWerte' : anzahlGeforderterWerte
    }
    
    #Rendern der HTML-Page und Übergabe von "datenVorlage" an die HTML-Page. 
    return render_template('index.html', **datenVorlage)
   
 
#Diese Funktion erstellt eine PNG-Datei beziehungsweise ein Abbild eines, in Matplotlib
#erstellten, Temperaturdiagrammes.
@app.route('/plot/temperaturdiagramm')
def tempearturdiagramm():
    #Auslesen und Initialisieren historischer Daten aus der Datenbank.
    zeiten, temperaturen, luftfeuchtigkeiten = auslesenHistorischerDaten(anzahlAbtastungen)
    
    #Konfiguration des zu erstellenden Diagrammes.
    ys = temperaturen
    fig = Figure(facecolor="#181818")
    axis = fig.add_subplot(1, 1, 1, axisbg='#181818')
    axis.spines['top'].set_color('white')
    axis.spines['bottom'].set_color('white')
    axis.spines['left'].set_color('white')
    axis.spines['right'].set_color('white')
    axis.set_title("Temperatur [°C]", color = 'white')
    axis.set_xlabel("Zeit", color = 'white')
    axis.set_ylabel("Temperatur", color = 'white')
    axis.tick_params(axis='x', colors='white')
    axis.tick_params(axis='y', colors='white')
    axis.grid(True)
    
    #Beifügen der Zeitachse (x-Achse) zum Diagramm.
    zeit = []
    for l in zeiten:
        zeit.append(".".join(l.split(" ")[1].split(":")[slice(2)]))
    xs = zeit
    
    #Plotten beziehungsweise Erstellen des Diagrammes.
    axis.plot(xs, ys, linewidth = 5)
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    
    #Rückgabe des Diagrammes an den Webserver
    ausgabe = make_response(output.getvalue())
    ausgabe.mimetype = 'image/png'
    return ausgabee
 
 
#Diese Funktion erstellt eine PNG-Datei beziehungsweise ein Abbild eines in Matplotlib
#erstellten Luftfeuchtigkeitsdiagrammes.
@app.route('/plot/luftfeuchtigkeitsdiagramm')
def luftfeuchtigkeitsdiagramm():
    #Auslesen und Initialisieren historischer Daten aus der Datenbank.
    zeiten, temperaturen, luftfeuchtigkeiten = auslesenHistorischerDaten(anzahlAbtastungen)
    
    #Konfiguration des zu erstellenden Diagrammes.
    ys = luftfeuchtigkeiten
    fig = Figure(facecolor="#181818")
    axis = fig.add_subplot(1, 1, 1, axisbg="#181818")
    axis.spines['top'].set_color('white')
    axis.spines['bottom'].set_color('white')
    axis.spines['left'].set_color('white')
    axis.spines['right'].set_color('white')
    axis.set_title("Luftfeuchtigkeit [%]", color = 'white')
    axis.set_xlabel("Zeit", color = 'white')
    axis.set_ylabel("Luftfeuchtigkeit", color = 'white')
    axis.tick_params(axis='x', colors='white')
    axis.tick_params(axis='y', colors='white')
    axis.grid(True)
    
    #Beifügen der Zeitachse (x-Achse) zum Diagramm.
    zeit = []
    for l in zeiten:
        zeit.append(".".join(l.split(" ")[1].split(":")[slice(2)]))
    xs = zeit
    
    #Plotten beziehungsweise Erstellen des Diagrammes.
    axis.plot(xs, ys, linewidth = 5)
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    
    #Rückgabe des Diagrammes an den Webserver
    ausgabe = make_response(output.getvalue())
    ausgabe.mimetype = 'image/png'
    return ausgabe
   

#Diese Funktion updated die Kamera-Seite.
@app.route('/kamera')
def kameraseiteUpdaten():
    return render_template('kamera.html')
 
 
def kameraGenerator():
    #Starten der Kamera
    kameraAufnahme = cv2.VideoCapture(0)
    
    #Die Kamera soll dauerhaft Bilder aufnehmen.
    while True:
        #Aufnahme des Frames
        ret, frame = kameraAufnahme.read()
        
        #Spiegelung des Frames, um das Kameraproblem zu beheben beziehungsweise zu umgehen.
        frameMirror = cv2.rotate(frame, cv2.ROTATE_180)
        
        #Einbinden des Motionsensors in das Bild.
        frameMirror = cv2.putText(frameMirror, bewegungScannen(),(50,50),cv2
            .FONT_HERSHEY_SIMPLEX, 1,(0,0,0), 1, cv2.LINE_AA, False)
        
        #Komprimieren des Frames und vorläufiges Lagern im Memory Buffer.
        ret, frameMirror = cv2.imencode('.jpeg',frameMirror)
        
        #Rückgabe des Generators.
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frameMirror.tobytes() + b'\r\n')
 

@app.route('/liveuebertragung')
def liveuebertragung():
    #Rückgabe der Antwort der "kameraGenerator()" Funktion als Frame.
    return Response(kameraGenerator(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    try:
        #cert.pem und key.pem werden eingebunden
        #Als Host wird 0.0.0.0. konfiguriert.
        #Als Port wird 443 verwendet.
        app.run(ssl_context=('cert.pem', 'key.pem'), host='0.0.0.0', port=443, debug=False)
        
    #Ausgeben von exceptions, um Prozesse besser nachvollziehen zu können.    
    except Exception as e:
        print(e)
