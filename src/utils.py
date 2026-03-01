import re
import time
from datetime import datetime


def limpiar_nombre_cancion(nombre):
    """
    Limpia el nombre de una canción para mejorar la búsqueda.
    Elimina cosas como "(feat. ...)", "(Remix)", etc.
    que pueden hacer que la búsqueda falle en YouTube Music.
    """
    patrones_a_eliminar = [
        r"\(feat\..*?\)",  # (feat. Artista)
        r"\(ft\..*?\)",  # (ft. Artista)
        r"\(with.*?\)",  # (with Artista)
        r"\(Remastered.*?\)",  # (Remastered 2023)
        r"\(Deluxe.*?\)",  # (Deluxe Edition)
        r"\- Remastered.*",  # - Remastered 2023
        r"\- Bonus Track",  # - Bonus Track
    ]
    nombre_limpio = nombre
    for patron in patrones_a_eliminar:
        nombre_limpio = re.sub(patron, "", nombre_limpio, flags=re.IGNORECASE)

    nombre_limpio = " ".join(nombre_limpio.split())
    return nombre_limpio.strip()


def extraer_playlist_id(url_playlist):
    """
    Extrae el ID de la playlist desde la URL de Spotify.
    """
    if url_playlist.startswith("spotify:playlist:"):
        return url_playlist.split(":")[-1]

    match = re.search(r"playlist[/:]([a-zA-Z0-9]+)", url_playlist)
    if match:
        return match.group(1)

    if re.match(r"^[a-zA-Z0-9]+$", url_playlist):
        return url_playlist

    return None


def limpiar_texto_yt(texto):
    """Mantiene letras, números, espacios y puntuación básica para títulos en YT."""
    return re.sub(r"[^\w\s.,!?-]", "", texto).strip()


def guardar_canciones_no_encontradas(
    canciones_fallidas, archivo="canciones_no_encontradas.txt"
):
    """
    Guarda la lista de canciones que no se encontraron en YouTube Music
    """
    if not canciones_fallidas:
        return

    with open(archivo, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(" CANCIONES NO ENCONTRADAS EN YOUTUBE MUSIC\n")
        f.write(f" Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f" Total: {len(canciones_fallidas)} canciones\n")
        f.write("=" * 60 + "\n\n")
        f.write(" Estas canciones no se pudieron encontrar automáticamente.\n")
        f.write(" Puedes buscarlas manualmente en YouTube Music y agregarlas.\n\n")
        f.write("-" * 60 + "\n\n")

        for i, cancion in enumerate(canciones_fallidas, 1):
            f.write(f"{i:4d}. {cancion['artista']} — {cancion['nombre']}\n")
            f.write(f"      Álbum: {cancion['album']}\n\n")
            if cancion.get("motivo"):
                f.write(f"      Motivo: {cancion['motivo']}\n\n")

    print(f"\n📝 Lista de canciones no encontradas guardada en: {archivo}")


def formato_tiempo_estimado(segundos):
    """Formatea segundos en una cadena hh:mm:ss legible."""
    m, s = divmod(int(segundos), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    elif m > 0:
        return f"{m}m {s}s"
    else:
        return f"{s}s"
