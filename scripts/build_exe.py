"""Genera un ejecutable de 64 bits de ASIS con PyInstaller."""

import struct
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def main() -> int:
    if struct.calcsize("P") * 8 != 64:
        print(
            "ERROR: se requiere un Python de 64 bits para generar un ejecutable "
            "de 64 bits. Instala Python desde https://www.python.org/downloads/windows/"
        )
        return 2

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print(
            "Falta PyInstaller. Instalalo con:\n"
            "  python -m pip install -r requirements-dev.txt"
        )
        return 2

    print("Construyendo ASIS de 64 bits...")
    orden = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--console",
        "--name",
        "ASIS",
        str(RAIZ / "asis.py"),
    ]
    codigo = subprocess.call(orden, cwd=RAIZ)
    if codigo == 0:
        salida = RAIZ / "dist" / ("ASIS.exe" if sys.platform == "win32" else "ASIS")
        print(f"Listo: {salida}")
        print("Verifica con: ASIS --version")
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
