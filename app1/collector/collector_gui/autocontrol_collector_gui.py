import json
import threading
import time
from pathlib import Path

import customtkinter as ctk
import requests
from serial.tools import list_ports

try:
    import obd
except ImportError:
    obd = None


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "collector_config.json"


class AutoControlCollector(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AutoControl Collector")
        self.geometry("650x520")
        self.resizable(False, False)

        self.config_data = self.load_config()
        self.connection = None
        self.selected_port = None
        self.sending = False

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.build_ui()

    def load_config(self):
        if not CONFIG_PATH.exists():
            return {
                "api_url": "http://127.0.0.1:8000/api/obd/ingest/",
                "api_key": "tu_clave_secreta",
                "vehicle_code": "ABC5543",
                "interval_seconds": 2,
                "demo_mode": True,
            }

        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            return json.load(file)

    def build_ui(self):
        title = ctk.CTkLabel(
            self,
            text="AutoControl Collector",
            font=("Arial", 24, "bold"),
        )
        title.pack(pady=15)

        self.vehicle_label = ctk.CTkLabel(
            self,
            text=f"Vehículo: {self.config_data.get('vehicle_code')}",
            font=("Arial", 15),
        )
        self.vehicle_label.pack(pady=5)

        self.status_label = ctk.CTkLabel(
            self,
            text="Estado: Desconectado",
            text_color="orange",
            font=("Arial", 15, "bold"),
        )
        self.status_label.pack(pady=5)

        self.scan_button = ctk.CTkButton(
            self,
            text="Escanear puertos",
            command=self.scan_ports,
        )
        self.scan_button.pack(pady=10)

        self.port_menu = ctk.CTkOptionMenu(
            self,
            values=["Sin puertos detectados"],
            command=self.select_port,
            width=420,
        )
        self.port_menu.pack(pady=5)

        self.connect_button = ctk.CTkButton(
            self,
            text="Conectar",
            command=self.connect_obd,
        )
        self.connect_button.pack(pady=10)

        self.data_frame = ctk.CTkFrame(self)
        self.data_frame.pack(pady=10, padx=20, fill="x")

        self.rpm_label = ctk.CTkLabel(self.data_frame, text="RPM: --")
        self.rpm_label.pack(pady=5)

        self.temp_label = ctk.CTkLabel(self.data_frame, text="Temperatura: -- °C")
        self.temp_label.pack(pady=5)

        self.speed_label = ctk.CTkLabel(self.data_frame, text="Velocidad: -- km/h")
        self.speed_label.pack(pady=5)

        self.send_button = ctk.CTkButton(
            self,
            text="Iniciar envío de datos",
            command=self.toggle_sending,
            fg_color="green",
        )
        self.send_button.pack(pady=15)

        self.log_box = ctk.CTkTextbox(self, height=120, width=580)
        self.log_box.pack(pady=10)
        self.write_log("Collector iniciado correctamente.")

    def write_log(self, message):
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")

    def scan_ports(self):
        ports = list(list_ports.comports())

        if not ports:
            self.port_menu.configure(values=["Sin puertos detectados"])
            self.port_menu.set("Sin puertos detectados")
            self.write_log("No se encontraron puertos seriales.")
            return

        port_names = [f"{p.device} - {p.description}" for p in ports]
        self.port_menu.configure(values=port_names)
        self.port_menu.set(port_names[0])
        self.selected_port = ports[0].device

        self.write_log("Puertos encontrados:")
        for port in port_names:
            self.write_log(f" - {port}")

    def select_port(self, value):
        self.selected_port = value.split(" - ")[0]
        self.write_log(f"Puerto seleccionado: {self.selected_port}")

    def connect_obd(self):
        demo_mode = self.config_data.get("demo_mode", True)

        if demo_mode:
            self.status_label.configure(
                text="Estado: Modo demo activo", text_color="green"
            )
            self.write_log("Conexión demo activada. No se requiere OBD físico.")
            return

        if obd is None:
            self.write_log("ERROR: La librería obd no está instalada.")
            return

        if not self.selected_port:
            self.write_log("Seleccione un puerto antes de conectar.")
            return

        try:
            self.write_log(f"Conectando a {self.selected_port}...")
            self.connection = obd.OBD(self.selected_port, fast=False)

            if self.connection.is_connected():
                self.status_label.configure(
                    text="Estado: Conectado", text_color="green"
                )
                self.write_log("Conexión OBD establecida correctamente.")
            else:
                self.status_label.configure(
                    text="Estado: No conectado", text_color="red"
                )
                self.write_log("No se pudo establecer conexión OBD.")
        except Exception as e:
            self.status_label.configure(
                text="Estado: Error de conexión", text_color="red"
            )
            self.write_log(f"ERROR al conectar: {e}")

    def toggle_sending(self):
        if self.sending:
            self.sending = False
            self.send_button.configure(text="Iniciar envío de datos", fg_color="green")
            self.write_log("Envío detenido.")
        else:
            self.sending = True
            self.send_button.configure(text="Detener envío", fg_color="red")
            thread = threading.Thread(target=self.send_loop, daemon=True)
            thread.start()
            self.write_log("Envío iniciado.")

    def read_obd_data(self):
        demo_mode = self.config_data.get("demo_mode", True)

        if demo_mode:
            return {
                "vehicle_code": self.config_data.get("vehicle_code"),
                "engine_rpm": 850,
                "engine_temp_c": 90,
                "vehicle_speed_kph": 0,
            }

        try:
            rpm = self.connection.query(obd.commands.RPM)
            temp = self.connection.query(obd.commands.COOLANT_TEMP)
            speed = self.connection.query(obd.commands.SPEED)

            return {
                "vehicle_code": self.config_data.get("vehicle_code"),
                "engine_rpm": float(rpm.value.magnitude) if not rpm.is_null() else None,
                "engine_temp_c": (
                    float(temp.value.magnitude) if not temp.is_null() else None
                ),
                "vehicle_speed_kph": (
                    float(speed.value.magnitude) if not speed.is_null() else None
                ),
            }
        except Exception as e:
            self.write_log(f"ERROR leyendo datos OBD: {e}")
            return None

    def send_loop(self):
        interval = self.config_data.get("interval_seconds", 2)

        while self.sending:
            data = self.read_obd_data()

            if data:
                self.update_labels(data)
                self.send_to_api(data)

            time.sleep(interval)

    def update_labels(self, data):
        self.rpm_label.configure(text=f"RPM: {data.get('engine_rpm')}")
        self.temp_label.configure(text=f"Temperatura: {data.get('engine_temp_c')} °C")
        self.speed_label.configure(
            text=f"Velocidad: {data.get('vehicle_speed_kph')} km/h"
        )

    def send_to_api(self, data):
        api_url = self.config_data.get("api_url")
        api_key = self.config_data.get("api_key")

        headers = {
            "Content-Type": "application/json",
            "X-INGEST-KEY": api_key,
        }

        try:
            response = requests.post(api_url, json=data, headers=headers, timeout=10)

            if response.status_code in [200, 201]:
                self.write_log(f"Enviado correctamente: {data}")
            else:
                self.write_log(f"Error API {response.status_code}: {response.text}")
        except Exception as e:
            self.write_log(f"ERROR enviando a API: {e}")


if __name__ == "__main__":
    app = AutoControlCollector()
    app.mainloop()
