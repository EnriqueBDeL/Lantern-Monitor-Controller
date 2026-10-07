from __future__ import annotations

import customtkinter as ctk

from control_monitores import APP_VERSION
from graficos import small

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Ajustes")
        self.resizable(False, False)
        self._fit_window()
        self.after(150, self.lift)
        box = ctk.CTkFrame(self, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=8, pady=8)
        self.box = box
        self.switch_vars = {}

        self.section("Barras de control")
        self.switch("Barra combinada (mueve todos a la vez)", "show_master")
        self.switch("Barras individuales (una por monitor)", "show_individual")
        self.switch("Mostrar contraste", "show_contrast")
        self.switch("Iniciar con Windows", "launch_at_startup")
        self.switch(
            "Mantener en segundo plano",
            "background_mode",
            "Al cerrar la ventana, la aplicación seguirá disponible en la bandeja del sistema.",
        )

        self.section("Varios monitores DDC/CI")
        self.switch("Soporte para varios monitores DDC", "multi_ddc",
                    "Desactivado: solo se usa el primer monitor DDC detectado.")
        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=(6, 0))
        ctk.CTkButton(row, text="Buscar monitores de nuevo", width=190,
                      command=app.scan_ddc).pack(side="left")
        self.scan_label = small(row, text="")
        self.scan_label.pack(side="left", padx=10)

        self.section("Monitores detectados")
        self.devices_frame = ctk.CTkFrame(box, fg_color="transparent")
        self.devices_frame.pack(fill="x")
        self.build_devices()

        self.section("Apariencia")
        names = {"System": "Sistema", "Light": "Claro", "Dark": "Oscuro"}
        inverse = {v: k for k, v in names.items()}
        seg = ctk.CTkSegmentedButton(
            box, values=list(names.values()),
            command=lambda v: (ctk.set_appearance_mode(inverse[v]), app.cfg.set("theme", inverse[v])))
        seg.set(names[app.cfg.get("theme")])
        seg.pack(padx=8, pady=4, anchor="w")

        ver_row = ctk.CTkFrame(box, fg_color="transparent")
        ver_row.pack(fill="x", padx=8, pady=(20, 6))
        small(ver_row, text=f"Versión: {APP_VERSION}").pack(side="left")

        self.after_idle(self._fit_window)

    def _fit_window(self):
        self.update_idletasks()
        max_height = int(self.winfo_screenheight() * 0.9)
        height = min(max(self.winfo_reqheight(), 440), max_height)
        self.geometry(f"480x{height}")

    def section(self, text):
        ctk.CTkLabel(self.box, text=text, font=ctk.CTkFont(size=14, weight="bold"),
                     anchor="w").pack(fill="x", padx=8, pady=(16, 6))

    def switch(self, text, key, hint=None):
        var = ctk.BooleanVar(value=self.app.cfg.get(key))
        self.switch_vars[key] = var

        def toggled():
            enabled = var.get()
            if key == "launch_at_startup":
                try:
                    self.app.set_startup(enabled)
                except OSError as error:
                    var.set(not enabled)
                    self.app.footer.configure(text=f"No se pudo cambiar el inicio automático: {error}")
                    return
            if key == "show_master" and enabled:
                self.app.cfg.data["show_individual"] = False
                self.switch_vars["show_individual"].set(False)
            elif key == "show_individual" and enabled:
                self.app.cfg.data["show_master"] = False
                self.switch_vars["show_master"].set(False)
            self.app.cfg.set(key, enabled)
            self.app.rebuild()
            if key == "multi_ddc":
                self.build_devices()

        ctk.CTkSwitch(self.box, text=text, variable=var, command=toggled).pack(anchor="w", padx=8, pady=4)
        if hint:
            small(self.box, text=hint).pack(fill="x", padx=12)

    def build_devices(self):
        for w in self.devices_frame.winfo_children():
            w.destroy()
        if not self.app.devices:
            small(self.devices_frame, text="Buscando monitores…").pack(fill="x", padx=8)
        for d in self.app.devices:
            row = ctk.CTkFrame(self.devices_frame, corner_radius=10)
            row.pack(fill="x", padx=8, pady=4)
            locked = d.ddc_index not in (None, 0) and not self.app.cfg.get("multi_ddc")
            var = ctk.BooleanVar(value=d.settings["enabled"])

            def toggled(d=d, var=var):
                d.settings["enabled"] = var.get()
                self.app.cfg.save()
                self.app.rebuild()

            ctk.CTkSwitch(row, text="", width=46, variable=var, command=toggled,
                          state="disabled" if locked else "normal").pack(side="left", padx=(10, 4), pady=8)
            entry = ctk.CTkEntry(row, width=210)
            entry.insert(0, d.name)
            entry.pack(side="left", padx=4)

            def rename(*_args, d=d, entry=entry):
                del _args
                d.settings["name"] = entry.get().strip() or d.default_name
                self.app.cfg.save()
                self.app.refresh()

            entry.bind("<Return>", rename)
            entry.bind("<FocusOut>", rename)
            small(row, text=d.protocol + ("  (desactivado)" if locked else "")).pack(side="right", padx=10)
