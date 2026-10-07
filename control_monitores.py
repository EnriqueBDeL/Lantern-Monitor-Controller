"""
Lantern
=======
Controla brillo y contraste de varios monitores a la vez, cada uno con su protocolo:
  - Portátil  -> WMI    (solo brillo)
  - Externos  -> DDC/CI (brillo y contraste, uno o varios monitores)

Dependencias (solo Windows):
    pip install customtkinter monitorcontrol wmi pywin32

Uso:
    python control_monitores.py          # normal
    python control_monitores.py --demo   # modo demo con monitores simulados
"""
import json
import os
import sys
import threading
import time

APP_NAME = "Lantern"
APP_VERSION = "v1.0.0"
WIDTH = 460
DEMO = "--demo" in sys.argv
MUTED = ("gray40", "gray60")
DEFAULT_LEVEL = 50
DDC_PROTOCOL = "DDC/CI"
BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
ICON_PATH = os.path.join(BASE_DIR, "control_monitores.ico")


# ============================================================ Configuración
DEFAULTS = {
    "theme": "System",       # System / Light / Dark
    "show_master": True,     # barra combinada (todos a la vez)
    "show_individual": False,  # una barra por monitor
    "show_contrast": True,   # mostrar barras de contraste
    "multi_ddc": True,       # soporte para varios monitores DDC
    "launch_at_startup": False,
    "background_mode": False,
    "devices": {},           # id -> {"enabled": bool, "name": str}
}


class Config:
    def __init__(self):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        folder = os.path.join(base, "Lantern")
        try:
            os.makedirs(folder, exist_ok=True)
        except OSError:
            folder = os.path.expanduser("~")
        self.path = os.path.join(folder, "config.json")
        old_path = os.path.join(base, "ControlMonitores", "config.json")
        self.data = json.loads(json.dumps(DEFAULTS))
        target = self.path if os.path.exists(self.path) else (old_path if os.path.exists(old_path) else self.path)
        try:
            with open(target, encoding="utf-8") as f:
                self.data.update(json.load(f))
        except (OSError, ValueError):
            pass
        if self.data["show_master"]:
            self.data["show_individual"] = False

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def get(self, key):
        return self.data[key]

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def device(self, dev_id, default_name):
        device = self.data["devices"].setdefault(
            dev_id,
            {
                "enabled": True,
                "name": default_name,
                "last_brightness": None,
                "last_contrast": None,
            },
        )
        device.setdefault("last_brightness", None)
        device.setdefault("last_contrast", None)
        return device


# ================================================================ Backends
class WMIBackend:
    """Pantalla interna del portÃ¡til (solo brillo)."""
    protocol = "WMI"
    supports_contrast = False

    def open(self):
        import pythoncom
        import wmi
        pythoncom.CoInitialize()  # COM hay que iniciarlo en cada hilo
        conn = wmi.WMI(namespace="root\\wmi")
        self.methods = conn.WmiMonitorBrightnessMethods()[0]
        return {"brightness": conn.WmiMonitorBrightness()[0].CurrentBrightness, "contrast": None}

    def set(self, kind, value):
        if kind == "brightness":
            self.methods.WmiSetBrightness(Brightness=int(value), Timeout=0)

    def close(self):
        import pythoncom
        pythoncom.CoUninitialize()


class DDCBackend:
    """Un monitor externo por DDC/CI."""
    protocol = DDC_PROTOCOL
    supports_contrast = True

    def __init__(self, monitor):
        self.mon = monitor

    def open(self):
        self.mon.__enter__()
        brightness = self.mon.get_luminance()
        try:
            contrast = self.mon.get_contrast()
        except Exception:
            contrast = None  # este monitor no permite contraste
        return {"brightness": brightness, "contrast": contrast}

    def set(self, kind, value):
        if kind == "brightness":
            self.mon.set_luminance(int(value))
        elif kind == "contrast":
            self.mon.set_contrast(int(value))

    def close(self):
        try:
            self.mon.__exit__(None, None, None)
        except Exception:
            pass


class DemoBackend:
    """Monitor simulado para probar la interfaz sin hardware."""

    def __init__(self, protocol, supports_contrast, delay):
        self.protocol, self.supports_contrast, self.delay = protocol, supports_contrast, delay

    def open(self):
        time.sleep(0.6)
        return {"brightness": 70, "contrast": 50 if self.supports_contrast else None}

    def set(self, *_args):
        del _args
        time.sleep(self.delay)

    def close(self):
        pass


# ================================================================== Worker
class Worker(threading.Thread):
    """Un hilo por monitor: asÃ­ uno no bloquea al otro (DDC es lento)."""

    def __init__(self, backend, on_ready, on_error):
        super().__init__(daemon=True)
        self.backend, self.on_ready, self.on_error = backend, on_ready, on_error
        self.pending = {}
        self.lock = threading.Lock()
        self.event = threading.Event()
        self.running = True

    def request(self, kind, value):
        with self.lock:
            self.pending[kind] = value  # solo importa el Ãºltimo valor
        self.event.set()

    def stop(self):
        self.running = False
        self.event.set()

    def run(self):
        try:
            self.on_ready(self.backend.open())
        except Exception as e:
            self.on_error(str(e) or e.__class__.__name__)
            return
        while True:
            self.event.wait()
            self.event.clear()
            if not self.running:
                break
            with self.lock:
                jobs, self.pending = self.pending, {}
            for kind, value in jobs.items():
                try:
                    self.backend.set(kind, value)
                except Exception as e:
                    self.on_error(str(e) or e.__class__.__name__)
        self.backend.close()


class Device:
    """Un monitor lÃ³gico: estado + hilo de comunicaciÃ³n."""

    def __init__(self, app, dev_id, default_name, backend, ddc_index=None):
        self.app, self.id, self.backend, self.ddc_index = app, dev_id, backend, ddc_index
        self.default_name = default_name
        self.values = {"brightness": 50, "contrast": 50}
        self.has_contrast = False
        self.status = "connecting"  # connecting / ready / error
        self.message = "Conectando…"
        q = app.ui_queue
        self.worker = Worker(
            backend,
            lambda state: q.put(lambda: self._ready(state)),
            lambda msg: q.put(lambda: self._error(msg)),
        )
        self.worker.start()

    # --- propiedades
    @property
    def protocol(self):
        return self.backend.protocol

    @property
    def supports_contrast(self):
        return self.backend.supports_contrast

    @property
    def settings(self):
        return self.app.cfg.device(self.id, self.default_name)

    @property
    def name(self):
        return self.settings["name"] or self.default_name

    @property
    def visible(self):
        if not self.settings["enabled"]:
            return False
        return self.ddc_index is None or self.app.cfg.get("multi_ddc") or self.ddc_index == 0

    # --- estado
    def set_value(self, kind, value):
        self.values[kind] = value
        if kind == "brightness":
            self.settings["last_brightness"] = value
        elif kind == "contrast":
            self.settings["last_contrast"] = value
        self.app.cfg.save()
        if self.status == "ready":
            self.worker.request(kind, value)

    def stop(self):
        self.worker.stop()

    def _ready(self, state):
        self.values["brightness"] = state["brightness"]
        if state["contrast"] is not None:
            self.values["contrast"] = state["contrast"]
        self.has_contrast = state["contrast"] is not None
        self.status, self.message = "ready", "Conectado"
        saved_brightness = self.settings["last_brightness"]
        saved_contrast = self.settings["last_contrast"]
        if isinstance(saved_brightness, (int, float)):
            self.set_value("brightness", saved_brightness)
        if self.has_contrast and isinstance(saved_contrast, (int, float)):
            self.set_value("contrast", saved_contrast)
        self.app.refresh()

    def _error(self, msg):
        self.status, self.message = "error", f"Error: {msg}"
        self.app.refresh()



if __name__ == "__main__":
    from pantalla_principal import App

    App().mainloop()
