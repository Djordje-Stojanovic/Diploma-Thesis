import time
import sqlite3
import Adafruit_DHT

dbname='Datenbank.db'
sampleFreq = 2 # in sekunden


def datenAuslesen():
        #Parameter 1 der folgenden Funktion, "Adafruit_DHT.DHT11" ruft den DHT11 Sensor auf
        #Parameter 2 der folgenden Funktion, "16" steht für den GPIO 16 beziehungsweise
        #Pin 36 des Raspberry Pi
	luftfeuchtigkeit, temperatur = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, 16)
	
	#wenn Werte ausgelesen werden konnten,
	#wird datenSpeichern() und datenAnzeigen() aufgerufen.
	if luftfeuchtigkeit is not None and temperatur is not None:
		luftfeuchtigkeit = round(luftfeuchtigkeit)
		temperatur = round(temperatur, 1)
		datenSpeichern (temperatur, luftfeuchtigkeit)
		datenAnzeigen()	


def datenSpeichern (temperatur, luftfeuchtigkeit):

        #Es wird eine Verbindung zur SQLite Datenbank hergestellt.
	conn=sqlite3.connect('Datenbank.db')
	curs=conn.cursor()
	
	#Anschließend werden, die über Parameter übergebenen Daten, mittels
	#INSERT INTO Befehl in die SQLite Datenbank eingespeichert.
	curs.execute("INSERT INTO Daten_Tabelle values(datetime('now','localtime'), 
	(?), (?))", (temperatur, luftfeuchtigkeit))
	
	#Die Transaktion wird nun beendet.
	conn.commit()
	conn.close()	

	
def datenAnzeigen():
    #Es wird eine Verbindung zur SQLite Datenbank hergestellt.
    conn = sqlite3.connect('Datenbank.db')
    curs = conn.cursor()
    
    #Anschließend werden die Werte mittels SELECT Befehl aus der Tabelle geholt
    #und dann mittels print Befehl ausgegeben.
    for row in curs.execute("SELECT * FROM Daten_Tabelle ORDER BY zeit DESC LIMIT 1"):
        zeit = str(row[0])
        temperatur = row[1]
        luftfeuchtigkeit = row[2]
    print(zeit,temperatur,luftfeuchtigkeit)


#Bei Ausführung der Main-Funktion wird in Dauerschleife
#datenAuslesen() aufgerufen. Dabei wird eine Zeitverzögerung von 60 sekunden
#eingebaut. Diese ist dazu da, um die gewünschte Messfrequenz von einer Messung
#pro Minute zu liefern.
def main():
	while True:
                datenAuslesen()
                time.sleep(60)




