"""ASIS: crea tus propias IA y conversa con ellas desde la terminal.

ASIS es una aplicacion de linea de comandos basada en los modelos Gemini de
Google. Permite crear asistentes personalizados (nombre, personalidad y
modelo), guardarlos en disco y mantener conversaciones con contexto.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import struct
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterator, Sequence

__version__ = "1.0.0"

# Alias mantenido por Google: apunta siempre al Flash mas reciente y evita
# depender de una version concreta que pueda quedar obsoleta.
MODELO_POR_DEFECTO = "gemini-flash-latest"
PROMPT_POR_DEFECTO = (
    "Eres ASIS, un asistente de inteligencia artificial claro, directo y util. "
    "Responde en el idioma en el que te hable la persona usuaria. "
    "Si no sabes algo, dilo con honestidad en lugar de inventarlo."
)
MAX_HISTORIAL_POR_DEFECTO = 40
ARCHIVO_ENV_POR_DEFECTO = ".env"
NOMBRE_APP = "ASIS"
NOMBRE_INTEGRADO = "ASIS"


class ErrorAsis(Exception):
    """Error controlado que se muestra a la persona usuaria sin traza."""


# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------


def cargar_dotenv(ruta: str | Path = ARCHIVO_ENV_POR_DEFECTO) -> dict[str, str]:
    """Carga variables desde un archivo .env sin pisar valores ya definidos.

    Formato admitido: ``CLAVE=valor``. Se ignoran lineas vacias, comentarios
    que empiezan por ``#`` y comillas envolventes simples o dobles.
    """
    archivo = Path(ruta)
    cargadas: dict[str, str] = {}
    if not archivo.is_file():
        return cargadas

    for linea in archivo.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        clave = clave.strip()
        if clave.startswith("export "):
            clave = clave[len("export ") :].strip()
        if not clave:
            continue
        valor = valor.strip()
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
            valor = valor[1:-1]
        cargadas[clave] = valor
        if not os.environ.get(clave):
            os.environ[clave] = valor
    return cargadas


def obtener_api_key() -> str | None:
    return os.environ.get("ASIS_GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")


def obtener_modelo() -> str:
    return os.environ.get("ASIS_MODEL", MODELO_POR_DEFECTO)


def obtener_prompt() -> str:
    return os.environ.get("ASIS_SYSTEM_PROMPT", PROMPT_POR_DEFECTO)


def obtener_max_historial() -> int:
    valor = os.environ.get("ASIS_MAX_HISTORY")
    if valor is None:
        return MAX_HISTORIAL_POR_DEFECTO
    try:
        cantidad = int(valor)
    except ValueError as exc:
        raise ErrorAsis(f"ASIS_MAX_HISTORY debe ser un entero, no {valor!r}.") from exc
    return max(2, cantidad)


def es_64_bits() -> bool:
    return struct.calcsize("P") * 8 == 64


def describir_arquitectura() -> str:
    return f"{struct.calcsize('P') * 8} bits ({platform.machine() or sys.platform})"


# ---------------------------------------------------------------------------
# Presentacion
# ---------------------------------------------------------------------------


@dataclass
class Estilo:
    activo: bool = True

    def _pintar(self, codigo: str, texto: str) -> str:
        return f"\033[{codigo}m{texto}\033[0m" if self.activo else texto

    def nombre(self, texto: str) -> str:
        return self._pintar("1;36", texto)

    def tenue(self, texto: str) -> str:
        return self._pintar("2", texto)

    def error(self, texto: str) -> str:
        return self._pintar("1;31", texto)

    def ok(self, texto: str) -> str:
        return self._pintar("1;32", texto)


def estilo_por_defecto() -> Estilo:
    return Estilo(
        activo=sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
    )


def enmascarar_clave(clave: str | None) -> str:
    if not clave:
        return "no configurada"
    if len(clave) <= 8:
        return "***"
    return f"{clave[:4]}...{clave[-4:]}"


AYUDA = """\
Comandos disponibles:
  /ayuda, /help                Muestra esta ayuda.
  /crear, /nueva-ia            Crea una IA personalizada y la activa.
  /asistentes, /ias            Lista tus IA y la integrada.
  /asistente [nombre], /ia     Muestra o cambia la IA activa ("ASIS" para la integrada).
  /borrar-asistente NOMBRE     Elimina una IA personalizada.
  /limpiar, /clear             Borra el historial de la conversacion.
  /historial, /history         Muestra cuantos mensajes hay en contexto.
  /modelo [nombre], /model     Muestra o cambia el modelo de Gemini.
  /modelos, /models            Lista los modelos disponibles para tu clave.
  /guardar [ruta], /save       Guarda la conversacion en Markdown.
  /estado, /status             Muestra configuracion, IA activa y arquitectura.
  /salir, /quit, /exit         Termina la sesion.

Escribe tu mensaje y pulsa Enter. Usa Ctrl+C para interrumpir una respuesta."""


# ---------------------------------------------------------------------------
# IA personalizadas
# ---------------------------------------------------------------------------


@dataclass
class Asistente:
    nombre: str
    descripcion: str = ""
    prompt: str = PROMPT_POR_DEFECTO
    modelo: str = MODELO_POR_DEFECTO

    def a_dict(self) -> dict[str, object]:
        return {
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "prompt": self.prompt,
            "modelo": self.modelo,
        }

    @classmethod
    def desde_dict(cls, datos: object) -> "Asistente":
        if not isinstance(datos, dict):
            raise ValueError("El asistente debe ser un objeto JSON.")
        nombre = str(datos.get("nombre", "")).strip()
        if not nombre:
            raise ValueError("El asistente no tiene nombre.")
        prompt = str(datos.get("prompt") or PROMPT_POR_DEFECTO)
        modelo = str(datos.get("modelo") or MODELO_POR_DEFECTO)
        return cls(
            nombre=nombre,
            descripcion=str(datos.get("descripcion") or ""),
            prompt=prompt,
            modelo=modelo,
        )


def directorio_datos() -> Path:
    base = os.environ.get("ASIS_HOME")
    return Path(base).expanduser() if base else Path.home() / ".asis"


def ruta_asistentes() -> Path:
    return directorio_datos() / "asistentes.json"


def cargar_asistentes(ruta: str | Path | None = None) -> dict[str, Asistente]:
    archivo = Path(ruta) if ruta is not None else ruta_asistentes()
    if not archivo.is_file():
        return {}

    try:
        datos = json.loads(archivo.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ErrorAsis(f"No se pudo leer {archivo}: {exc}") from exc

    lista = datos.get("asistentes") if isinstance(datos, dict) else datos
    if not isinstance(lista, list):
        raise ErrorAsis(f"El archivo {archivo} no tiene el formato esperado.")

    asistentes: dict[str, Asistente] = {}
    for elemento in lista:
        try:
            asistente = Asistente.desde_dict(elemento)
        except ValueError:
            continue
        asistentes[asistente.nombre.casefold()] = asistente
    return asistentes


def guardar_asistentes(
    asistentes: dict[str, Asistente], ruta: str | Path | None = None
) -> Path:
    archivo = Path(ruta) if ruta is not None else ruta_asistentes()
    try:
        archivo.parent.mkdir(parents=True, exist_ok=True)
        temporal = archivo.with_suffix(".tmp")
        contenido = {
            "version": 1,
            "asistentes": [a.a_dict() for a in asistentes.values()],
        }
        temporal.write_text(
            json.dumps(contenido, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporal.replace(archivo)
    except OSError as exc:
        raise ErrorAsis(f"No se pudo guardar {archivo}: {exc}") from exc
    return archivo


def guardar_asistente(asistente: Asistente, asistentes: dict[str, Asistente]) -> Path:
    asistentes[asistente.nombre.casefold()] = asistente
    return guardar_asistentes(asistentes)


def eliminar_asistente(nombre: str, asistentes: dict[str, Asistente]) -> Asistente:
    clave = nombre.casefold()
    if clave == NOMBRE_INTEGRADO.casefold():
        raise ErrorAsis("La IA integrada ASIS no se puede eliminar.")
    if clave not in asistentes:
        raise ErrorAsis(f'No existe una IA llamada "{nombre}".')
    eliminado = asistentes.pop(clave)
    guardar_asistentes(asistentes)
    return eliminado


def listar_asistentes(
    asistentes: dict[str, Asistente], actual: str = NOMBRE_INTEGRADO
) -> None:
    modelo = obtener_modelo()
    marca = "*" if actual.casefold() == NOMBRE_INTEGRADO.casefold() else " "
    print(f"{marca} {NOMBRE_INTEGRADO} (integrada, modelo {modelo})")
    for asistente in sorted(asistentes.values(), key=lambda a: a.nombre.casefold()):
        marca = "*" if actual.casefold() == asistente.nombre.casefold() else " "
        detalle = f" - {asistente.descripcion}" if asistente.descripcion else ""
        print(f"{marca} {asistente.nombre} ({asistente.modelo}){detalle}")
    if not asistentes:
        print("  (todavia no has creado ninguna IA; usa /crear)")


def crear_asistente_interactivo(
    entrada: Callable[[str], str],
    existentes: dict[str, Asistente],
) -> Asistente:
    print("Vamos a crear tu propia IA. Necesitas un nombre y sus instrucciones.")
    while True:
        nombre = entrada("Nombre de tu IA: ").strip()
        if not nombre:
            print("El nombre no puede estar vacio.")
            continue
        if nombre.casefold() == NOMBRE_INTEGRADO.casefold():
            print(f'"{NOMBRE_INTEGRADO}" esta reservado para la IA integrada.')
            continue
        if nombre.casefold() in existentes:
            print(f'Ya existe una IA llamada "{nombre}". Elige otro nombre.')
            continue
        break

    descripcion = entrada("Descripcion breve (opcional): ").strip()
    prompt = entrada("Como debe comportarse (personalidad e instrucciones): ").strip()
    modelo = entrada(f"Modelo [{MODELO_POR_DEFECTO}]: ").strip() or MODELO_POR_DEFECTO

    return Asistente(
        nombre=nombre,
        descripcion=descripcion,
        prompt=prompt or PROMPT_POR_DEFECTO,
        modelo=modelo,
    )


# ---------------------------------------------------------------------------
# Proveedor Gemini
# ---------------------------------------------------------------------------


def extraer_texto(fragmento: object) -> str:
    """Extrae texto de una respuesta del SDK sin depender de su version."""
    try:
        texto = getattr(fragmento, "text", None)
    except Exception:
        texto = None
    if texto:
        return texto

    partes = []
    for candidato in getattr(fragmento, "candidates", None) or []:
        contenido = getattr(candidato, "content", None)
        for parte in getattr(contenido, "parts", None) or []:
            texto_parte = getattr(parte, "text", None)
            if texto_parte:
                partes.append(texto_parte)
    return "".join(partes)


class ProveedorGemini:
    """Cliente fino sobre google-genai con historial propio."""

    def __init__(
        self,
        api_key: str,
        modelo: str,
        prompt: str = PROMPT_POR_DEFECTO,
    ) -> None:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:  # pragma: no cover - depende del entorno
            raise ErrorAsis(
                "Falta la libreria google-genai. Instalala con:\n"
                "  python -m pip install -r requirements.txt"
            ) from exc

        self.modelo = modelo
        self.prompt = prompt
        self._types = types
        self._cliente = genai.Client(api_key=api_key)

    def listar_modelos(self) -> list[str]:
        try:
            nombres = set()
            for modelo in self._cliente.models.list():
                nombre = str(getattr(modelo, "name", "") or "")
                if nombre.startswith("models/"):
                    nombre = nombre.split("/", 1)[1]
                acciones = getattr(modelo, "supported_actions", None) or []
                if acciones and "generateContent" not in acciones:
                    continue
                if nombre:
                    nombres.add(nombre)
        except Exception as exc:
            raise ErrorAsis(explicar_error(exc)) from exc
        return sorted(nombres)

    def _contenidos(self, historial: Sequence[dict[str, str]]):
        return [
            self._types.Content(
                role=mensaje["role"],
                parts=[self._types.Part(text=mensaje["text"])],
            )
            for mensaje in historial
        ]

    def generar(
        self,
        historial: Sequence[dict[str, str]],
        mensaje: str,
        stream: bool = True,
    ) -> Iterator[str]:
        contenidos = self._contenidos(historial)
        contenidos.append(
            self._types.Content(role="user", parts=[self._types.Part(text=mensaje)])
        )
        config = self._types.GenerateContentConfig(
            system_instruction=self.prompt
        )

        if stream:
            for fragmento in self._cliente.models.generate_content_stream(
                model=self.modelo, contents=contenidos, config=config
            ):
                texto = extraer_texto(fragmento)
                if texto:
                    yield texto
            return

        respuesta = self._cliente.models.generate_content(
            model=self.modelo, contents=contenidos, config=config
        )
        texto = extraer_texto(respuesta)
        if texto:
            yield texto


# ---------------------------------------------------------------------------
# Conversacion
# ---------------------------------------------------------------------------


def _recortar(historial: list[dict[str, str]], maximo: int) -> None:
    maximo = max(2, maximo - maximo % 2)
    if len(historial) <= maximo:
        return
    del historial[: len(historial) - maximo]


@dataclass
class Conversacion:
    proveedor: object
    historial: list[dict[str, str]] = field(default_factory=list)
    max_historial: int = MAX_HISTORIAL_POR_DEFECTO
    stream: bool = True

    def limpiar(self) -> None:
        self.historial.clear()

    def aplicar(self, asistente: Asistente) -> None:
        self.proveedor.prompt = asistente.prompt
        self.proveedor.modelo = asistente.modelo

    def aplicar_integrada(self) -> None:
        self.proveedor.prompt = obtener_prompt()
        self.proveedor.modelo = obtener_modelo()

    def responder(
        self,
        mensaje: str,
        al_fragmento: Callable[[str], None] | None = None,
    ) -> str:
        partes: list[str] = []
        try:
            for fragmento in self.proveedor.generar(
                self.historial, mensaje, stream=self.stream
            ):
                partes.append(fragmento)
                if al_fragmento is not None:
                    al_fragmento(fragmento)
        except ErrorAsis:
            raise
        except Exception as exc:
            raise ErrorAsis(explicar_error(exc)) from exc

        respuesta = "".join(partes).strip()
        if not respuesta:
            raise ErrorAsis(
                "El modelo no devolvio texto. Prueba con otro modelo o reformula la pregunta."
            )

        self.historial.append({"role": "user", "text": mensaje})
        self.historial.append({"role": "model", "text": respuesta})
        _recortar(self.historial, self.max_historial)
        return respuesta

    def guardar(self, ruta: str | Path) -> Path:
        destino = Path(ruta)
        if destino.parent and not destino.parent.exists():
            destino.parent.mkdir(parents=True, exist_ok=True)
        lineas = [
            "# Conversacion con ASIS",
            "",
            f"- Fecha: {datetime.now().isoformat(timespec='seconds')}",
            f"- Modelo: {getattr(self.proveedor, 'modelo', 'desconocido')}",
            "",
        ]
        for mensaje in self.historial:
            autor = "Tu" if mensaje["role"] == "user" else "ASIS"
            lineas.extend([f"## {autor}", "", mensaje["text"], ""])
        destino.write_text("\n".join(lineas), encoding="utf-8")
        return destino


def explicar_error(exc: Exception) -> str:
    detalle = str(exc).strip() or exc.__class__.__name__
    bajo = detalle.lower()
    if "api key" in bajo or "api_key" in bajo or "unauthenticated" in bajo:
        return (
            "La clave de API no es valida. Comprueba ASIS_GEMINI_API_KEY en tu "
            "entorno o en .env. Puedes crear una en https://aistudio.google.com/apikey"
        )
    if "quota" in bajo or "rate limit" in bajo or "429" in bajo:
        return "Se agoto la cuota o el limite de peticiones de la API. Intenta de nuevo en un momento."
    if "not found" in bajo and "model" in bajo:
        return (
            "Ese modelo no esta disponible para tu clave. Consulta los modelos "
            "disponibles con /modelos y cambia con /modelo <nombre>."
        )
    if "connect" in bajo or "timeout" in bajo or "network" in bajo:
        return "No se pudo conectar con Gemini. Revisa tu conexion a internet e intentalo de nuevo."
    return f"Error al contactar con Gemini: {detalle}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@dataclass
class Cli:
    conversacion: Conversacion
    asistentes: dict[str, Asistente] = field(default_factory=dict)
    estilo: Estilo = field(default_factory=estilo_por_defecto)
    entrada: Callable[[str], str] = input
    actual: str = NOMBRE_INTEGRADO
    activo: bool = True

    def aplicar(self, asistente: Asistente) -> None:
        self.conversacion.aplicar(asistente)
        self.actual = asistente.nombre

    def aplicar_integrada(self) -> None:
        self.conversacion.aplicar_integrada()
        self.actual = NOMBRE_INTEGRADO

    def cambiar_asistente(self, nombre: str) -> None:
        if nombre.casefold() == NOMBRE_INTEGRADO.casefold():
            self.aplicar_integrada()
            print(self.estilo.ok(f'IA activa: {NOMBRE_INTEGRADO} (integrada).'))
            return
        asistente = self.asistentes.get(nombre.casefold())
        if asistente is None:
            raise ErrorAsis(
                f'No existe una IA llamada "{nombre}". Usa /asistentes para verlas '
                "o /crear para crear una."
            )
        self.aplicar(asistente)
        print(self.estilo.ok(f"IA activa: {asistente.nombre} ({asistente.modelo})."))

    def crear(self) -> None:
        asistente = crear_asistente_interactivo(self.entrada, self.asistentes)
        ruta = guardar_asistente(asistente, self.asistentes)
        self.aplicar(asistente)
        print(self.estilo.ok(f'IA "{asistente.nombre}" creada y activada.'))
        print(self.estilo.tenue(f"Guardada en {ruta}."))

    def borrar(self, nombre: str) -> None:
        if not nombre:
            raise ErrorAsis("Indica que IA borrar: /borrar-asistente <nombre>.")
        clave = nombre.casefold()
        if clave == NOMBRE_INTEGRADO.casefold():
            raise ErrorAsis("La IA integrada ASIS no se puede eliminar.")
        asistente = self.asistentes.get(clave)
        if asistente is None:
            raise ErrorAsis(f'No existe una IA llamada "{nombre}".')
        respuesta = self.entrada(f'¿Borrar la IA "{asistente.nombre}"? [s/N]: ')
        if respuesta.strip().lower() not in {"s", "si", "sí", "y", "yes"}:
            print("Cancelado.")
            return
        eliminar_asistente(asistente.nombre, self.asistentes)
        if self.actual.casefold() == clave:
            self.aplicar_integrada()
        print(self.estilo.ok(f'IA "{asistente.nombre}" eliminada.'))

    def procesar(self, linea: str) -> None:
        partes = linea.split(maxsplit=1)
        comando = partes[0].lower()
        argumento = partes[1].strip() if len(partes) > 1 else ""

        if comando in {"/ayuda", "/help"}:
            print(AYUDA)
        elif comando in {"/limpiar", "/clear"}:
            self.conversacion.limpiar()
            print(self.estilo.ok("Historial borrado."))
        elif comando in {"/historial", "/history"}:
            turnos = len(self.conversacion.historial) // 2
            print(
                f"Mensajes en contexto: {len(self.conversacion.historial)} ({turnos} turnos)."
            )
        elif comando in {"/modelo", "/model"}:
            if argumento:
                self.conversacion.proveedor.modelo = argumento
                print(self.estilo.ok(f"Modelo cambiado a {argumento}."))
            else:
                print(f"Modelo actual: {self.conversacion.proveedor.modelo}")
        elif comando in {"/modelos", "/models"}:
            modelos = self.conversacion.proveedor.listar_modelos()
            if modelos:
                print("Modelos disponibles para tu clave:")
                for nombre in modelos:
                    print(f"  {nombre}")
            else:
                print("La API no devolvio modelos disponibles.")
        elif comando in {"/crear", "/nueva-ia", "/nueva"}:
            self.crear()
        elif comando in {"/asistentes", "/ias"}:
            listar_asistentes(self.asistentes, self.actual)
        elif comando in {"/asistente", "/ia"}:
            if argumento:
                self.cambiar_asistente(argumento)
            else:
                print(f"IA activa: {self.actual}")
        elif comando in {"/borrar-asistente", "/borrar-ia"}:
            self.borrar(argumento)
        elif comando in {"/guardar", "/save"}:
            if not self.conversacion.historial:
                print(self.estilo.tenue("No hay nada que guardar todavia."))
            else:
                ruta = argumento or f"conversacion-{datetime.now():%Y%m%d-%H%M%S}.md"
                destino = self.conversacion.guardar(ruta)
                print(self.estilo.ok(f"Conversacion guardada en {destino}."))
        elif comando in {"/estado", "/status"}:
            print(f"IA activa: {self.actual}")
            print(f"Modelo: {self.conversacion.proveedor.modelo}")
            print(f"Clave API: {enmascarar_clave(obtener_api_key())}")
            print(f"Arquitectura: {describir_arquitectura()}")
            print(
                f"Streaming: {'activo' if self.conversacion.stream else 'desactivado'}"
            )
            print(f"Historial: {len(self.conversacion.historial)} mensajes")
            print(f"Datos: {directorio_datos()}")
        elif comando in {"/salir", "/quit", "/exit"}:
            self.activo = False
        else:
            print(self.estilo.error(f"Comando desconocido: {comando}. Prueba /ayuda."))

    def ejecutar(self) -> int:
        modelo = getattr(self.conversacion.proveedor, "modelo", "?")
        print(
            f"{self.estilo.nombre(NOMBRE_APP)} v{__version__} · "
            f"IA: {self.actual} · modelo {modelo}"
        )
        print(
            self.estilo.tenue(
                "Escribe /ayuda para ver los comandos. Ctrl+C interrumpe."
            )
        )
        print()

        while self.activo:
            try:
                linea = self.entrada(self.estilo.nombre("Tu> ")).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not linea:
                continue

            if linea.startswith("/"):
                try:
                    self.procesar(linea)
                except ErrorAsis as exc:
                    print(self.estilo.error(str(exc)))
                continue

            print(self.estilo.nombre(f"{NOMBRE_APP}> "), end="", flush=True)
            try:
                self.conversacion.responder(
                    linea,
                    al_fragmento=lambda fragmento: print(fragmento, end="", flush=True),
                )
                print()
            except KeyboardInterrupt:
                print(self.estilo.tenue("\n[interrumpido]"))
            except ErrorAsis as exc:
                print(self.estilo.error(f"\n{exc}"))
            print()
        return 0


def ejecutar_repl(
    conversacion: Conversacion,
    *,
    entrada: Callable[[str], str] = input,
    estilo: Estilo | None = None,
    asistentes: dict[str, Asistente] | None = None,
    actual: str = NOMBRE_INTEGRADO,
) -> int:
    cli = Cli(
        conversacion=conversacion,
        asistentes=asistentes if asistentes is not None else {},
        estilo=estilo or estilo_por_defecto(),
        entrada=entrada,
        actual=actual,
    )
    return cli.ejecutar()


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asis",
        description="ASIS: crea tus propias IA y conversa con ellas en la terminal.",
    )
    parser.add_argument(
        "pregunta",
        nargs="*",
        help="Pregunta para una sola respuesta. Sin pregunta se abre la conversacion.",
    )
    parser.add_argument(
        "-m", "--modelo", "--model", dest="modelo", help="Modelo de Gemini a usar."
    )
    parser.add_argument(
        "--sistema", "--system", dest="sistema", help="Instruccion de sistema personalizada."
    )
    parser.add_argument(
        "-a", "--asistente", dest="asistente", help="Nombre de la IA personalizada a usar."
    )
    parser.add_argument(
        "--crear",
        action="store_true",
        help="Crea una IA personalizada y termina (no usa la clave de API).",
    )
    parser.add_argument(
        "--lista-asistentes",
        "--asistentes",
        dest="lista_asistentes",
        action="store_true",
        help="Lista tus IA personalizadas y termina.",
    )
    parser.add_argument(
        "--lista-modelos",
        dest="lista_modelos",
        action="store_true",
        help="Lista los modelos disponibles para tu clave y termina.",
    )
    parser.add_argument(
        "--sin-streaming",
        "--no-stream",
        action="store_true",
        dest="no_stream",
        help="Espera la respuesta completa en lugar de mostrarla por partes.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Valida la configuracion y termina sin abrir la conversacion.",
    )
    parser.add_argument("--version", action="version", version=f"ASIS {__version__}")
    return parser


def _error_sin_clave(estilo: Estilo) -> int:
    print(
        estilo.error("No se encontro la clave de API de Gemini.")
        + "\n\nConfigura ASIS_GEMINI_API_KEY antes de ejecutar ASIS:\n"
        "  Windows (PowerShell):  $env:ASIS_GEMINI_API_KEY=\"tu_clave\"\n"
        "  macOS / Linux:         export ASIS_GEMINI_API_KEY=\"tu_clave\"\n\n"
        "O crea un archivo .env a partir de .env.example. Consigue una clave en:\n"
        "  https://aistudio.google.com/apikey"
    )
    return 2


def main(
    argv: Sequence[str] | None = None,
    *,
    fabrica_proveedor: Callable[..., object] | None = None,
    entrada: Callable[[str], str] = input,
    estilo: Estilo | None = None,
) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    estilo = estilo or estilo_por_defecto()

    cargar_dotenv()

    if not es_64_bits():
        print(
            estilo.tenue(
                "Aviso: Python de 32 bits detectado. ASIS funciona, pero se "
                "recomienda un interprete de 64 bits para usar todos los modelos "
                "y generar ejecutables de 64 bits."
            ),
            file=sys.stderr,
        )

    try:
        asistentes = cargar_asistentes()
    except ErrorAsis as exc:
        print(estilo.error(str(exc)))
        asistentes = {}

    if args.crear:
        try:
            asistente = crear_asistente_interactivo(entrada, asistentes)
            ruta = guardar_asistente(asistente, asistentes)
        except ErrorAsis as exc:
            print(estilo.error(str(exc)))
            return 2
        print(estilo.ok(f'IA "{asistente.nombre}" creada.'))
        print(estilo.tenue(f"Guardada en {ruta}."))
        print(f'Usala con: asis --asistente "{asistente.nombre}"')
        return 0

    if args.lista_asistentes:
        listar_asistentes(asistentes)
        return 0

    try:
        api_key = obtener_api_key()
        if not api_key:
            return _error_sin_clave(estilo)

        perfil: Asistente | None = None
        seleccion = args.asistente or os.environ.get("ASIS_ASISTENTE")
        if seleccion and seleccion.casefold() != NOMBRE_INTEGRADO.casefold():
            perfil = asistentes.get(seleccion.casefold())
            if perfil is None:
                raise ErrorAsis(
                    f'No existe una IA llamada "{seleccion}". Usa --lista-asistentes '
                    "para verlas o --crear para crear una."
                )

        modelo = args.modelo or (perfil.modelo if perfil else obtener_modelo())
        sistema = args.sistema or (perfil.prompt if perfil else obtener_prompt())
        actual = perfil.nombre if perfil else NOMBRE_INTEGRADO
        max_historial = obtener_max_historial()
    except ErrorAsis as exc:
        print(estilo.error(str(exc)))
        return 2

    if args.check:
        print(estilo.ok("Configuracion correcta."))
        print(f"IA activa: {actual}")
        print(f"Modelo: {modelo}")
        print(f"Clave API: {enmascarar_clave(api_key)}")
        print(f"Arquitectura: {describir_arquitectura()}")
        print(f"Streaming: {'si' if not args.no_stream else 'no'}")
        print(f"Datos: {directorio_datos()}")
        return 0

    fabrica = fabrica_proveedor or ProveedorGemini
    try:
        proveedor = fabrica(api_key=api_key, modelo=modelo, prompt=sistema)
    except ErrorAsis as exc:
        print(estilo.error(str(exc)))
        return 2

    if args.lista_modelos:
        try:
            modelos = proveedor.listar_modelos()
        except ErrorAsis as exc:
            print(estilo.error(str(exc)))
            return 1
        if not modelos:
            print("La API no devolvio modelos disponibles.")
            return 0
        for nombre in modelos:
            print(nombre)
        return 0

    conversacion = Conversacion(
        proveedor=proveedor,
        max_historial=max_historial,
        stream=not args.no_stream,
    )

    if args.pregunta:
        pregunta = " ".join(args.pregunta).strip()
        return _responder_una_vez(conversacion, pregunta, estilo)

    if not sys.stdin.isatty():
        pregunta = sys.stdin.read().strip()
        if pregunta:
            return _responder_una_vez(conversacion, pregunta, estilo)

    try:
        return ejecutar_repl(
            conversacion,
            entrada=entrada,
            estilo=estilo,
            asistentes=asistentes,
            actual=actual,
        )
    except ErrorAsis as exc:
        print(estilo.error(str(exc)))
        return 1


def _responder_una_vez(conversacion: Conversacion, pregunta: str, estilo: Estilo) -> int:
    try:
        conversacion.responder(
            pregunta,
            al_fragmento=lambda fragmento: print(fragmento, end="", flush=True),
        )
        print()
        return 0
    except KeyboardInterrupt:
        print(estilo.tenue("\n[interrumpido]"))
        return 130
    except ErrorAsis as exc:
        print(estilo.error(str(exc)))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
