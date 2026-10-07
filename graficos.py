from __future__ import annotations

import customtkinter as ctk

MUTED = ("gray40", "gray60")

class SliderRow(ctk.CTkFrame):
    def __init__(self, master, text, command):
        super().__init__(master, fg_color="transparent")
        self.command = command
        self.columnconfigure(1, weight=1)
        ctk.CTkLabel(self, text=text, width=64, anchor="w").grid(row=0, column=0)
        self.slider = ctk.CTkSlider(self, from_=0, to=100, number_of_steps=100, command=self._moved)
        self.slider.grid(row=0, column=1, sticky="ew", padx=8)
        self.value_label = ctk.CTkLabel(self, text="--", width=44, anchor="e")
        self.value_label.grid(row=0, column=2)

    def _moved(self, value):
        value = int(round(value))
        self.value_label.configure(text=f"{value}%")
        self.command(value)

    def update_state(self, enabled, value):
        self.slider.configure(state="normal" if enabled else "disabled")
        if enabled:
            self.slider.set(value)
            self.value_label.configure(text=f"{int(value)}%")
        else:
            self.value_label.configure(text="--")


def small(master, **kw):
    kw.setdefault("anchor", "w")
    return ctk.CTkLabel(master, font=ctk.CTkFont(size=12), text_color=MUTED, **kw)


class DeviceCard(ctk.CTkFrame):
    """Tarjeta con las barras de un monitor individual."""

    def __init__(self, master, app, device):
        super().__init__(master, corner_radius=14)
        self.device = device

        def move(kind, value):
            device.set_value(kind, value)
            app.refresh(skip=self)  # actualiza la barra combinada

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 4))
        self.title = ctk.CTkLabel(top, text=device.name, font=ctk.CTkFont(size=15, weight="bold"))
        self.title.pack(side="left")
        small(top, text=device.protocol).pack(side="right")

        self.brightness = SliderRow(self, "Brillo", lambda v: move("brightness", v))
        self.brightness.pack(fill="x", padx=16, pady=4)
        self.contrast = None
        if app.cfg.get("show_contrast") and device.supports_contrast:
            self.contrast = SliderRow(self, "Contraste", lambda v: move("contrast", v))
            self.contrast.pack(fill="x", padx=16, pady=4)
        self.status = small(self, text="")
        self.status.pack(fill="x", padx=16, pady=(2, 12))

    def refresh(self):
        d = self.device
        ready = d.status == "ready"
        self.title.configure(text=d.name)
        self.brightness.update_state(ready, d.values["brightness"])
        message = d.message
        if self.contrast:
            self.contrast.update_state(ready and d.has_contrast, d.values["contrast"])
            if ready and not d.has_contrast:
                message = "Este monitor no permite ajustar el contraste"
        self.status.configure(text=message)


class MasterCard(ctk.CTkFrame):
    """Barra combinada: mueve todos los monitores visibles a la vez."""

    def __init__(self, master, app):
        super().__init__(master, corner_radius=14)
        self.app = app
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(top, text="Todos los monitores", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        ctk.CTkButton(
            top, text="Restablecer valores", width=120, height=26,
            command=app.reset_defaults,
        ).pack(side="right")
        self.brightness = SliderRow(self, "Brillo", lambda v: self._move("brightness", v))
        self.brightness.pack(fill="x", padx=16, pady=(4, 12))
        self.contrast = None
        if app.cfg.get("show_contrast") and any(d.supports_contrast for d in app.visible_devices()):
            self.contrast = SliderRow(self, "Contraste", lambda v: self._move("contrast", v))
            self.contrast.pack(fill="x", padx=16, pady=(0, 12))

    def _move(self, kind, value):
        for d in self.app.targets(kind):
            d.set_value(kind, value)
        self.app.refresh(skip=self)

    def _refresh_row(self, row, kind):
        targets = self.app.targets(kind)
        if targets:
            row.update_state(True, sum(d.values[kind] for d in targets) / len(targets))
        else:
            row.update_state(False, 0)

    def refresh(self):
        self._refresh_row(self.brightness, "brightness")
        if self.contrast:
            self._refresh_row(self.contrast, "contrast")
