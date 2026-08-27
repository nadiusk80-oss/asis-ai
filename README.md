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

También necesitas una clave API de Gemini. Si no tienes una, ve a:

https://aistudio.google.com/prompts/new_chat

Crea una nueva conversación o prompt, copia la clave API que te proporcione la plataforma y luego abre el archivo `asis.py` en tu editor de texto. Localiza la variable `API_KEY` y pega tu clave dentro de las comillas.

Notas adicionales:

- Guarda el archivo y vuelve a ejecutar `python asis.py`.
- Por seguridad, evita subir tu clave API a repositorios públicos. Considera usar variables de entorno o un archivo de configuración ignorado por git para producción.

Licencia

Este proyecto es de código abierto; revisa el archivo LICENSE (si existe) para conocer los detalles de la licencia.
