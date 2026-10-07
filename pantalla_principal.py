from __future__ import annotations

import os
import queue
import sys
import threading

import customtkinter as ctk
import pystray
from PIL import Image
from pystray import MenuItem

from ajustes import SettingsWindow
from control_monitores import (
    APP_NAME, DEFAULT_LEVEL, DEMO, ICON_PATH, WIDTH, Config,
    DDCBackend, DDC_PROTOCOL, Device, WMIBackend, DemoBackend,
)
from graficos import MUTED, DeviceCard, MasterCard, small

class App(ctk.CTk):
    def __init__(self):
        self.cfg = Config()
        ctk.set_appearance_mode(self.cfg.get("theme"))
        ctk.set_default_color_theme("blue")
        super().__init__()
        self.title(APP_NAME)
        self.minsize(WIDTH, 160)
        self.resizable(False, False)
        self.ui_queue = queue.Queue()
        self.devices, self.cards, self.master_card = [], [], None
        self.settings = None
        self.loading = True
        self.tray_icon = None
        self.tray_thread = None

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(header, text="Monitores", font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="⚙  Ajustes", width=100, fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90"), command=self.open_settings).pack(side="right")
        ctk.CTkButton(
            header, text="Restablecer valores", width=130, fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"), command=self.reset_defaults,
        ).pack(side="right", padx=(0, 8))
        footer_bar = ctk.CTkFrame(self, fg_color="transparent")
        footer_bar.pack(side="bottom", fill="x", padx=18, pady=(0, 12))
        self.footer = small(footer_bar, text="")
        self.footer.pack(side="left", fill="x", expand=True)
        small(footer_bar, text="© EnriqueBDL 2026", anchor="e").pack(side="right")
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=12)
        self.loading_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        self.loading_frame.pack(fill="both", expand=True, pady=42)
        ctk.CTkLabel(
            self.loading_frame,
            text="☀",
            font=ctk.CTkFont(size=56, weight="bold"),
            text_color=("#1f6aa5", "#5da9e9"),
        ).pack(pady=(18, 4))
        ctk.CTkLabel(
            self.loading_frame,
            text=APP_NAME,
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack()
        ctk.CTkLabel(
            self.loading_frame,
            text="Preparando los monitores…",
            text_color=MUTED,
        ).pack(pady=(4, 16))
        self.loading_bar = ctk.CTkProgressBar(self.loading_frame, width=220, mode="indeterminate")
        self.loading_bar.pack()
        self.loading_bar.start()
        self.start_tray()

        self.after(250, self.initialize_devices)
        self.after(50, self.poll)
        self.protocol("WM_DELETE_WINDOW", self.close)
        if "--background" in sys.argv:
            self.after(300, self.hide_to_tray)

    def start_tray(self):
        try:
            image = Image.open(ICON_PATH)
            menu = pystray.Menu(
                MenuItem("Mostrar", self._tray_show, default=True),
                MenuItem(
                    "Restablecer brillo y contraste",
                    self._tray_reset,
                ),
                MenuItem("Salir", self._tray_exit),
            )
            self.tray_icon = pystray.Icon(APP_NAME, image, APP_NAME, menu)
            self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()
        except (OSError, ValueError) as error:
            self.footer.configure(text=f"No se pudo cargar el icono de bandeja: {error}")

    def _tray_show(self, _icon, _item):
        del _icon, _item
        self.after(0, self.show_from_tray)

    def _tray_reset(self, _icon, _item):
        del _icon, _item
        self.after(0, self.reset_defaults)

    def _tray_exit(self, _icon, _item):
        del _icon, _item
        self.after(0, self.exit_app)

    def set_startup(self, enabled):
        import winreg

        command = f'"{sys.executable}"'
        if not getattr(sys, "frozen", False):
            command += f' "{os.path.abspath(__file__)}"'
        command += " --background"
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            if enabled:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
        self.cfg.set("launch_at_startup", enabled)

    def hide_to_tray(self):
        if self.tray_icon:
            self.withdraw()

    def show_from_tray(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def reset_defaults(self):
        for device in self.targets("brightness"):
            device.set_value("brightness", DEFAULT_LEVEL)
        for device in self.targets("contrast"):
            device.set_value("contrast", DEFAULT_LEVEL)
        self.refresh()
        self.footer.configure(text="Brillo y contraste restablecidos al 50%")

    def exit_app(self):
        for d in self.devices:
            d.stop()
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()

    def initialize_devices(self):
        if DEMO:
            self.add_device("laptop", "Portátil", DemoBackend("WMI", False, 0.02))
            self.add_device("ddc0", "Monitor externo 1", DemoBackend(DDC_PROTOCOL, True, 0.2), 0)
            self.add_device("ddc1", "Monitor externo 2", DemoBackend(DDC_PROTOCOL, True, 0.2), 1)
            self.footer.configure(text="Modo demo: monitores simulados")
            self.after(800, self.finish_loading)
        else:
            self.add_device("laptop", "Portátil", WMIBackend())
            self.scan_ddc()
        self.rebuild()

    def finish_loading(self):
        if not self.loading:
            return
        self.loading = False
        self.loading_bar.stop()
        self.loading_frame.destroy()
        self.rebuild()

    # --- dispositivos
    def add_device(self, dev_id, name, backend, ddc_index=None):
        self.devices.append(Device(self, dev_id, name, backend, ddc_index))

    def visible_devices(self):
        return [d for d in self.devices if d.visible]

    def targets(self, kind):
        return [d for d in self.visible_devices() if d.status == "ready"
                and (kind == "brightness" or (d.supports_contrast and d.has_contrast))]

    # --- detección DDC (en segundo plano: puede tardar unos segundos)
    def scan_ddc(self):
        self.footer.configure(text="Buscando monitores DDC/CI…")

        def work():
            try:
                from monitorcontrol import get_monitors
                monitors = get_monitors()
                self.ui_queue.put(lambda: self.scan_done(monitors))
            except Exception as e:
                self.ui_queue.put(lambda e=e: self.scan_done([], str(e)))

        threading.Thread(target=work, daemon=True).start()

    def scan_done(self, monitors, error=None):
        ddc_devices = [d for d in self.devices if d.ddc_index is not None]
        for d in ddc_devices[len(monitors):]:
            d.stop()
            self.devices.remove(d)
        for i in range(len(ddc_devices[:len(monitors)]), len(monitors)):
            self.add_device(f"ddc{i}", f"Monitor externo {i + 1}", DDCBackend(monitors[i]), i)
        if error:
            text = f"No se pudo buscar monitores DDC/CI: {error}"
        elif not monitors:
            text = "No se encontraron monitores DDC/CI. Actívalo en el menú del monitor."
        else:
            text = f"{len(monitors)} monitor(es) DDC/CI detectado(s)"
        self.footer.configure(text=text)
        self.finish_loading()
        self.rebuild()
        if self.settings and self.settings.winfo_exists():
            self.settings.scan_label.configure(text=text)
            self.settings.build_devices()
            self.settings.after_idle(self.settings._fit_window)

    # --- interfaz
    def open_settings(self):
        if self.settings and self.settings.winfo_exists():
            self.settings.lift()
        else:
            self.settings = SettingsWindow(self)

    def rebuild(self):
        if self.loading:
            return
        for w in self.body.winfo_children():
            w.destroy()
        self.cards, self.master_card = [], None
        visible = self.visible_devices()
        if self.cfg.get("show_master") and visible:
            self.master_card = MasterCard(self.body, self)
            self.master_card.pack(fill="x", pady=6)
        if self.cfg.get("show_individual"):
            for d in visible:
                card = DeviceCard(self.body, self, d)
                card.pack(fill="x", pady=6)
                self.cards.append(card)
        if not self.master_card and not self.cards:
            small(self.body, text="No hay nada que mostrar. Activa alguna barra o monitor en Ajustes.").pack(pady=20)
        self.refresh()
        self.fit_window()

    def refresh(self, skip=None):
        for widget in ([self.master_card] if self.master_card else []) + self.cards:
            if widget is not skip:
                widget.refresh()

    def fit_window(self):
        self.update_idletasks()
        try:
            scale = self._get_window_scaling()
        except Exception:
            scale = 1.0
        max_height = self.winfo_screenheight() * 0.9 / scale
        height = min(max(self.winfo_reqheight() / scale, 160), max_height)
        self.geometry(f"{WIDTH}x{int(height)}")

    def poll(self):
        try:
            while True:
                self.ui_queue.get_nowait()()
        except queue.Empty:
            pass
        self.after(50, self.poll)

    def close(self):
        if self.cfg.get("background_mode") and self.tray_icon:
            self.hide_to_tray()
        else:
            self.exit_app()


if __name__ == "__main__":
    App().mainloop()
