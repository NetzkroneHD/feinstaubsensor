# Feinstaubsensor-Daten - Lastenheft

## Inhalt:
1. Präambel
   1. Empfängerkreis
   2. Projektbeschreibung
2. Projektkonzept
3. Definition des Anforderungsprofil


## 1. Präambel

### Empfängerkreis:
1. Der Kunde
2. Das Projektteam
3. Jeder Stakeholder, der an der Lösung interessiert ist

### Projektbeschreibung:
Ziel des Projekts ist es eine Lösung zu bieten, mit der er die Daten der [Sensor-Community-API](https://sensor.community/de/) herunterladen, aufbereiten und darstellen kann.  
Die Lösung umfasst die folgenden Aspekte:

* **PM-Modell:** Das passende Projektmanagement-Modell (PM-Modell) wird ausgewählt und angewendet.
* **Download der Daten:** Es wird eine automatisierte Lösung bereitgestellt, um die Daten vom Feinstaubsensor herunterzuladen.
* **Datenbank:** Die aufbereiteten Daten werden in einer Datenbank gespeichert. Es kann zwischen sqlite3 oder mariadb/mysql ausgewählt werden.
* **Datenbereinigung:** Offensichtliche Fehlerdaten werden aus den Daten entfernt.
* **Datenanalyse:** Die aufbereiteten Daten werden analysiert, indem Statistiken wie Minimum, Maximum und Durchschnitt berechnet werden.
* **(G)UI-User-Interface:** Es wird eine grafische Benutzeroberfläche (GUI) entwickelt, die eine intuitive und benutzerfreundliche Möglichkeit bietet, auf die Daten zuzugreifen. Die GUI wird mit Python entwickelt.
* **Grafische Darstellung:** Die Daten werden in einem Graphen dargestellt, um sie visuell ansprechender zu machen und dem Kunden A eine einfache Möglichkeit zu bieten, Trends und Muster in den Daten zu erkennen.

Das Projektteam soll eng mit dem Kunden zusammenarbeiten, um sicherzustellen, dass die Lösung seinen Anforderungen entspricht.  
Der Projektfortschritt wird regelmäßig mit dem Kunden kommuniziert und Feedback wird berücksichtigt, um sicherzustellen, dass die Lösung den Erwartungen des Kunden entspricht.  
Das Projekt wird in einer angemessenen Zeit abgeschlossen sein und dem Kunden eine voll funktionsfähige Lösung zur Verfügung stellen, um die Feinstaubsensordaten herunterzuladen, aufzubereiten und darzustellen.

## 2. Projektkonzept

### Zielsetzung:
Die Lösung soll eine automatisierte Möglichkeit bereitstellen, um die Daten vom Feinstaubsensor herunterzuladen und eine Datenbank bereitstellen,  
in der die aufbereiteten Daten gespeichert werden können.  
Die Daten sollen bereinigt und analysiert werden, indem Statistiken wie Minimum, Maximum und Durchschnitt berechnet werden.  
Die Lösung soll eine benutzerfreundliche grafische Benutzeroberfläche (GUI) enthalten, die eine einfache und intuitive Möglichkeit bietet,  
auf die Daten zuzugreifen und sie visuell darzustellen. Die Lösung soll in der Sprache Python entwickelt werden und innerhalb einer angemessenen Zeit abgeschlossen sein.

## 3. Definition des Anforderungsprofil

### Anforderungsprofil:
1. **Download der Dateien und Daten:** Die Lösung muss in der Lage sein, Daten vom Feinstaubsensor automatisch herunterzuladen und zu speichern.
2. **PM-Modell wählen und verwenden:** Ein geeignetes PM-Modell (Projektmanagement-Modell) muss ausgewählt werden, um den Projektfortschritt zu planen und zu überwachen. 
3. **Abspeichern in Datenbank:** Die Lösung muss eine Datenbank bereitstellen, in der die aufbereiteten Daten des Feinstaubsensors gespeichert werden können. Zwei Datenbank-Optionen sollen in Betracht gezogen werden: sqlite3 und mariadb/mysql. 
4. **Offensichtliche Fehlerdaten ausmerzen:** Die Lösung muss in der Lage sein, offensichtliche Fehlerdaten aus den heruntergeladenen Daten zu identifizieren und zu bereinigen. 
5. **Aufbereitung:** Die Lösung muss in der Lage sein, statistische Analysen der Feinstaubdaten durchzuführen, einschließlich Minimum, Maximum, Durchschnitt usw.
6. **(G)UI User Interface:** Die Lösung muss eine benutzerfreundliche grafische Benutzeroberfläche (GUI) enthalten, die eine einfache und intuitive Möglichkeit bietet, auf die Daten zuzugreifen und sie visuell darzustellen. 
7. **Darstellung als Graph:** Die Lösung muss in der Lage sein, die aufbereiteten Daten des Feinstaubsensors in Form von Diagrammen und Grafiken darzustellen, um sie visuell ansprechend und verständlich zu machen. 
8. **Sprache Python:** Die Lösung muss in der Programmiersprache Python entwickelt werden. 
9. **Dokumentation:** Die Lösung muss vollständig dokumentiert werden, einschließlich einer Beschreibung der Funktionalitäten, der Datenbank-Struktur und der technischen Details. 
10. **Zeitrahmen:** Die Lösung muss innerhalb eines bestimmten Zeitrahmens abgeschlossen werden. 
11. **Kommunikation:** Regelmäßige Kommunikation und Feedback über den Projektfortschritt sind erforderlich, um sicherzustellen, dass die Lösung den Anforderungen des Kunden entspricht.