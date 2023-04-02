from __future__ import annotations

import csv
import datetime
import functools
import os
import sqlite3
import threading

import requests

from pathlib import Path


def create_cache_dir():
    """
    Erstellt einen Ordner namens "cache", sofern dieser noch nicht existiert.
    """
    try:
        os.mkdir("cache/sensors")
        print("Cache folder was created.")
    except FileExistsError:
        print("Cache folder already exists.")


# https://archive.sensor.community/2022/2022-01-01/2022-01-01_bme280_sensor_113.csv
sensor_archive_format = "https://archive.sensor.community/%year%/%date%/%date%_%sensor_type%_sensor_%id%.csv"
sensor_archive_format_indoor = "https://archive.sensor.community/%year%/%date%/%date%_%sensor_type%_sensor_%id%_indoor.csv"

# https://archive.sensor.community/2023-01-01/2023-01-01_bme280_sensor_113.csv
sensor_archive_format_current_year = "https://archive.sensor.community/%date%/%date%_%sensor_type%_sensor_%id%.csv"
sensor_archive_format_indoor_current_year = "https://archive.sensor.community/%date%/%date%_%sensor_type%_sensor_%id%_indoor.csv"

date_format = "%Y-%m-%dT%H:%M:%S"

create_cache_dir()
database_connection = sqlite3.connect("./cache/database.db", check_same_thread=False)

sensor_id_cache: set[int] = set()


@functools.total_ordering
class SensorData:
    def __init__(self, timestamp: datetime.datetime, value: str, value_name: str, sensor_id: int):
        super().__init__()
        self.value = value
        self.value_name = value_name
        self.timestamp = timestamp
        self.sensor_id = sensor_id

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, SensorData):
            return False
        return self.timestamp == o.timestamp and self.value == o.value and self.value_name == o.value_name and self.sensor_id == o.sensor_id

    def __hash__(self):
        return id(self)

    def __lt__(self, other):
        if other == self:
            return True
        if not isinstance(other, SensorData):
            return False
        return self.timestamp.__lt__(other.timestamp)

    def __str__(self):
        return f"(timestamp={self.timestamp}, value={self.value}, value_name={self.value_name}, sensor_id={self.sensor_id})"


class Sensor:
    def __init__(self, id: int, type: str, lat: float, lon: float, indoor: int, load_data=True):
        super().__init__()
        self.id = id
        self.type = type
        self.lat = lat
        self.lon = lon
        self.indoor = indoor
        self.sensor_data: list[SensorData] = []
        if load_data:
            self.load_data()
        else:
            self.sensor_data: list[SensorData] = []
            self.maximum: dict[str, set: SensorData] = {}
            self.minimum: dict[str, set: SensorData] = {}
            self.average: dict[str, set: SensorData] = {}

    def load_data(self):
        """
        Lädt Daten, sortiert sie und berechnet das Maximum, das Minimum und den Durchschnitt.
        """
        self.sensor_data = self.sort_data()
        self.maximum = self.calc_maximum()
        self.minimum = self.calc_minimum()
        self.average = self.calc_avg()

    def sort_data(self) -> dict[str, list[SensorData]]:
        """
        Lädt die Sensor-Daten in der Reihenfolge des Datums.
        """
        sorted_data = {}
        res = database_connection.execute(f"SELECT * FROM data WHERE sensor_id=? ORDER BY `time`", [self.id])
        for row in res:
            if sorted_data.get(row[2]) is None:
                sorted_data[row[2]] = []
            sorted_data.get(row[2]).append(SensorData(datetime.datetime.fromisoformat(row[0]), row[3], row[2], row[1]))
        return sorted_data

    def calc_maximum(self) -> dict[str, set: SensorData]:
        """
        Lädt alle maximalen Werte der Sensor-Daten.
        """
        maximum = {}
        res = database_connection.execute(
            f"SELECT *, MAX(CAST(value AS FLOAT)) as max, strftime(?, time) as month "
            f"FROM data "
            f"WHERE sensor_id=? AND value <> '' "
            f"AND value IS NOT 'nan' "
            f"GROUP BY month, value_name;", (get_setting("sql_date"), self.id)).fetchall()

        for row in res:
            if maximum.get(row[2]) is None:
                maximum[row[2]] = set()
            maximum[row[2]].add(SensorData(datetime.datetime.fromisoformat(row[0]), row[3], row[2], row[1]))
        return maximum

    def calc_minimum(self) -> dict[str, set: SensorData]:
        """
        Lädt alle minimalen Werte der Sensor-Daten.
        """
        minimum = {}
        res = database_connection.execute(
            f"SELECT *, MIN(CAST(value AS FLOAT)) as min, strftime(?, time) as month "
            f"FROM data "
            f"WHERE sensor_id=? AND value <> '' "
            f"AND value IS NOT 'nan' "
            f"GROUP BY month, value_name;", (get_setting("sql_date"), self.id)).fetchall()

        for row in res:
            if minimum.get(row[2]) is None:
                minimum[row[2]] = set()
            minimum[row[2]].add(SensorData(datetime.datetime.fromisoformat(row[0]), row[3], row[2], row[1]))
        return minimum

    def calc_avg(self) -> dict[str, set: SensorData]:
        """
        Lädt die durchschnittlichen Sensor-Daten.
        """
        avg = {}
        res = database_connection.execute(
            f"SELECT *, AVG(CAST(value AS FLOAT)) as avg, strftime(?, time) as month "
            f"FROM data "
            f"WHERE sensor_id=? AND value <> '' "
            f"AND value IS NOT 'nan' "
            f"GROUP BY month, value_name;", (get_setting("sql_date"), self.id)).fetchall()
        for row in res:
            if avg.get(row[2]) is None:
                avg[row[2]] = set()
            avg[row[2]].add(SensorData(datetime.datetime.fromisoformat(row[0]), row[4], row[2], row[1]))
        return avg

    def __str__(self):
        return f"(id={self.id} type={self.type}, lat={self.lat}, lon={self.lon}, indoor={self.indoor}, sensor_data={self.sensor_data}, sensor_data={self.sensor_data}, maximum={self.maximum}, minimum={self.minimum}, average={self.average})"


def create_tables():
    """
    Legt die Tabellen für die Datenbank an, wenn sie noch nicht existieren, und fügt einige Standardwerte hinzu
    """
    database_connection.execute(
        "CREATE TABLE IF NOT EXISTS sensor_type(sensor_id INTEGER, sensor_type TEXT, indoor INT, PRIMARY KEY (sensor_id))")

    database_connection.execute(
        "CREATE TABLE IF NOT EXISTS sensor(id INT PRIMARY KEY, lat INT, lon INT, FOREIGN KEY (id) REFERENCES sensor_type(sensor_id))")

    database_connection.execute(
        "CREATE TABLE IF NOT EXISTS data(`time` DATE, sensor_id INT, value_name TEXT, value TEXT, "
        "PRIMARY KEY (`time`, sensor_id, value_name), "
        "FOREIGN KEY (sensor_id) REFERENCES sensor(id));")

    database_connection.execute("CREATE TABLE IF NOT EXISTS sensor_search_types(type TEXT, PRIMARY KEY (type))")

    database_connection.execute("CREATE TABLE IF NOT EXISTS gui_settings(name TEXT, value TEXT, PRIMARY KEY (name))")

    database_connection.execute("INSERT OR IGNORE INTO gui_settings(name, value) VALUES "
                                "('linestyle', 'solid'), "
                                "('sql_date', '%Y-%m')")

    database_connection.execute("INSERT OR IGNORE INTO sensor_search_types (type) VALUES "
                                "('sds011'), "
                                "('bme280'), "
                                "('dht22'), "
                                "('htu21d'), "
                                "('sds021'), "
                                "('bmp280'), "
                                "('sps30'), "
                                "('dnms (laerm)'), "
                                "('sht31'), "
                                "('bmp180')")

    database_connection.commit()


def import_sensor_types():
    """
    Importiert Sensor-Typen von den sensor.community-API und speichert sie in einer Datenbanktabelle
    """
    print("Importing Sensor types...")
    r = requests.get("https://data.sensor.community/static/v2/data.json")
    json = r.json()
    for key in json:
        try:
            name = key["sensor"]["sensor_type"]["name"].lower().replace(" ", "_")
            id = int(key["sensor"]["id"])
            indoor = key["location"]["indoor"]
            database_connection.execute(f"INSERT OR IGNORE INTO sensor_search_types(type) VALUES ('{name}')")
            database_connection.execute("INSERT OR IGNORE INTO sensor_type(sensor_id, sensor_type, indoor) "
                                        "VALUES (?, ?, ?)",
                                        (id, name, indoor))
        except AttributeError or ValueError:
            pass
    database_connection.commit()
    print("Imported Sensor types.")


def get_date_range_year(year: int) -> list[datetime.date]:
    """
    Gibt eine Liste von Datumsobjekten zurück, die alle Tage des angegebenen Jahres enthalten.
    Falls das Jahr das aktuelle Jahr ist, wird der letzte Tag durch den heutigen Tag ersetzt.
    """
    int(year)
    first_day = datetime.datetime(year=year, month=1, day=1)
    last_day = datetime.datetime(year=year, month=12, day=31)

    if first_day.year == datetime.datetime.now().year:
        last_day = datetime.datetime.now()
    return get_date_range(first_day, last_day)


def get_date_range(from_time: datetime.datetime, to_time: datetime.datetime) -> list[datetime]:
    """
    Gibt eine Liste aller Daten zwischen zwei gegebenen Datumsobjekten zurück.
    """
    date_list = []

    for i in range(int((to_time - from_time).days) + 1):
        date_list.append(from_time + datetime.timedelta(days=i))

    return date_list


def get_csv_dump(date: datetime.date, sensor_type: str, sensor_id: int, indoor: int):
    """
    Lädt eine CSV-Datei aus dem Cache-Ordner, wenn diese existiert oder vom Server herunter und gibt den Inhalt als csv.reader zurück.
    Der Dateiname setzt sich aus Datum, Sensortyp und Sensor-ID zusammen.
    """
    filename = "cache/sensors/" + ("%date%_%sensor_type%_sensor_%id%" + ["", "_indoor"][indoor > 0] + ".csv") \
        .replace("%date%", date.strftime("%Y-%m-%d")) \
        .replace("%sensor_type%", sensor_type) \
        .replace("%id%", str(sensor_id))

    if Path(filename).exists():
        return csv.reader(open(filename, 'r'), dialect='excel')

    if date.year == datetime.datetime.now().year:
        url = ([sensor_archive_format_current_year, sensor_archive_format_indoor_current_year][indoor > 0])
    else:
        url = ([sensor_archive_format, sensor_archive_format_indoor][indoor > 0])
    url = url.replace("%year%", date.strftime("%Y")).replace("%date%", date.strftime("%Y-%m-%d")).replace(
        "%sensor_type%", sensor_type).replace("%id%", str(sensor_id))
    response = requests.get(url)
    if not response.ok:
        return

    file = open(filename, 'wb')
    file.write(response.content)
    file.close()

    return csv.reader(open(filename, 'r'), dialect='excel')


def clear_cache(clear_all: bool = False):
    """
    Löscht alle Dateien im Ordner "cache".
    Wenn das Argument clear_all auf True gesetzt ist,
    werden auch alle Daten aus der Datenbank gelöscht.
    """

    print("Clearing cache...")
    g = os.scandir("./cache/sensors")
    for t in g:
        if t.name.endswith(".csv"):
            os.remove(t)
    print("Cache folder was cleared.")

    if clear_all:
        database_connection.execute("DELETE FROM sensor")
        database_connection.execute("DELETE FROM data")
        database_connection.execute("DELETE FROM sensor_type")
        database_connection.commit()
        print("Database was cleared.")


def load_sensor_cache():
    """
    Leert den Sensor-Cache und füllt ihn mit den IDs der in der Datenbank vorhandenen Sensoren
    """
    sensor_id_cache.clear()
    for id in database_connection.execute("SELECT id FROM sensor").fetchall():
        sensor_id_cache.add(id[0])
    print(f"sensor_id_cache: {sensor_id_cache}")


def percentage(g: float, w: float) -> float:
    """
    Brechnet das Verhältnis von w zu g und gibt das Ergebnis als float zurück
    """
    return float(w) / float(g)


def exists_in_database(id: int) -> bool:
    """
    Prüft, ob ein Sensor bereits in der Datenbank existiert.
    """
    int(id)
    return len(database_connection.execute(f"SELECT id FROM sensor WHERE id=?", [id]).fetchall()) > 0


def get_sensor_types() -> set[str]:
    """
    Gibt ein Set von Sensor-Typen zurück,
    die in der Datenbank gespeichert sind.
    """
    types = set()
    res = database_connection.execute("SELECT DISTINCT (type) FROM sensor_search_types ORDER BY type").fetchall()
    for row in res:
        types.add(row[0])
    return types


def has_data_in_year(id: int, year: int) -> bool:
    """
    überprüft, ob ein Sensor mit einer bestimmten ID im angegebenen Jahr Daten hat und gibt True zurück,
    wenn Daten vorhanden sind, andernfalls False.
    """
    int(id)
    int(year)
    return len(database_connection.execute("SELECT sensor_id FROM data WHERE "
                                           f"date(`time`) >= date('{year}-01-01') AND date(`time`) <= date('{year}-12-31') "
                                           f"AND sensor_id={id}").fetchall()) > 0


def save_in_database(sid):
    """
    Speichert ein Sensor- oder Sensor-Daten-Objekt in der Datenbank.
    Wenn es sich um ein SensorData-Objekt handelt, werden der Zeitstempel,
    der Wertname, der Wert und die Sensor-ID in die data-Tabelle eingefügt.

    Wenn es sich um ein Sensor-Objekt handelt, werden die Sensor-ID, der Sensortyp,
    die Koordinaten und die Indoor-Eigenschaft in die sensor_type- und sensor-Tabellen eingefügt.
    Die Sensor-Daten werden ebenfalls in die data-Tabelle eingefügt.
    """

    if isinstance(sid, SensorData):
        database_connection.execute("INSERT OR IGNORE INTO data(`time`, value_name, value, sensor_id) VALUES "
                                    "(?, ?, ?, ?)",
                                    (sid.timestamp, sid.value_name, sid.value, sid.sensor_id))
    elif isinstance(sid, Sensor):
        database_connection.execute("INSERT OR IGNORE INTO sensor_type(sensor_id, sensor_type, indoor) VALUES "
                                    "(?, ?, ?)",
                                    (sid.id, sid.type.lower(), sid.indoor))

        database_connection.execute("INSERT OR IGNORE INTO sensor(id, lat, lon) VALUES "
                                    "(?, ?, ?)",
                                    (sid.id, sid.lat, sid.lon))
        for sd in sid.sensor_data:
            database_connection.execute("INSERT OR IGNORE INTO data(`time`, value_name, value, sensor_id) VALUES "
                                        "(?, ?, ?, ?)",
                                        (sd.timestamp, sd.value_name, sd.value, sd.sensor_id))

    else:
        return
    database_connection.commit()


def get_sensor(id: int) -> Sensor | None:
    """
    Ruft die Informationen eines Sensors mit einer bestimmten Sensor-ID aus einer Datenbank ab.
    Wenn der Sensor in der Datenbank vorhanden ist, wird ein Sensor-Objekt mit der entsprechenden Sensor-ID,
    dem Sensor-Typ, den Koordinaten und der Indoor-Eigenschaft erstellt und zurückgegeben.
    Andernfalls gibt die Funktion None zurück.
    """
    if exists_in_database(id):
        print(f"Loading sensor '{id}' from database...")
        rs = database_connection.execute(
            f"SELECT sensor.id, sensor_type.sensor_type, sensor.lat, sensor.lon, sensor_type.indoor "
            f"FROM sensor "
            f"INNER JOIN sensor_type on sensor.id = sensor_type.sensor_id "
            f"WHERE id=?", [id]).fetchone()

        sensor = Sensor(id, rs[1], rs[2], rs[3], rs[4])
        print(f"Loaded sensor '{id}' from database.")
        return sensor
    return None


def load_sensor_data(year: int, sensor_type: str, sensor_id: int, indoor: int, callback=None) -> Sensor:
    """
    Lädt die Sensor-Daten für einen bestimmten Sensor-Typ und eine Sensor-ID für das angegebene Jahr.
    Sie ruft eine CSV-Datei ab, verarbeitet die Daten und speichert sie als Sensor-Objekt ab.
    Die Funktion gibt das Sensor-Objekt zurück.
    Ein Fortschritts-Callback kann optional angegeben werden.
    """
    dr = get_date_range_year(year)
    drl = len(dr)
    i = 0

    data_list: list[SensorData] = []
    sensor = Sensor(sensor_id, "type", 0, 0, indoor, load_data=False)

    # w=g*p
    for i, d in enumerate(dr):
        if callback is not None:
            callback(percentage(drl, i), drl, i)
        cvs_reader = get_csv_dump(d, sensor_type, sensor_id, indoor)

        if cvs_reader is None:
            continue

        value_names = {}

        for cvs_i, row in enumerate(cvs_reader):
            if cvs_i == 0:
                values = row[0].split(";")
                for vi, v in enumerate(values):
                    value_names[vi] = v
            else:
                vi = 0
                splitted = row[0].split(";")

                sensor.type = splitted[1]
                sensor.lat = float(splitted[3])
                sensor.lon = float(splitted[4])
                for vi, value in enumerate(splitted):
                    if vi >= 6:
                        data_list.append(
                            SensorData(datetime.datetime.strptime(splitted[5], date_format), value, value_names[vi],
                                       sensor_id))
    sensor.sensor_data = data_list

    if callback is not None:
        callback(1, drl, i)
    return sensor


def delete_from_database(sensor_id: int):
    print(f"Deleting '{sensor_id}' from database...")
    int(sensor_id)
    database_connection.execute(f"DELETE FROM data WHERE sensor_id=?", [sensor_id])
    database_connection.execute(f"DELETE FROM sensor WHERE id=?", [sensor_id])
    database_connection.commit()
    print(f"Deleted '{sensor_id}' from database.")


def is_indoor(sensor_id: int) -> int | None:
    """
    überprüft anhand einer Sensor-ID, ob es sich um einen Indoor- oder Outdoor-Sensor handelt.
    Die Funktion greift auf eine Datenbankverbindung zu und führt eine SQL-Abfrage auf der Tabelle sensor_type aus,
    um die Indoor- oder Outdoor-Eigenschaft des Sensors zu ermitteln.
    Die Funktion gibt als Ergebnis entweder 1 für Indoor, 0 für Outdoor oder None zurück,
    wenn die Sensor-ID in der Datenbank nicht gefunden wurde oder es ein Problem mit der Datenbankverbindung gibt.
    """
    int(sensor_id)
    res = database_connection.execute(f"SELECT indoor FROM sensor_type WHERE sensor_id=?", [sensor_id]).fetchone()
    if res is None:
        return None
    elif res[0] == 1:
        return 1
    elif res[0] == 0:
        return 0
    return None


def find_sensor_type(sensor_id: int, year: int, indoor: int) -> str | None:
    """
    Sucht den Typ eines Sensors anhand seiner ID, Jahres und Innen- / Außenanwendung.
    Falls der Typ in der Datenbank existiert, wird dieser zurückgegeben.
    Ansonsten wird für das angegebene Jahr nach passenden Sensor-Typen gesucht,
    indem CSV-Dateien ausgelesen und auf den Sensor hin geprüft werden.
    Wird ein passender Typ gefunden, wird dieser in die Datenbank eingetragen und zurückgegeben.
    Andernfalls wird None zurückgegeben.
    """

    int(year)
    int(sensor_id)
    int(indoor)

    res = database_connection.execute(f"SELECT sensor_type FROM sensor_type WHERE sensor_id=?", [sensor_id]).fetchone()
    if res is not None:
        return res[0]

    dr = get_date_range_year(year)
    types = database_connection.execute("SELECT type FROM sensor_search_types").fetchall()

    for d in dr:
        for typ in types:
            cvs_reader = get_csv_dump(d, typ[0], sensor_id, indoor)
            if cvs_reader is not None:
                typ_name = typ[0].lower()
                database_connection.execute("INSERT OR IGNORE INTO sensor_type(sensor_id, sensor_type, indoor) VALUES "
                                            "(?, ?, ?)",
                                            (sensor_id, typ_name, indoor))
                database_connection.commit()
                return typ[0]
    return None


def check_connection(timeout: int) -> True:
    try:
        requests.get("http://www.google.com/", timeout=timeout, allow_redirects=True)
        return True
    except requests.exceptions.RequestException:
        return False


def get_setting(name: str):
    return database_connection.execute("SELECT value FROM gui_settings WHERE lower(name)=?", [name.lower()]).fetchone()[
        0]


def set_setting(name: str, value: str):
    database_connection.execute("UPDATE gui_settings SET value=? WHERE name=?", (value, name.lower()))
    database_connection.commit()


create_tables()

load_sensor_cache()
thread = threading.Thread(target=import_sensor_types)
thread.start()
