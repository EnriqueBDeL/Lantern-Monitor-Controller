<h1 align="center">💡 Lantern — Universal Monitor Brightness & Contrast Controller</h1>

<p align="center">
  <strong>Controlador integral y fluido de brillo y contraste para pantallas de portátil y monitores externos en Windows</strong><br>
  <em>Soporte nativo para protocolos WMI (pantalla integrada) y DDC/CI (monitores externos individuales y multimonitor).</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Versi%C3%B3n-v1.0.0-blue?style=for-the-badge&logo=semver" alt="Versión v1.0.0"/>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/Plataforma-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows"/>
  <img src="https://img.shields.io/badge/Privacidad-100%25%20Offline-green?style=for-the-badge&logo=shield" alt="100% Offline"/>
  <img src="https://img.shields.io/badge/Desarrollado%20por-EnriqueBDL-purple?style=for-the-badge" alt="Autor EnriqueBDL"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Estado-v1.0.0%20Estable-success?style=flat-square&logo=git" alt="Estado"/>
  <img src="https://img.shields.io/badge/UI-CustomTkinter-2b5b84?style=flat-square" alt="CustomTkinter"/>
  <img src="https://img.shields.io/badge/Creado%20con-Google%20Antigravity-4285F4?style=flat-square&logo=google" alt="Google Antigravity"/>
  <img src="https://img.shields.io/badge/Editor-VS%20Code-007ACC?style=flat-square&logo=visual-studio-code" alt="VS Code"/>
  <img src="https://img.shields.io/badge/IA%20Pair-Gemini%20Flash%20%2F%20Pro-8E75B2?style=flat-square&logo=google-gemini" alt="Gemini"/>
</p>

---

## 📌 ¿De qué trata esta aplicación?

**Lantern** es una herramienta de escritorio ligera, moderna y de alto rendimiento diseñada para Windows que permite regular el brillo y el contraste de todos tus monitores desde un único lugar.

Elimina la molestia de usar los botones físicos de los monitores. **Lantern** se comunica directamente con el hardware mediante:
- **WMI (`Windows Management Instrumentation`)**: Para regular el brillo de la pantalla integrada en portátiles y laptops.
- **DDC/CI (`Display Data Channel Command Interface`)**: Para gestionar brillo y contraste en pantallas y monitores externos conectados por HDMI, DisplayPort o USB-C.

---

## ✨ Características Principales

- 🎛️ **Modo Maestro y Control Individual**:
  - **Barra Combinada**: Modifica el brillo de todas las pantallas conectadas al unísono de forma sincronizada.
  - **Barras Individuales**: Ajusta el brillo y contraste de cada monitor por separado.
- 🖥️ **Soporte Multimonitor Avanzado**: Detección y control de múltiples pantallas externas DDC/CI con opción de renombrarlas a tu gusto.
- 🔄 **Búsqueda Dinámica de Monitores**: Botón de reescaneo en caliente para detectar nuevas pantallas conectadas sin reiniciar el sistema.
- 💾 **Persistencia Automática de Ajustes**: Recuerda tus niveles preferidos de brillo y contraste por pantalla tras cada reinicio (`%AppData%/Lantern/config.json`).
- ⚡ **Bandeja del Sistema (System Tray)**: Opción de operar en segundo plano minimizándose en la bandeja con menú contextual rápido.
- 🚀 **Inicio con Windows**: Opción integrada para arrancar automáticamente junto al sistema operativo.
- 🎨 **Interfaz Moderna y Adaptativa**: Diseñada con `CustomTkinter` en modo Claro, Oscuro o Automático según el sistema.
- 🔒 **100% Local y Sin Conexión**: No requiere Internet, ni cuentas, ni servicios en la nube.

---

## 📁 Estructura del Proyecto

El código está organizado siguiendo una arquitectura modular y limpia:

```text
Lantern/
├── .github/
│   └── workflows/
│       └── build-exe.yml           # Compilación automatizada en GitHub Actions al crear un tag
│
├── control_monitores.py            # Punto de entrada, configuración, backends WMI y DDC/CI
├── pantalla_principal.py           # Ventana principal, bandeja del sistema y ciclo de eventos
├── ajustes.py                      # Ventana de configuración, monitores y temas
├── graficos.py                     # Tarjetas de monitores y controles deslizantes CustomTkinter
├── control_monitores.ico           # Icono oficial de alta definición
├── requirements.txt                # Dependencias requeridas en Python
├── Lantern.spec                    # Especificación oficial de compilación con PyInstaller
├── build_exe.bat                   # Script en lote para compilar a .EXE en local con 1 clic
├── .gitignore                      # Reglas de exclusión de entornos virtuales y binarios
└── README.md                       # Documentación oficial del repositorio
```

---

## 🚀 Instalación y Puesta en Marcha

### Prerrequisitos
- Sistema Operativo **Windows 10 / Windows 11**.
- **Python 3.10** o superior.

### 1. Clonar el repositorio
```bash
git clone https://github.com/TU_USUARIO/Lantern.git
cd Lantern
```

### 2. Crear entorno virtual e instalar dependencias
```bat
py -3 -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación
```bat
python control_monitores.py
```

> [!TIP]
> Si deseas probar la interfaz gráfica sin necesidad de interactuar con monitores físicos, puedes usar el modo demo:
> ```bat
> python control_monitores.py --demo
> ```

---

## 📦 Compilación a Ejecutable (.EXE)

Puedes empaquetar toda la aplicación en un archivo `.exe` único y portable sin dependencias externas:

### Método 1 (Recomendado):
Haz doble clic sobre el script [`build_exe.bat`](build_exe.bat). Se encargará de crear el entorno, instalar los módulos necesarios y compilar el archivo final en `dist/Lantern.exe`.

### Método 2 (Manual por Terminal):
```powershell
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean Lantern.spec
```

---

## 🌐 Publicación de Releases en GitHub

Este repositorio incluye integración continua con **GitHub Actions**. Para publicar una nueva versión con el `.exe` compilado automáticamente en GitHub:

```bash
git add .
git commit -m "Preparar versión v1.0.0"
git tag v1.0.0
git push origin main
git push origin v1.0.0
```

GitHub Actions compilará automáticamente el proyecto en un entorno limpio de Windows y adjuntará `Lantern.exe` en los **Assets** de la Release correspondiente.

---

## 🔒 Privacidad y Seguridad

> [!IMPORTANT]
> **Zero Telemetry / 100% Offline Policy**
> Lantern no realiza solicitudes de red, no recopila métricas ni envía datos de uso. La comunicación se realiza de manera 100% local a través de los controladores del sistema operativo.

---

## 👨💻 Autor y Créditos

- **Desarrollador Principal**: **EnriqueBDL**
- **Herramientas de Desarrollo**: Diseñado y refinado utilizando **Google Antigravity**, **Visual Studio Code** y **Gemini**.

---

<p align="center">
  Desarrollado con dedicación por <strong>EnriqueBDL</strong> © 2026
</p>
