from __future__ import annotations

import ctypes
import datetime
import enum
import threading
import time
import tkinter as tk
import tkinter.ttk as ttk

import matplotlib
from pathlib import Path

import requests
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from tkinter import messagebox

import sensor_data
from sensor_data import Sensor

empty_cache = 0

sensor_search_timeout = 60
sensor_thread_timeout = 5

# Erstellt ein Fenster mit einer MessageBox
def message_box(title: str, text: str, style: int):
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    if style == 0:  # Information
        messagebox.showinfo(title, text)
    elif style == 1:  # Warning
        messagebox.showwarning(title, text)
    elif style == 2:  # Error
        messagebox.showerror(title, text)
    root.destroy()


# Repräsentiert den Status des Download-prozesses
class DownloadState(enum.Enum):
    NONE = 0
    SEARCHING_TYPE = 1
    DOWNLOADING = 2
    SAVING_IN_DATABASE = 3
    LOADING_GRAPH = 4
    CLEARING_CACHE = 5


class SensorSettings(tk.Toplevel):
    def __init__(self, sensor_selector: SensorSelector, master=None, **kw):
        super(SensorSettings, self).__init__(master, **kw)

        self.selector: SensorSelector = sensor_selector

        self.linestyle_label = tk.Label(self)
        self.linestyle_label.configure(justify="center", text='Liniensytle:')
        self.linestyle_label.grid(column=0, row=0, sticky="w")

        self.linestyle_var = tk.StringVar()
        self.linestyle_var.set(sensor_data.get_setting("linestyle"))

        __values = ['solid', 'dotted', 'dashed', 'dashdot']
        self.linestyle_option = tk.OptionMenu(
            self, self.linestyle_var, *__values, command=self.linestyle_callback)
        self.linestyle_option.grid(column=2, row=0)

        self.sort_label = tk.Label(self)
        self.sort_label.configure(justify="center", text='Sortieren nach:')
        self.sort_label.grid(column=0, row=1, sticky="w")

        self.sort_var = tk.StringVar()
        self.sort_var.set(sensor_data.get_setting("sql_date"))

        __values = ["%Y", "%Y-%m", "%Y-%m-%d", "%Y-%m-%d %H"]
        self.sort_option = tk.OptionMenu(
            self, self.sort_var, *__values, command=self.sort_callback)

        self.sort_option.grid(column=2, row=1)

        self.ok_btn = tk.Button(self)
        self.ok_btn.configure(text='Ok')
        self.ok_btn.grid(column=0, row=3, sticky="w")
        self.ok_btn.configure(command=self.ok_callback)

        self.configure(takefocus=True, width=250)
        self.grid()
        self.grid_anchor("center")

    def destroy(self) -> None:
        self.selector.settings_gui = None
        super().destroy()

    def ok_callback(self):
        self.destroy()

    def linestyle_callback(self, option):
        sensor_data.set_setting("linestyle", option)
        pass

    def sort_callback(self, option):
        sensor_data.set_setting("sql_date", option)
        pass


# Das Frame, was für die Download-Anzeige zuständig ist
class SensorDownloader(tk.Frame):
    def __init__(self, sensor_selector: SensorSelector, master=None, show_cancel=False, **kw):
        super(SensorDownloader, self).__init__(master, **kw)
        self.sensor_selector = sensor_selector

        self.title = tk.Label(self)
        self.title.configure(text='Downloading...')
        self.title.pack(anchor="center", expand=True, fill="x", side="top")

        self.progressbar = ttk.Progressbar(self)
        self.progressbar.configure(orient="horizontal")
        self.progressbar.pack(
            anchor="center",
            expand=True,
            fill="x",
            side="top")

        if show_cancel:
            self.cancel_btn = tk.Button(self)
            self.cancel_btn.configure(text='Abbrechen')
            self.cancel_btn.pack(anchor="center", expand=True, side="top")
            self.cancel_btn.configure(command=self.cancel_callback)

        self.configure(takefocus=True, width=250)
        self.pack(side="top")
        self.grid_anchor("center")

    def cancel_callback(self):
        self.cancel_download()

    def cancel_download(self):
        if self.sensor_selector.downloading.value.numerator == 1 or self.sensor_selector.downloading.value.numerator == 2:
            self.sensor_selector.check_thread.join(timeout=0)
            self.sensor_selector.download_thread.join(timeout=0)
            self.sensor_selector.downloading = DownloadState.NONE
            self.finished()
            message_box("Download", "Download wurde erfolgreich abgebrochen", 0)
            pass
        else:
            message_box("Download", "Der download konnte nicht abgebrochen werden.", 0)
            pass

    # Führt die Download-Anzeige aus
    def download(self, p: float, g: float, w: float, title=None):
        if title is None:
            self.title.configure(text=f"Herunterladen ({(int(p * 100))}%)...")
        else:
            self.title.configure(text=title)

        self.title.update()

        self.progressbar.configure(maximum=g, value=w)
        self.progressbar.update()

    # Zerstört die Download-Anzeige
    def finished(self):
        self.pack_forget()
        self.sensor_selector.downloading = DownloadState.NONE


class GraphToolbar(NavigationToolbar2Tk):

    def __init__(self, canvas, window=None, *, pack_toolbar=True):
        super().__init__(canvas, window, pack_toolbar=pack_toolbar)

    def set_message(self, s):
        pass


# Dieses Frame ist für die Darstellung der Daten zuständig
class SensorGraph(tk.Frame):
    def __init__(self, sensor: Sensor, master=None, **kw):
        super(SensorGraph, self).__init__(master, **kw)
        self.sensor: Sensor = sensor

        self.graph_frame = tk.Frame(self)
        self.graph_frame.configure(height=100, width=300)
        self.graph_frame.grid(row=0, column=0)

        self.configure(height=100, takefocus=True, width=300)
        self.place(anchor="nw", x=0, y=0)

    # Zeigt die Daten eines Sensors aus einem Jahr
    def show_data(self, loader: SensorDownloader):
        print(f"Showing data for {self.sensor.id}...")
        i = 0
        max_i = len(self.sensor.maximum.keys()) + len(self.sensor.minimum.keys()) + len(self.sensor.average.keys())
        column = 0
        row = 0
        for i, key in enumerate(self.sensor.maximum.keys()):
            loader.download(sensor_data.percentage(max_i, i), max_i, i, f"Lade Graf für Daten '{key}'...")
            y_label = key

            x_axis = []
            y_axis_min: list[float] = []
            y_axis_max: list[float] = []
            y_axis_avg: list[float] = []

            print(f"Plotting for {y_label}...")

            sql_date_format = sensor_data.get_setting("sql_date")

            for y_min in sorted(self.sensor.minimum[key]):
                x_axis.append(y_min.timestamp.strftime(sql_date_format))
                y_axis_min.append(float(y_min.value))

            for y_max in sorted(self.sensor.maximum[key]):
                y_axis_max.append(float(y_max.value))

            for y_avg in sorted(self.sensor.average[key]):
                y_axis_avg.append(float(y_avg.value))

            self._show_plot(x_axis, y_axis_min, y_axis_avg, y_axis_max, y_label, column, row)
            if row == 2:
                column += 1
                row = 0
            else:
                row += 2

        loader.download(sensor_data.percentage(max_i, i), max_i, i, f"Fertigstellen...")
        pass

    # Erstellt den Graphen
    def _show_plot(self, x_axis: list[float], y_axis_min: list[float], y_axis_avg: list[float], y_axis_max: list[float],
                   y_label: str, column: int, row: int):
        fig = Figure(figsize=(5, 4), dpi=65)

        subplt: matplotlib.axes = fig.add_subplot(111)

        line_style = sensor_data.get_setting("linestyle")

        # Max
        subplt.plot(x_axis, y_axis_max, linestyle=line_style, color="red", label="max")
        # Avg
        subplt.plot(x_axis, y_axis_avg, linestyle=line_style, color="black", label="Ø")
        # Min
        subplt.plot(x_axis, y_axis_min, linestyle=line_style, color="green", label="min")

        subplt.legend(loc="upper left")

        subplt.grid()

        subplt.set_title(y_label)

        fig.add_gridspec(4, 4)

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=row, column=column)

        toolbar = GraphToolbar(canvas, self.graph_frame, pack_toolbar=False)
        toolbar.update()
        toolbar.grid(row=row + 1, column=column)

        print(f"Showed for {y_label}")


# Ist für die Auswahl der Sensoren zuständig
class SensorSelector(tk.Frame):
    def __init__(self, sensor_id_cache: set[int], master=None, **kw):
        super(SensorSelector, self).__init__(master, **kw)
        self.check_thread: threading.Thread | None = None

        self.downloading: DownloadState = DownloadState.NONE
        self.graph: SensorGraph | None = None
        self.download_thread: threading.Thread | None = None

        self.sensor_id_label = tk.Label(self)
        self.sensor_id_label.configure(anchor="center", text="Sensor ID*:")
        self.sensor_id_label.grid(column=0, row=0, sticky="w")

        self.sensor_id_entry = tk.Entry(self)
        self.sensor_id_entry.grid(column=1, row=0)

        self.sensor_option_label = tk.Label(self)
        self.sensor_option_label.configure(
            anchor="center", text="Sensor Cache:")
        self.sensor_option_label.grid(column=0, row=4, sticky="w")

        self.sensor_id_cache = sensor_id_cache
        if len(self.sensor_id_cache) == 0:
            self.sensor_id_cache.add(empty_cache)

        self.sensor_cache_option_var = tk.StringVar()
        self.sensor_cache_option = tk.OptionMenu(
            self, self.sensor_cache_option_var, *self.sensor_id_cache, command=self.option_callback)
        self.sensor_cache_option.grid(column=1, row=4)

        self.load_btn = tk.Button(self)
        self.load_btn.configure(anchor="center", text="Sensor auswählen")
        self.load_btn.grid(column=0, row=6)
        self.load_btn.bind("<ButtonPress>", self.select_callback, add="")

        self.clear_cache_btn = tk.Button(self)
        self.clear_cache_btn.configure(anchor="center", text="Cache leeren")
        self.clear_cache_btn.grid(column=2, row=6)
        self.clear_cache_btn.bind(
            "<ButtonPress>",
            self.clear_cache_callback,
            add="")

        self.clear_all_check = tk.Checkbutton(self)
        self.clear_all_checked = tk.BooleanVar(value=False)
        self.clear_all_check.configure(
            anchor="center",
            text="Alles leeren",
            variable=self.clear_all_checked)
        self.clear_all_check.grid(column=2, row=4)

        self.sensor_type_label = tk.Label(self)
        self.sensor_type_label.configure(anchor="center", text="Sensor Typ:")
        self.sensor_type_label.grid(column=0, row=2, sticky="w")

        self.sensor_type_entry = tk.Entry(self)
        self.sensor_type_entry.grid(column=1, row=2)

        self.year_label = tk.Label(self)
        self.year_label.configure(anchor="center", text="Jahr*:")
        self.year_label.grid(column=0, row=3, sticky="w")
        self.year_entry = tk.Entry(self)
        self.year_entry.grid(column=1, row=3)

        self.sync_btn = tk.Button(self)
        self.sync_btn.configure(text="Sensor Syncen")
        self.sync_btn.grid(column=1, row=6)
        self.sync_btn.bind("<ButtonPress>", self.sync_callback, add="")

        self.info_label = tk.Label(self)
        self.info_label.configure(text="*: Pflichtfelder")
        self.info_label.grid(column=2, row=0)

        self.indoor_check_btn = tk.Checkbutton(self)
        self.indoor_value = tk.IntVar()
        self.indoor_check_btn.configure(
            text='Indoor', variable=self.indoor_value)
        self.indoor_check_btn.grid(column=2, row=3)

        self.type_cache = tk.StringVar()
        self.type_cache_option = tk.OptionMenu(
            self, self.type_cache, *sensor_data.get_sensor_types(), command=self.type_cache_callback)
        self.type_cache_option.grid(column=2, row=2)

        self.settings_btn = tk.Button(self)
        self.img_settings = tk.PhotoImage(file="./cache/Settings16x16.png")
        self.settings_btn.configure(image=self.img_settings)
        self.settings_btn.grid(column=3, row=0, sticky="w")
        self.settings_btn.configure(command=self.settings_callback)

        self.settings_gui: SensorSettings | None = None

        self.configure(height=80, takefocus=True, width=310)
        self.grid(column=0, row=0)

    def settings_callback(self):
        if self.settings_gui is None:
            self.settings_gui = SensorSettings(self, root)
            self.settings_gui.wm_iconphoto(False, ImageTk.PhotoImage(Image.open("./cache/favicon.png")))
            self.settings_gui.title = "Einstellungen"
        pass

    def type_cache_callback(self, option):
        if empty_cache == option:
            return
        self.sensor_type_entry.delete(0, "end")
        self.sensor_type_entry.insert(0, option)
        self.sensor_type_entry.update()
        pass

    # Wird ausgeführt, wenn der Anwender eine Sensor-ID auswählt
    def option_callback(self, option):
        if empty_cache == option:
            return
        self.sensor_id_entry.delete(0, "end")
        self.sensor_id_entry.insert(0, option)
        self.sensor_id_entry.update()

        indoor = sensor_data.is_indoor(option)

        self.sensor_type_entry.delete(0, "end")
        self.sensor_type_entry.insert(0, sensor_data.find_sensor_type(option, datetime.datetime.now().year, indoor))
        self.sensor_type_entry.update()

        self.indoor_value.set(indoor)
        self.indoor_check_btn.update()
        pass

    # Wird ausgeführt, wenn der Anwender auf den Auswählen-Button drückt.
    # Diese Funktion führt einen neuen Thread aus, der die Funktion select_sensor ausführt.
    # Außerdem werden die angegebenen Parameter auf Richtigkeit geprüft.
    def select_callback(self, event=None):
        if self.downloading.value.numerator > DownloadState.NONE.value.numerator:
            already_downloading()
            return
        try:
            id = int(self.sensor_id_entry.get())

            if not self.__check_id(id):
                return
            self.downloading = DownloadState.LOADING_GRAPH
            thread = threading.Thread(target=self.select_sensor, args=([id]))
            thread.start()
        except ValueError:
            message_box("Fehler", "Bitte wähle richtige Datentypen aus.", 0)

    # Führt die Funktion show_graph aus,
    # wenn der ausgewählte Sensor in der Datenbank existiert,
    # sowie wenn Daten aus dem jeweiligen Jahr existieren.
    # Wenn nicht, werden Fehlermeldungen in mit der message_box Funktion ausgegeben.
    def select_sensor(self, id: int):
        if sensor_data.exists_in_database(id):
            self.__check_old_graph()
            self.downloading = DownloadState.LOADING_GRAPH
            loader = SensorDownloader(sensor_selector=self, master=root)
            loader.pack(expand=True, fill="both")

            loader.title.configure(text="Lade Sensor aus Datenbank...")
            loader.title.update()

            sensor = sensor_data.get_sensor(id)
            self.__check_indoor(sensor.indoor)

            self.show_graph(sensor, loader)
            loader.finished()
        else:
            message_box("Fehler", "Dieser Sensor konnte nicht gefunden werden, bitte synchronisiere diesen erst.",
                        0)
            pass
        self.downloading = DownloadState.NONE

    # Wird ausgeführt, wenn der Anwender auf den Cache-Leeren-Button drückt.
    # Diese Funktion prüft, ob bereits ein Download stattfindet,
    # wenn nicht, wird der Cache geleert.
    # Nachdem der Cache geleert wurde, wird das Option-Panel neu geladen.
    def clear_cache_callback(self, event=None):
        if self.downloading.value.numerator > DownloadState.NONE.value.numerator:
            already_downloading()
            return
        self.downloading = DownloadState.CLEARING_CACHE
        thread = threading.Thread(target=self.clear_cache, args=())
        thread.start()

    def clear_cache(self):
        sensor_data.clear_cache(self.clear_all_checked.get())
        if self.clear_all_checked.get():
            self.sensor_id_cache.clear()
            self.sensor_id_cache.add(empty_cache)
            self.__reload_option_panel()
        self.__check_old_graph()
        message_box("Cache", "Cache wurde erfolgreich gelöscht", 0)
        self.downloading = DownloadState.NONE

    # Wird ausgeführt, wenn der Anwender auf den Cache-Leeren-Button drückt.
    # Erstellt einen neuen SensorDownloader, wenn kein Download stattfindet.
    #
    # Nach der Überprüfung der angegebenen Parameter,
    # wird ein neuer Thread erstellt, der die Funktion start_download_check startet.
    def sync_callback(self, event=None):
        if self.downloading.value.numerator > DownloadState.NONE.value.numerator:
            already_downloading()
            return
        self.downloading = DownloadState.SEARCHING_TYPE
        try:
            year = int(self.year_entry.get())
            id = int(self.sensor_id_entry.get())

            if self.__check_year(year) == False or self.__check_id(id) == False:
                return

            self.__check_old_graph()
            downloader = SensorDownloader(self, root, show_cancel=True)
            downloader.pack(expand=True, fill="both")

            self.check_thread = threading.Thread(target=self.start_download_check, args=(year, id, downloader))
            self.check_thread.start()

        except ValueError:
            self.downloading = DownloadState.NONE
            message_box("Fehler", "Bitte wähle richtige Datentypen aus.", 0)

    # Startet den Download-Thread und den Checker
    def start_download_check(self, year: int, id: int, downloader: SensorDownloader):
        self.download_thread = threading.Thread(target=self.start_download, args=(year, id, downloader))
        self.download_thread.start()
        self.__check_download(downloader)

    # Startet den eigentlichen Download sowie die Speicherung der Daten.
    # Nach der Fertigstellung des downloads wird das Option-Panel aktualisiert.
    def start_download(self, year: int, id: int, downloader: SensorDownloader):

        downloader.title.configure(text="Prüfe Internetverbindung...")
        if not sensor_data.check_connection(10):
            message_box("Fehler", "Es konnte keine Internetverbindung hergestellt werden.", 0)
            downloader.finished()
            self.downloading = DownloadState.NONE
            return

        downloader.title.configure(text=f"Suche Sensortyp...")
        downloader.title.update()
        indoor = sensor_data.is_indoor(id)
        if indoor is None:
            indoor = self.indoor_value.get()

        if self.sensor_type_entry.get().replace(" ", "") != "":
            typ = self.sensor_type_entry.get()
        else:
            typ = sensor_data.find_sensor_type(id, year, indoor)

        self.__check_indoor(indoor)
        self.downloading = DownloadState.DOWNLOADING
        downloader.title.configure(text="Initialisiere Download...")

        self.sensor_type_entry.delete(0, "end")
        self.sensor_type_entry.insert(0, typ)
        self.sensor_type_entry.update()

        sensor = sensor_data.load_sensor_data(year, typ, id, indoor, downloader.download)
        if self.downloading.value.numerator == DownloadState.NONE.value.numerator:
            return

        if sensor is None or len(sensor.sensor_data) == 0:
            message_box("Fehler", "Es konnte keine Daten gefunden werden.", 0)
            self.downloading = DownloadState.NONE
            downloader.finished()
            return

        self.downloading = DownloadState.SAVING_IN_DATABASE

        downloader.title.configure(text="Speicher Sensor in Datenbank...")
        sensor_data.save_in_database(sensor)
        downloader.finished()

        if empty_cache in self.sensor_id_cache:
            self.sensor_id_cache.remove(empty_cache)
        if str(sensor.id) not in self.sensor_id_cache:
            self.sensor_id_cache.add(sensor.id)
            self.__reload_option_panel()

        message_box("Download", "Daten wurden erfolgreich heruntergeladen.", 0)
        self.downloading = DownloadState.NONE

    #
    def show_graph(self, sensor: sensor_data.Sensor, loader: SensorDownloader):
        self.graph = SensorGraph(sensor, root)
        self.graph.pack(expand=True, fill="both")
        self.graph.show_data(loader)

    def __reload_option_panel(self):
        self.sensor_cache_option.destroy()
        self.sensor_cache_option = tk.OptionMenu(
            self, self.sensor_cache_option_var, *self.sensor_id_cache, command=self.option_callback)
        self.sensor_cache_option.grid(column=1, row=4)

    def __check_download(self, downloader: SensorDownloader):
        time.sleep(sensor_search_timeout)
        if self.downloading == DownloadState.SEARCHING_TYPE:
            self.download_thread.join(timeout=sensor_thread_timeout)
            message_box("Fehler", "Fehler beim laden des Sensortyps. Bitte gib den Typ manuell ein.", 0)
            self.downloading = DownloadState.NONE
            downloader.finished()

    def __check_old_graph(self):
        if self.graph is not None:
            self.graph.destroy()

    def __check_indoor(self, indoor: int):
        self.indoor_value.set(indoor)
        self.indoor_check_btn.update()

    def __check_year(self, year: int) -> bool:
        if year < 2015 or year > datetime.datetime.now().year:
            message_box("Fehler", f"Die das Jahr ist ungültig!\n"
                                  f"Es können nur Daten geladen werden von 2015 bis {datetime.datetime.now().year}.", 0)
            self.downloading = DownloadState.NONE
            return False
        return True

    def __check_id(self, id: int):
        if id <= 0:
            message_box("Fehler", f"Die SensorID ist ungültig!\n"
                                  f"Die ID kann nicht kleiner als 1 sein.", 0)
            self.downloading = DownloadState.NONE
            return False
        return True


def already_downloading():
    message_box("Bitte warten...", "Es werden momentan Daten geladen.", 0)


print("Opening GUI...")

root = tk.Tk()

root.title("Feinstaubdaten")
if not Path("./cache/favicon.png").exists():
    if not sensor_data.check_connection(10):
        message_box("Fehler", "Es konnte keine Internetverbindung hergestellt werden.", 0)
    else:
        res = requests.get("https://sensor.community/favicon.png")
        file = open("./cache/favicon.png", "wb")
        file.write(res.content)
        file.close()

ico = Image.open("./cache/favicon.png")
photo = ImageTk.PhotoImage(ico)
root.wm_iconphoto(False, photo)

selector = SensorSelector(sensor_data.sensor_id_cache, root)
selector.pack(expand=True, fill="both")

root.mainloop()
