"""
============================================================
 SCRIPT: Migrar Playlist de Spotify a YouTube Music
============================================================
 Este script toma todas las canciones de una playlist de Spotify
 y las busca/agrega a una nueva playlist en YouTube Music.

 Autor: b0nfire
 Fecha: 2026-02-28
 version: 1.1

 REQUISITOS:
   - Python 3.8 o superior
   - Credenciales de Spotify Developer (ver GUIA_PASO_A_PASO.md)
   - Cuenta de YouTube Music autenticada (ver GUIA_PASO_A_PASO.md)
============================================================
"""

import sys

# --- Librerías externas ---
try:
    from src.main import migrar
except ImportError as e:
    print("=" * 60)
    print("❌ ERROR: Faltan librerías por instalar o módulos no encontrados.")
    print(f"   Detalle: {e}")
    print()
    print("   Ejecuta este comando para instalarlas:")
    print("   pip install -r requirements.txt")
    print("=" * 60)
    sys.exit(1)

# ============================================================
# PUNTO DE ENTRADA
# ============================================================
if __name__ == "__main__":
    try:
        migrar()
    except KeyboardInterrupt:
        print("\n\n⏹️  Migración cancelada por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        print("   Si el error persiste, reporta el problema.")
        sys.exit(1)
