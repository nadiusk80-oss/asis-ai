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
