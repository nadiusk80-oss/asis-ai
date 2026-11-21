"""Pruebas de ASIS. No requieren conexion ni clave de API real."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import asis


class ProveedorFalso:
    def __init__(self, fragmentos=("Hola", ", mundo"), error=None):
        self.modelo = "modelo-falso"
        self.prompt = "prompt-falso"
        self.temperatura = 0.7
        self.fragmentos = fragmentos
        self.error = error
        self.llamadas = []

    def generar(self, historial, mensaje, stream=True):
        self.llamadas.append(([dict(m) for m in historial], mensaje, stream))
        if self.error is not None:
            raise self.error
        yield from self.fragmentos


class EntradaFalsa(io.StringIO):
    def isatty(self):
        return False


def entorno(**valores):
    return mock.patch.dict(os.environ, valores, clear=True)


def ejecutar_main(argv, **kwargs):
    salida = io.StringIO()
    with redirect_stdout(salida):
        codigo = asis.main(argv, **kwargs)
    return codigo, salida.getvalue()


def crear_cli(asistentes=None, entrada=None, conversacion=None):
    conversacion = conversacion or asis.Conversacion(proveedor=ProveedorFalso())
    return asis.Cli(
        conversacion=conversacion,
        asistentes=asistentes if asistentes is not None else {},
        estilo=asis.Estilo(activo=False),
        entrada=entrada or (lambda _: ""),
    )


def ejecutar_comando(cli, linea):
    salida = io.StringIO()
    with redirect_stdout(salida):
        cli.procesar(linea)
    return salida.getvalue()


class PruebasConfiguracion(unittest.TestCase):
    def test_cargar_dotenv_lee_valores_y_no_sobrescribe(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / ".env"
            ruta.write_text(
                'A=valor\n# comentario\nB="dos palabras"\nexport C=3\nA=otro\n\n',
                encoding="utf-8",
            )
            with mock.patch.dict(os.environ, {"A": "previo"}, clear=True):
                cargadas = asis.cargar_dotenv(ruta)
                self.assertEqual(os.environ["A"], "previo")
                self.assertEqual(os.environ["B"], "dos palabras")
                self.assertEqual(os.environ["C"], "3")
            self.assertEqual(cargadas["A"], "otro")

    def test_cargar_dotenv_rellena_variables_vacias(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / ".env"
            ruta.write_text("ASIS_MODEL=modelo-desde-env\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"ASIS_MODEL": ""}, clear=True):
                asis.cargar_dotenv(ruta)
                self.assertEqual(os.environ["ASIS_MODEL"], "modelo-desde-env")

    def test_cargar_dotenv_sin_archivo(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(asis.cargar_dotenv("no-existe.env"), {})

    def test_api_key_prefiere_variable_asis(self):
        with entorno(ASIS_GEMINI_API_KEY="asis", GEMINI_API_KEY="gemini"):
            self.assertEqual(asis.obtener_api_key(), "asis")

    def test_temperatura_se_limita_entre_0_y_2(self):
        with entorno(ASIS_TEMPERATURE="9"):
            self.assertEqual(asis.obtener_temperatura(), 2.0)
        with entorno(ASIS_TEMPERATURE="-3"):
            self.assertEqual(asis.obtener_temperatura(), 0.0)

    def test_temperatura_invalida(self):
        with entorno(ASIS_TEMPERATURE="alta"):
            with self.assertRaises(asis.ErrorAsis):
                asis.obtener_temperatura()

    def test_historial_invalido(self):
        with entorno(ASIS_MAX_HISTORY="muchos"):
            with self.assertRaises(asis.ErrorAsis):
                asis.obtener_max_historial()

    def test_enmascarar_clave(self):
        self.assertEqual(asis.enmascarar_clave(None), "no configurada")
        self.assertEqual(asis.enmascarar_clave("corta"), "***")
        self.assertEqual(asis.enmascarar_clave("abcdefghijklmnop"), "abcd...mnop")

    def test_arquitectura_describe_bits(self):
        self.assertIn("bits", asis.describir_arquitectura())


class PruebasAsistentes(unittest.TestCase):
    def test_guardar_cargar_y_eliminar(self):
        with tempfile.TemporaryDirectory() as tmp, entorno(ASIS_HOME=tmp):
            asistente = asis.Asistente(
                nombre="Tutor",
                descripcion="Ayuda a estudiar",
                prompt="Se un tutor paciente",
                modelo="gemini-2.5-pro",
                temperatura=0.4,
            )
            asistentes = {}
            ruta = asis.guardar_asistente(asistente, asistentes)

            self.assertTrue(ruta.is_file())
            cargados = asis.cargar_asistentes()
            self.assertEqual(cargados["tutor"].modelo, "gemini-2.5-pro")
            self.assertEqual(cargados["tutor"].temperatura, 0.4)

            eliminado = asis.eliminar_asistente("Tutor", cargados)
            self.assertEqual(eliminado.nombre, "Tutor")
            self.assertEqual(asis.cargar_asistentes(), {})

    def test_no_se_puede_eliminar_la_integrada(self):
        with self.assertRaises(asis.ErrorAsis):
            asis.eliminar_asistente("ASIS", {})

    def test_archivo_con_formato_invalido(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "asistentes.json"
            ruta.write_text('{"asistentes": "no es lista"}', encoding="utf-8")
            with self.assertRaises(asis.ErrorAsis):
                asis.cargar_asistentes(ruta)

    def test_desde_dict_ignora_temperatura_invalida(self):
        asistente = asis.Asistente.desde_dict(
            {"nombre": "X", "temperatura": "muy alta"}
        )
        self.assertEqual(asistente.temperatura, asis.TEMPERATURA_POR_DEFECTO)
        self.assertEqual(asistente.modelo, asis.MODELO_POR_DEFECTO)

    def test_wizard_crea_asistente(self):
        respuestas = iter(
            ["Mi IA", "Para cocinar", "Se un chef breve", "gemini-2.5-pro", "0.3"]
        )
        with redirect_stdout(io.StringIO()):
            asistente = asis.crear_asistente_interactivo(
                lambda _: next(respuestas), {}
            )
        self.assertEqual(asistente.nombre, "Mi IA")
        self.assertEqual(asistente.prompt, "Se un chef breve")
        self.assertEqual(asistente.modelo, "gemini-2.5-pro")
        self.assertEqual(asistente.temperatura, 0.3)

    def test_wizard_rechaza_nombres_y_temperaturas_invalidas(self):
        respuestas = iter(
            ["ASIS", "Mi IA", "", "", "", "alta", "3", "0.5"]
        )
        salida = io.StringIO()
        with redirect_stdout(salida):
            asistente = asis.crear_asistente_interactivo(
                lambda _: next(respuestas), {}
            )
        self.assertEqual(asistente.nombre, "Mi IA")
        self.assertEqual(asistente.prompt, asis.PROMPT_POR_DEFECTO)
        self.assertEqual(asistente.temperatura, 0.5)
        self.assertIn("reservado", salida.getvalue())


class PruebasConversacion(unittest.TestCase):
    def test_respuesta_en_streaming_y_historial(self):
        proveedor = ProveedorFalso()
        conversacion = asis.Conversacion(proveedor=proveedor, stream=False)
        fragmentos = []

        respuesta = conversacion.responder("Hola", al_fragmento=fragmentos.append)

        self.assertEqual(respuesta, "Hola, mundo")
        self.assertEqual(fragmentos, ["Hola", ", mundo"])
        self.assertEqual(
            conversacion.historial,
            [
                {"role": "user", "text": "Hola"},
                {"role": "model", "text": "Hola, mundo"},
            ],
        )
        self.assertFalse(proveedor.llamadas[0][2])

    def test_historial_se_recorta_en_pares(self):
        conversacion = asis.Conversacion(
            proveedor=ProveedorFalso(), max_historial=3, stream=True
        )
        for numero in range(3):
            conversacion.responder(f"mensaje {numero}")

        self.assertEqual(len(conversacion.historial), 2)
        self.assertEqual(conversacion.historial[0]["role"], "user")
        self.assertEqual(conversacion.historial[0]["text"], "mensaje 2")

    def test_error_del_proveedor_se_traduce(self):
        proveedor = ProveedorFalso(error=RuntimeError("429 quota exceeded"))
        conversacion = asis.Conversacion(proveedor=proveedor)

        with self.assertRaises(asis.ErrorAsis) as ctx:
            conversacion.responder("Hola")
        self.assertIn("cuota", str(ctx.exception))
        self.assertEqual(conversacion.historial, [])

    def test_respuesta_vacia(self):
        conversacion = asis.Conversacion(proveedor=ProveedorFalso(fragmentos=("",)))
        with self.assertRaises(asis.ErrorAsis):
            conversacion.responder("Hola")

    def test_guardar_conversacion(self):
        conversacion = asis.Conversacion(proveedor=ProveedorFalso())
        conversacion.responder("Hola")

        with tempfile.TemporaryDirectory() as tmp:
            ruta = conversacion.guardar(Path(tmp) / "charla.md")
            texto = ruta.read_text(encoding="utf-8")

        self.assertIn("# Conversacion con ASIS", texto)
        self.assertIn("## Tu", texto)
        self.assertIn("## ASIS", texto)
        self.assertIn("Hola, mundo", texto)

    def test_aplicar_asistente(self):
        conversacion = asis.Conversacion(proveedor=ProveedorFalso())
        conversacion.aplicar(
            asis.Asistente(
                nombre="Chef",
                prompt="Cocina",
                modelo="m1",
                temperatura=0.2,
            )
        )
        self.assertEqual(conversacion.proveedor.prompt, "Cocina")
        self.assertEqual(conversacion.proveedor.modelo, "m1")
        self.assertEqual(conversacion.proveedor.temperatura, 0.2)


class PruebasComandos(unittest.TestCase):
    def test_ayuda(self):
        self.assertIn(
            "Comandos disponibles", ejecutar_comando(crear_cli(), "/ayuda")
        )

    def test_limpiar(self):
        cli = crear_cli()
        cli.conversacion.responder("Hola")
        self.assertIn("Historial borrado", ejecutar_comando(cli, "/clear"))
        self.assertEqual(cli.conversacion.historial, [])

    def test_cambiar_modelo(self):
        cli = crear_cli()
        self.assertIn(
            "Modelo cambiado a gemini-2.5-pro",
            ejecutar_comando(cli, "/modelo gemini-2.5-pro"),
        )
        self.assertEqual(cli.conversacion.proveedor.modelo, "gemini-2.5-pro")

    def test_modelo_sin_argumento(self):
        self.assertIn(
            "modelo-falso", ejecutar_comando(crear_cli(), "/model")
        )

    def test_crear_ia_desde_la_conversacion(self):
        with tempfile.TemporaryDirectory() as tmp, entorno(ASIS_HOME=tmp):
            respuestas = iter(["Chef", "Cocina", "Se un chef", "", "0.4"])
            cli = crear_cli(entrada=lambda _: next(respuestas))
            salida = ejecutar_comando(cli, "/crear")

            self.assertIn('IA "Chef" creada y activada', salida)
            self.assertEqual(cli.actual, "Chef")
            self.assertEqual(cli.conversacion.proveedor.prompt, "Se un chef")
            self.assertTrue((Path(tmp) / "asistentes.json").is_file())
            self.assertEqual(asis.cargar_asistentes()["chef"].nombre, "Chef")

    def test_listar_y_cambiar_asistentes(self):
        asistentes = {
            "chef": asis.Asistente(nombre="Chef", prompt="Cocina", modelo="m-chef")
        }
        cli = crear_cli(asistentes=asistentes)

        salida = ejecutar_comando(cli, "/asistentes")
        self.assertIn("* ASIS", salida)
        self.assertIn("Chef (m-chef)", salida)

        salida = ejecutar_comando(cli, "/asistente Chef")
        self.assertIn("IA activa: Chef", salida)
        self.assertEqual(cli.actual, "Chef")
        self.assertEqual(cli.conversacion.proveedor.prompt, "Cocina")
        self.assertEqual(cli.conversacion.proveedor.modelo, "m-chef")

        salida = ejecutar_comando(cli, "/asistente ASIS")
        self.assertIn("ASIS (integrada)", salida)
        self.assertEqual(cli.actual, "ASIS")
        self.assertEqual(cli.conversacion.proveedor.modelo, asis.obtener_modelo())

    def test_asistente_inexistente(self):
        cli = crear_cli()
        with redirect_stdout(io.StringIO()):
            with self.assertRaises(asis.ErrorAsis):
                cli.procesar("/asistente Fantasma")

    def test_borrar_asistente(self):
        with tempfile.TemporaryDirectory() as tmp, entorno(ASIS_HOME=tmp):
            asistente = asis.Asistente(nombre="Chef", prompt="Cocina")
            asistentes = {}
            asis.guardar_asistente(asistente, asistentes)

            cli = crear_cli(asistentes=asistentes, entrada=lambda _: "s")
            cli.aplicar(asistente)
            salida = ejecutar_comando(cli, "/borrar-asistente Chef")

            self.assertIn("eliminada", salida)
            self.assertEqual(cli.actual, "ASIS")
            self.assertEqual(asis.cargar_asistentes(), {})

    def test_borrar_asistente_cancelado(self):
        asistente = asis.Asistente(nombre="Chef", prompt="Cocina")
        asistentes = {"chef": asistente}
        cli = crear_cli(asistentes=asistentes, entrada=lambda _: "n")

        salida = ejecutar_comando(cli, "/borrar-asistente Chef")
        self.assertIn("Cancelado", salida)
        self.assertIn("chef", cli.asistentes)

    def test_guardar_sin_historial(self):
        self.assertIn(
            "No hay nada que guardar", ejecutar_comando(crear_cli(), "/guardar")
        )

    def test_estado_muestra_clave_enmascarada_y_arquitectura(self):
        cli = crear_cli()
        with tempfile.TemporaryDirectory() as tmp, entorno(
            ASIS_GEMINI_API_KEY="abcdefghijklmnop", ASIS_HOME=tmp
        ):
            salida = ejecutar_comando(cli, "/estado")
        self.assertIn("abcd...mnop", salida)
        self.assertNotIn("abcdefghijklmnop", salida)
        self.assertIn("Arquitectura:", salida)
        self.assertIn("bits", salida)

    def test_comando_desconocido(self):
        self.assertIn(
            "Comando desconocido", ejecutar_comando(crear_cli(), "/voltereta")
        )


class PruebasRepl(unittest.TestCase):
    def test_conversacion_interactiva(self):
        conversacion = asis.Conversacion(proveedor=ProveedorFalso())
        respuestas = iter(["hola", "/modelo g-x", "otra", "/salir"])
        salida = io.StringIO()

        with redirect_stdout(salida):
            codigo = asis.ejecutar_repl(
                conversacion,
                entrada=lambda _: next(respuestas),
                estilo=asis.Estilo(activo=False),
            )

        texto = salida.getvalue()
        self.assertEqual(codigo, 0)
        self.assertIn("ASIS v", texto)
        self.assertIn("IA: ASIS", texto)
        self.assertIn("Hola, mundo", texto)
        self.assertIn("Modelo cambiado a g-x", texto)
        self.assertEqual(conversacion.proveedor.modelo, "g-x")
        self.assertEqual(len(conversacion.proveedor.llamadas), 2)

    def test_salida_al_final_del_stdin(self):
        conversacion = asis.Conversacion(proveedor=ProveedorFalso())

        def entrada(_):
            raise EOFError

        with redirect_stdout(io.StringIO()):
            codigo = asis.ejecutar_repl(conversacion, entrada=entrada)

        self.assertEqual(codigo, 0)


class PruebasMain(unittest.TestCase):
    def test_sin_clave_api(self):
        with tempfile.TemporaryDirectory() as tmp, entorno(ASIS_HOME=tmp), mock.patch.object(
            asis, "cargar_dotenv", return_value={}
        ):
            codigo, salida = ejecutar_main([])
        self.assertEqual(codigo, 2)
        self.assertIn("No se encontro la clave de API", salida)

    def test_check_valida_configuracion(self):
        with tempfile.TemporaryDirectory() as tmp, entorno(
            ASIS_GEMINI_API_KEY="clave-de-prueba", ASIS_HOME=tmp
        ), mock.patch.object(asis, "cargar_dotenv", return_value={}):
            codigo, salida = ejecutar_main(["--check"])
        self.assertEqual(codigo, 0)
        self.assertIn("Configuracion correcta", salida)
        self.assertIn("gemini-2.5-flash", salida)
        self.assertIn("Arquitectura:", salida)
        self.assertIn("bits", salida)

    def test_crear_ia_sin_clave(self):
        with tempfile.TemporaryDirectory() as tmp, entorno(ASIS_HOME=tmp), mock.patch.object(
            asis, "cargar_dotenv", return_value={}
        ):
            respuestas = iter(["Chef", "Cocina", "Se un chef", "", ""])
            codigo, salida = ejecutar_main(
                ["--crear"], entrada=lambda _: next(respuestas)
            )
            self.assertEqual(codigo, 0)
            self.assertIn('IA "Chef" creada', salida)
            self.assertTrue((Path(tmp) / "asistentes.json").is_file())

    def test_listar_asistentes(self):
        with tempfile.TemporaryDirectory() as tmp, entorno(ASIS_HOME=tmp), mock.patch.object(
            asis, "cargar_dotenv", return_value={}
        ):
            asis.guardar_asistente(
                asis.Asistente(nombre="Chef", descripcion="Cocina"), {}
            )
            codigo, salida = ejecutar_main(["--lista-asistentes"])
        self.assertEqual(codigo, 0)
        self.assertIn("Chef (gemini-2.5-flash)", salida)
        self.assertIn("Cocina", salida)

    def test_una_sola_pregunta(self):
        fabrica = mock.Mock(return_value=ProveedorFalso())
        with tempfile.TemporaryDirectory() as tmp, entorno(
            ASIS_GEMINI_API_KEY="clave-de-prueba", ASIS_HOME=tmp
        ), mock.patch.object(asis, "cargar_dotenv", return_value={}):
            codigo, salida = ejecutar_main(["hola"], fabrica_proveedor=fabrica)

        self.assertEqual(codigo, 0)
        self.assertIn("Hola, mundo", salida)
        self.assertEqual(fabrica.call_args.kwargs["api_key"], "clave-de-prueba")
        self.assertEqual(fabrica.call_args.kwargs["modelo"], asis.MODELO_POR_DEFECTO)

    def test_usa_la_ia_seleccionada(self):
        fabrica = mock.Mock(return_value=ProveedorFalso())
        with tempfile.TemporaryDirectory() as tmp, entorno(
            ASIS_GEMINI_API_KEY="clave-de-prueba", ASIS_HOME=tmp
        ), mock.patch.object(asis, "cargar_dotenv", return_value={}):
            asis.guardar_asistente(
                asis.Asistente(
                    nombre="Chef",
                    prompt="Se un chef",
                    modelo="m-chef",
                    temperatura=0.3,
                ),
                {},
            )
            codigo, _ = ejecutar_main(
                ["--asistente", "Chef", "--modelo", "m-otro", "hola"],
                fabrica_proveedor=fabrica,
            )

        self.assertEqual(codigo, 0)
        kwargs = fabrica.call_args.kwargs
        self.assertEqual(kwargs["modelo"], "m-otro")
        self.assertEqual(kwargs["prompt"], "Se un chef")
        self.assertEqual(kwargs["temperatura"], 0.3)

    def test_ia_inexistente(self):
        with tempfile.TemporaryDirectory() as tmp, entorno(
            ASIS_GEMINI_API_KEY="clave-de-prueba", ASIS_HOME=tmp
        ), mock.patch.object(asis, "cargar_dotenv", return_value={}):
            codigo, salida = ejecutar_main(["--asistente", "Fantasma", "hola"])
        self.assertEqual(codigo, 2)
        self.assertIn("No existe una IA llamada", salida)

    def test_stdin_redirigido(self):
        fabrica = mock.Mock(return_value=ProveedorFalso())
        with tempfile.TemporaryDirectory() as tmp, entorno(
            ASIS_GEMINI_API_KEY="clave-de-prueba", ASIS_HOME=tmp
        ), mock.patch.object(asis, "cargar_dotenv", return_value={}), mock.patch.object(
            asis.sys, "stdin", EntradaFalsa("pregunta desde pipe\n")
        ):
            codigo, salida = ejecutar_main([], fabrica_proveedor=fabrica)

        self.assertEqual(codigo, 0)
        self.assertIn("Hola, mundo", salida)
        self.assertEqual(fabrica.return_value.llamadas[0][1], "pregunta desde pipe")


class PruebasSdk(unittest.TestCase):
    def test_extraer_texto_desde_candidatos(self):
        class Parte:
            text = "hola"

        class Contenido:
            parts = [Parte()]

        class Candidato:
            content = Contenido()

        class Respuesta:
            candidates = [Candidato()]

        self.assertEqual(asis.extraer_texto(Respuesta()), "hola")

    def test_conversion_de_historial(self):
        try:
            from google.genai import types
        except ImportError:  # pragma: no cover
            self.skipTest("google-genai no esta instalado")

        proveedor = asis.ProveedorGemini.__new__(asis.ProveedorGemini)
        proveedor._types = types
        contenidos = proveedor._contenidos(
            [
                {"role": "user", "text": "pregunta"},
                {"role": "model", "text": "respuesta"},
            ]
        )

        self.assertEqual([c.role for c in contenidos], ["user", "model"])
        self.assertEqual(contenidos[0].parts[0].text, "pregunta")


if __name__ == "__main__":
    unittest.main()
