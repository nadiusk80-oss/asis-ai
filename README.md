# asis-ai

ASIS es una inteligencia artificial de código abierto implementada como un archivo Python sencillo y fácil de usar.

Características

- Proyecto open-source: el código fuente está disponible para revisarlo, modificarlo y redistribuirlo.
- Implementado en Python: el programa principal es un archivo .py para ejecutar localmente o integrarlo en otros proyectos.

Requisitos

1. Python 3.14.7 instalado en tu sistema. Puedes comprobar la versión con:

```bash
python --version
```

2. La librería "gemini" (o la librería necesaria llamada gemini) instalada. Instálala con pip:

```bash
python -m pip install --upgrade pip
pip install google-genai
```

Uso

- Ejecuta el archivo Python principal (por ejemplo `asis.py`) con:

```bash
python asis.py
```

- Ajusta el nombre del archivo si el archivo principal tiene otro nombre.

Configuración de la clave API

Para que ASIS pueda conectarse al modelo Gemini necesitas configurar tu clave API en el archivo `asis.py`.

Ejemplo (añade esto o edita la sección correspondiente en `asis.py`):

```python
from google import genai

# 1. Configura tu API Key aquí
API_KEY = "(API_KEY_HERE)"
```

Obtener la clave API de Gemini

1. Ve a: https://aistudio.google.com/prompts/new_chat
2. Crea una nueva conversación/prompt o sigue la interfaz para generar/obtener tu clave API de Gemini.
3. Copia la clave proporcionada por la plataforma.

Cómo pegar la clave en asis.py (Opción A — directo)

1. Abre `asis.py` en tu editor.
2. Localiza la sección con la variable `API_KEY` y pega la clave entre comillas:

```python
API_KEY = "sk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

3. Guarda y ejecuta:

```bash
python asis.py
```

Advertencia: no subas esta clave a repositorios públicos.

Opción recomendada: usar una variable de entorno (Opción B — más segura)

Edita `asis.py` para leer la clave desde la variable de entorno:

```python
import os
from google import genai

API_KEY = os.getenv("ASIS_GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("La variable de entorno ASIS_GEMINI_API_KEY no está configurada. Busca la clave en: https://aistudio.google.com/prompts/new_chat")

# Usa API_KEY con la librería google-genai según el resto del código
```

En macOS / Linux (bash/zsh), exporta la variable y ejecuta:

```bash
export ASIS_GEMINI_API_KEY="sk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
python asis.py
```

En Windows (PowerShell), establece y ejecuta:

```powershell
$env:ASIS_GEMINI_API_KEY="sk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
python asis.py
```

Para uso persistente, añade la exportación a `~/.bashrc`, `~/.profile` o usa un archivo `.env` (asegúrate de añadir `.env` a `.gitignore`).

Buenas prácticas

- Nunca publiques tu clave en repositorios públicos.
- Usa variables de entorno o servicios de gestión de secretos para entornos de producción.
- Revoca y regenera la clave si crees que se ha filtrado.
- Considera añadir un ejemplo de `.env.example` y documentarlo en el README.

Sugerencias de mejora (opcional)

- Puedo actualizar `asis.py` para leer la variable de entorno automáticamente y añadir un ejemplo `.env.example` al repo.
- Puedo añadir una sección en el README con pasos para crear un entorno virtual y ejecutar el proyecto de forma aislada.

Licencia

Este proyecto es de código abierto; revisa el archivo LICENSE (si existe) para conocer los detalles de la licencia.

---

# English translation / README (English)

ASIS is an open-source artificial intelligence implemented as a simple, easy-to-use Python file.

Features

- Open-source project: the source code is available for review, modification, and redistribution.
- Implemented in Python: the main program is a .py file you can run locally or integrate into other projects.

Requirements

1. Python 3.14.7 installed on your system. You can check the version with:

```bash
python --version
```

2. The "gemini" library (or the required library named gemini) installed. Install it with pip:

```bash
python -m pip install --upgrade pip
pip install google-genai
```

Usage

- Run the main Python file (for example `asis.py`) with:

```bash
python asis.py
```

- Adjust the filename if the main file has a different name.

API Key configuration

For ASIS to connect to the Gemini model you need to configure your API key in the `asis.py` file.

Example (add this or edit the corresponding section in `asis.py`):

```python
from google import genai

# 1. Set your API Key here
API_KEY = "(API_KEY_HERE)"
```

Obtaining the Gemini API key

1. Go to: https://aistudio.google.com/prompts/new_chat
2. Create a new conversation/prompt or follow the interface to generate/obtain your Gemini API key.
3. Copy the key provided by the platform.

How to paste the key into asis.py (Option A — direct)

1. Open `asis.py` in your editor.
2. Locate the section with the `API_KEY` variable and paste the key inside the quotes:

```python
API_KEY = "sk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

3. Save and run:

```bash
python asis.py
```

Warning: do not upload this key to public repositories.

Recommended option: use an environment variable (Option B — safer)

Edit `asis.py` to read the key from an environment variable:

```python
import os
from google import genai

API_KEY = os.getenv("ASIS_GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("The environment variable ASIS_GEMINI_API_KEY is not set. Get the key at: https://aistudio.google.com/prompts/new_chat")

# Use API_KEY with google-genai according to the rest of the code
```

On macOS / Linux (bash/zsh), export the variable and run:

```bash
export ASIS_GEMINI_API_KEY="sk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
python asis.py
```

On Windows (PowerShell), set and run:

```powershell
$env:ASIS_GEMINI_API_KEY="sk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
python asis.py
```

For persistent use, add the export to `~/.bashrc`, `~/.profile`, or use a `.env` file (make sure to add `.env` to `.gitignore`).

Best practices

- Never publish your key in public repositories.
- Use environment variables or secret management services for production environments.
- Revoke and regenerate the key if you think it has been leaked.
- Consider adding a `.env.example` and document it in the README.

Optional improvements

- I can update `asis.py` to automatically read the environment variable and add a `.env.example` to the repo.
- I can add a section to the README with steps to create a virtual environment and run the project in isolation.

License

This project is open-source; check the LICENSE file (if present) for license details.
