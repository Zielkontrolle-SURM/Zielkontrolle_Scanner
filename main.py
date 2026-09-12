import json
import logging
import threading
import time
import re
from pathlib import Path

import requests
import tkinter as tk
from tkinter import ttk


CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "api_url": "http://localhost:8080",
    "cooldown_seconds": 2
}


# --------------------------------------------------
# Konfiguration
# --------------------------------------------------

if not Path(CONFIG_FILE).exists():
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

API_URL = CONFIG["api_url"]
COOLDOWN_SECONDS = CONFIG.get("cooldown_seconds", 2)


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(
    filename="scanner.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# --------------------------------------------------
# Scanner App
# --------------------------------------------------

class ScannerApp:

    PATTERN = re.compile(r"^#\d{4}$")

    def __init__(self, root):
        self.root = root

        self.last_scan = {}
        self.running = True

        self.root.title("QR HID Scanner")

        # Vollbild
        self.root.attributes("-fullscreen", True)

        # Immer im Vordergrund
        self.root.attributes("-topmost", True)

        # ESC zum Beenden
        self.root.bind("<Escape>", lambda e: self.shutdown())

        # Klick irgendwo -> Fokus zurück
        self.root.bind(
            "<Button-1>",
            lambda e: self.entry.focus_set()
        )

        frame = ttk.Frame(root, padding=20)
        frame.pack(fill="both", expand=True)

        title = ttk.Label(
            frame,
            text="Scanner bereit",
            font=("Segoe UI", 24, "bold")
        )
        title.pack(pady=20)

        self.status = tk.StringVar(
            value="Warte auf Scan..."
        )

        status_label = ttk.Label(
            frame,
            textvariable=self.status,
            font=("Segoe UI", 14)
        )
        status_label.pack(pady=15)

        self.entry = ttk.Entry(
            frame,
            font=("Consolas", 24),
            justify="center"
        )

        self.entry.pack(
            fill="x",
            padx=100,
            pady=20
        )

        self.entry.bind("<Return>", self.process_scan)

        self.heartbeat()

    # --------------------------------------------

    def heartbeat(self):
        """Sorgt dafür, dass der Fokus erhalten bleibt."""
        try:
            self.entry.focus_force()
        except Exception:
            pass

        if self.running:
            self.root.after(1000, self.heartbeat)

    # --------------------------------------------

    def process_scan(self, event=None):

        value = self.entry.get().strip()
        self.entry.delete(0, tk.END)

        if not value:
            return

        logging.info("Scan erhalten: %s", value)

        if not self.PATTERN.match(value):
            self.status.set(f"Ungültig: {value}")
            logging.warning("Ungültiges Format: %s", value)
            return

        value = int(value[1:])

        if value <= 0 or value >= 10000:
            self.status.set(f"Ungültig: {value}")
            logging.warning("Ungültige Startnummer: %s", value)
            return

        now = time.time()

        if value in self.last_scan:
            age = now - self.last_scan[value]

            if age < COOLDOWN_SECONDS:
                self.status.set(
                    f"Cooldown aktiv: {value}"
                )
                return

        self.last_scan[value] = now

        self.status.set(
            f"Sende an API: {value}"
        )

        threading.Thread(
            target=self.send_to_api,
            args=(value,),
            daemon=True
        ).start()

    # --------------------------------------------

    def update_status(self, message):
        self.root.after(0, self.status.set, message)

    # --------------------------------------------

    def send_to_api(self, number):

        try:
            response = requests.post(
                f"{API_URL}/scan/{number}",
                timeout=10
            )

            if response.ok:

                logging.info(
                    "Erfolgreich gesendet: %s",
                    number
                )

                self.update_status(f"OK: {number}")

            else:

                logging.error(
                    "HTTP Fehler %s für %s",
                    response.status_code,
                    number
                )

                self.update_status(f"HTTP {response.status_code}")

        except Exception as ex:

            logging.exception(
                "API Fehler für %s",
                number
            )

            self.update_status(f"Fehler: {ex}")

        # --------------------------------------------

    def shutdown(self):

        logging.info("Programm beendet")

        self.running = False
        self.root.destroy()

# --------------------------------------------------
# Start
# --------------------------------------------------

root = tk.Tk()

style = ttk.Style()
style.theme_use("clam")

app = ScannerApp(root)

root.mainloop()