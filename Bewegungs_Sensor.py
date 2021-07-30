import RPi.GPIO as GPIO
import time 

#Es wird der Raspberry Pi Pin 16 (GPIO 23) konfiguriert
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(16, GPIO.IN)
    
def bewegungScannen():
	#wenn Bewegung stattfindet gibt dies Funktion "Bewegung" zurück,
	#ansonsten gibt diese Funktion "Keine Bewegung" zurück.
	if ((GPIO.input(16)==1):                 
	    return "Bewegung"
	else:
            return "Keine Bewegung"
