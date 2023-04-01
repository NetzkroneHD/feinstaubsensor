# Feinstaubsensor-Daten - Pflichtenheft

## Inhalt:
1. Informationen
   1. Allgemeine Informationen
   2. Technische Informationen
2. Rahmenbedingungen
3. Anforderungsbeschreibung des Kunden
4. Anlagen

## 1. Informationen

### Allgemeine Informationen:
* Name des Projekts: Feinstaubsensor-Datenanalyse
* Projektleiter und Teammitglieder:
  * Noah Fabian Aloé
* Datum der Erstellung des Pflichtenhefts: 01.04.23

### Technische Informationen:
* Verwendung von sqlite3 als Datenbank-Management-System
  * muss in Python mit der sqlite3-Bibliothek erstellt werden.
  * muss in der Lage sein, Feinstaubsensordaten zu speichern und abzurufen.
* Verwendung des Wasserfallmodells als Projektmanagement-Methodik
* Das Projekt wird in fünf Phasen unterteilt: Anforderungsanalyse, Entwurf, Implementierung, Test und Wartung.
* Verwendung von Python als Programmiersprache

## 2. Rahmenbedingungen
### Zeitliche Bedingungen:
* Projektstart: 23.01.2023
* Projektende: 15.04.2023
* Arbeitszeiten: Jeden Montag 90 Minuten

## 3. Anforderungsbeschreibung des Kunden
* Datenbeschaffung von Feinstaubsensordaten:
  * Die Daten werden über die [Sensor-Community-API](https://sensor.community/de/) abgerufen.

* Daten aufbereiten:
  * Die Daten müssen bereinigt und auf offensichtliche Fehler geprüft werden.
  * Die Daten müssen in geeigneten Formaten (min, max, Durchschnitt usw.) aufbereitet werden.

* Daten in Datenbank (sqlite3) speichern:
   * Die Daten müssen in der Datenbank mithilfe der sqlite3-Bibliothek gespeichert werden.
   * Die Datenbank muss in der Lage sein, eine große Anzahl von Daten effizient zu speichern und abzurufen.

* Offensichtliche Fehlerdaten ausmerzen:
  * Die Lösung muss in der Lage sein, offensichtliche Fehlerdaten automatisch oder manuell zu erkennen und auszumerzen.

* Visualisierung der Daten in Form von Graphen:
  * Die Lösung muss in der Lage sein, die Daten in Graphen darzustellen, um Trends und Muster zu identifizieren.
  * Die Graphen müssen interaktiv sein, um eine detaillierte Analyse zu ermöglichen.

* Benutzeroberfläche (GUI) zur einfachen Bedienung der Lösung:
  * Die Lösung muss eine grafische Benutzeroberfläche (GUI) bereitstellen, um die Interaktion mit der Lösung zu erleichtern.
  * Die GUI muss einfach zu bedienen und intuitiv sein.

## 4. Anlagen

# 