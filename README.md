# ASIS

[![CI](https://github.com/nadiusk80-oss/asis-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/nadiusk80-oss/asis-ai/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B%20x64-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

ASIS es una aplicacion de terminal para **crear tus propias IA**. Cada IA que creas tiene nombre, personalidad, modelo y temperatura propios; se guarda en tu equipo y puedes conversar con ella cuando quieras.

Por dentro usa la API de **Gemini** de Google. ASIS no entrena un modelo propio: es un cliente abierto, legible y facil de modificar que convierte a Gemini en tantos asistentes personalizados como quieras. Todo el nucleo cabe en `asis.py`.

## Caracteristicas

- Crea tus propias IA con un asistente guiado: nombre, descripcion, personalidad, modelo y temperatura.
- Guarda, lista, cambia y elimina tus IA cuando quieras.
- Conversacion interactiva con memoria del contexto e historial configurable.
- Respuestas en streaming, fragmento a fragmento.
- Modo de una sola pregunta y entrada por pipe (`echo ... | python asis.py`).
- Configuracion por variables de entorno o archivo `.env`; la clave nunca vive en el codigo.
- Mensajes de error claros para claves invalidas, cuotas agotadas o problemas de red.
- Exportacion de conversaciones a Markdown.
- **64 bits**: requisito documentado, comprobacion en tiempo de ejecucion y build de ejecutable de 64 bits.
- Pruebas automaticas sin conexion, integracion continua y licencia MIT.

## Requisitos

- **Python 3.10 o superior, de 64 bits.**
- Una clave de API de Gemini, gratuita en <https://aistudio.google.com/apikey>.

### Comprobar que tu Python es de 64 bits

```bash
python -c "import struct; print(struct.calcsize('P') * 8, 'bits')"
```

Debe imprimir `64 bits`. En Windows, descarga el instalador **Windows installer (64-bit)** desde <https://www.python.org/downloads/windows/>. ASIS funciona en 32 bits, pero avisa al arrancar y el build de ejecutables exige 64 bits para que el `.exe` resultante sea de 64 bits.

## Instalacion

```bash
git clone https://github.com/nadiusk80-oss/asis-ai.git
cd asis-ai

python -m venv .venv

# Windows (PowerShell o CMD)
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Si quieres el comando `asis` instalado, ejecuta `python -m pip install -e .` y usa `asis` en lugar de `python asis.py`.

## Crea tu primera IA

Ejecuta el asistente de creacion:

```bash
python asis.py --crear
```

ASIS te pedira:

1. Nombre de tu IA.
2. Una descripcion breve.
3. Como debe comportarse (personalidad e instrucciones).
4. Modelo de Gemini.
5. Temperatura entre 0 y 2.

Luego conversa con ella:

```bash
python asis.py --asistente "Mi IA"
```

Lista tus IA guardadas:

```bash
python asis.py --lista-asistentes
```

Las IA se guardan en `~/.asis/asistentes.json` (en Windows, `C:\Users\<tu_usuario>\.asis\asistentes.json`). Puedes cambiar la ubicacion con `ASIS_HOME`.

### Crear y administrar IA dentro de la conversacion

| Comando | Accion |
| --- | --- |
| `/crear` | Crea una IA personalizada y la activa. |
| `/asistentes` | Lista la IA integrada y las que has creado. |
| `/asistente NOMBRE` | Cambia la IA activa. Usa `/asistente ASIS` para volver a la integrada. |
| `/borrar-asistente NOMBRE` | Elimina una IA personalizada, con confirmacion. |

La IA integrada **ASIS** siempre esta disponible y usa la configuracion del entorno o del archivo `.env`.

## Configuracion

Copia el archivo de ejemplo y escribe tu clave:

```bash
# Windows
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```

```dotenv
ASIS_GEMINI_API_KEY=tu_clave_aqui
```

Tambien puedes usar variables de entorno sin archivo `.env`:

```powershell
# Windows (PowerShell)
$env:ASIS_GEMINI_API_KEY="tu_clave_aqui"
python asis.py
```

```bash
# macOS / Linux
export ASIS_GEMINI_API_KEY="tu_clave_aqui"
python asis.py
```

El entorno tiene prioridad sobre `.env`, de modo que puedes sobrescribir valores sin editar el archivo. `GEMINI_API_KEY` tambien se acepta como alternativa.

### Variables disponibles

| Variable | Valor por defecto | Descripcion |
| --- | --- | --- |
| `ASIS_GEMINI_API_KEY` | sin valor | Clave de API de Gemini. Obligatoria para conversar. |
| `GEMINI_API_KEY` | sin valor | Alternativa a la anterior. |
| `ASIS_MODEL` | `gemini-2.5-flash` | Modelo de la IA integrada. |
| `ASIS_TEMPERATURE` | `0.7` | Creatividad de 0 a 2 de la IA integrada. |
| `ASIS_MAX_HISTORY` | `40` | Mensajes de contexto que se conservan. |
| `ASIS_SYSTEM_PROMPT` | persona de ASIS | Instruccion de sistema de la IA integrada. |
| `ASIS_ASISTENTE` | sin valor | Nombre de la IA personalizada que se usa al arrancar. |
| `ASIS_HOME` | `~/.asis` | Carpeta donde se guardan tus IA. |

## Uso

Abre la conversacion interactiva:

```bash
python asis.py
python asis.py --asistente "Mi IA"
```

Haz una sola pregunta y sal:

```bash
python asis.py "Explicame la fotosintesis en tres frases"
```

Usa otro modelo o cambia la persona:

```bash
python asis.py --modelo gemini-2.5-pro
python asis.py --sistema "Responde siempre en formato de lista"
```

Envia una pregunta por un pipe:

```bash
echo "Que es una API?" | python asis.py
```

Valida la configuracion sin abrir la conversacion:

```bash
python asis.py --check
```

`--check` muestra la IA activa, el modelo, la clave enmascarada y la arquitectura del interprete.

### Comandos de la conversacion

| Comando | Alias | Accion |
| --- | --- | --- |
| `/ayuda` | `/help` | Muestra la ayuda. |
| `/crear` | `/nueva-ia` | Crea una IA personalizada. |
| `/asistentes` | `/ias` | Lista tus IA. |
| `/asistente [nombre]` | `/ia` | Muestra o cambia la IA activa. |
| `/borrar-asistente [nombre]` | | Elimina una IA personalizada. |
| `/limpiar` | `/clear` | Borra el historial de contexto. |
| `/historial` | `/history` | Indica cuantos mensajes hay en contexto. |
| `/modelo [nombre]` | `/model` | Muestra o cambia el modelo de la sesion. |
| `/guardar [ruta]` | `/save` | Guarda la charla en Markdown. |
| `/estado` | `/status` | Muestra IA, modelo, clave enmascarada, arquitectura y datos. |
| `/salir` | `/quit`, `/exit` | Termina la sesion. |

`Ctrl+C` interrumpe la respuesta que se este generando; `Ctrl+D` (o `Ctrl+Z` y Enter en Windows) cierra la sesion.

### Opciones de linea de comandos

| Opcion | Descripcion |
| --- | --- |
| `-m`, `--modelo`, `--model` | Modelo de Gemini a usar. |
| `--sistema`, `--system` | Instruccion de sistema personalizada. |
| `-a`, `--asistente` | Nombre de la IA personalizada a usar. |
| `--crear` | Crea una IA personalizada y termina. No necesita clave de API. |
| `--lista-asistentes`, `--asistentes` | Lista tus IA y termina. |
| `--sin-streaming`, `--no-stream` | Espera la respuesta completa. |
| `--check` | Valida la configuracion y termina. |
| `--version` | Muestra la version. |

## Ejecutable de 64 bits (Windows)

El codigo Python es independiente de la arquitectura, pero el `.exe` hereda la de tu interprete. El script de build lo comprueba y se niega a generar un ejecutable con Python de 32 bits:

```bash
python -m pip install -r requirements-dev.txt
python scripts/build_exe.py
```

Resultado: `dist/ASIS.exe`, un ejecutable autocontenido de 64 bits con la interfaz de consola. El script comprueba la arquitectura antes de compilar y usa el bootloader x64 de PyInstaller; con Python de 32 bits se detiene sin generar el archivo.

El archivo no es firmado digitalmente; Windows SmartScreen puede pedir confirmacion la primera vez. El ejecutable no se sube al repositorio: se genera localmente o se adjunta como release.

## Seguridad

- Nunca subas tu clave al repositorio: `.env` ya esta excluido en `.gitignore`.
- No compartas capturas ni registros donde aparezca la clave.
- Si crees que se filtro, revocala y genera otra en <https://aistudio.google.com/apikey>.
- ASIS solo muestra la clave enmascarada (primeros y ultimos caracteres).
- Tus IA guardadas incluyen sus instrucciones; revisa `~/.asis` antes de compartir esa carpeta.

## Estructura del proyecto

```text
asis-ai/
├── asis.py                  # App principal: configuracion, IA, Gemini y CLI
├── scripts/build_exe.py     # Build de ejecutable de 64 bits con PyInstaller
├── tests/test_asis.py       # Pruebas sin conexion ni clave real
├── .github/workflows/ci.yml # Integracion continua
├── .env.example             # Plantilla de configuracion
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── LICENSE
└── README.md
```

`asis.py` se organiza en cuatro piezas: configuracion (entorno y `.env`), gestion de IA personalizadas (JSON local), proveedor que habla con `google-genai` y conversacion/CLI con los comandos.

## Desarrollo y pruebas

```bash
python -m unittest discover -s tests -v
```

Las pruebas usan un proveedor simulado y un directorio de datos temporal: no necesitan clave de API ni conexion. La integracion continua se ejecuta en GitHub Actions con Python 3.10, 3.12 y 3.13.

## Licencia

Distribuido bajo la licencia MIT. Consulta [LICENSE](LICENSE).

---

# English

ASIS is a terminal application to **create your own AIs**. Every AI you create has its own name, personality, model, and temperature; it is stored on your machine and can be used in any session.

Internally it uses Google's **Gemini** API. ASIS does not train a model: it is a small, readable client that turns Gemini into as many custom assistants as you want. The core lives in a single Python file.

## Features

- Guided creation of your own AIs (name, description, personality, model, temperature).
- Store, list, switch, and delete your AIs.
- Context-aware chat with streaming responses and configurable history.
- One-shot questions, pipe input, and Markdown export.
- Environment variables or `.env`; the key never lives in the code.
- Clear errors for invalid keys, quotas, and network issues.
- 64-bit requirement, runtime check, and a 64-bit executable build script.
- Offline test suite and GitHub Actions CI.

## Requirements

- **Python 3.10+ 64-bit** (check with `python -c "import struct; print(struct.calcsize('P') * 8)"`).
- A free Gemini API key from <https://aistudio.google.com/apikey>.

## Install

```bash
git clone https://github.com/nadiusk80-oss/asis-ai.git
cd asis-ai
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Create your first AI

```bash
python asis.py --crear
python asis.py --asistente "My AI"
python asis.py --lista-asistentes
```

AIs are saved to `~/.asis/asistentes.json` (override with `ASIS_HOME`). Inside the chat, use `/crear`, `/asistentes`, `/asistente NAME`, and `/borrar-asistente NAME`.

## Configure

```bash
cp .env.example .env             # Windows: Copy-Item .env.example .env
```

Set `ASIS_GEMINI_API_KEY` in `.env` or your environment. Optional variables: `ASIS_MODEL` (default `gemini-2.5-flash`), `ASIS_TEMPERATURE` (0.7), `ASIS_MAX_HISTORY` (40), `ASIS_SYSTEM_PROMPT`, `ASIS_ASISTENTE`, `ASIS_HOME`.

## Usage

```bash
python asis.py                              # interactive chat
python asis.py "Explain photosynthesis"     # one-shot answer
python asis.py --asistente "My AI"          # use a custom AI
python asis.py --model gemini-2.5-pro       # choose a model
python asis.py --check                      # validate configuration
echo "What is an API?" | python asis.py
```

Type `/help` inside the chat to list every command. `Ctrl+C` interrupts a streaming answer.

## 64-bit executable (Windows)

```bash
python -m pip install -r requirements-dev.txt
python scripts/build_exe.py
```

The script refuses to build with 32-bit Python and produces `dist/ASIS.exe` as a self-contained 64-bit console executable. The binary is not committed; build it locally or attach it to a release. It is unsigned, so SmartScreen may ask for confirmation.

## Test

```bash
python -m unittest discover -s tests -v
```

No API key or network connection is required.

## License

MIT. See [LICENSE](LICENSE).
