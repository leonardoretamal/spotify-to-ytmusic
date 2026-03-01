"""
============================================================
 SCRIPT: Migrar Playlist de Spotify a YouTube Music
============================================================
 Este script toma todas las canciones de una playlist de Spotify
 y las busca/agrega a una nueva playlist en YouTube Music.

 Autor: b0nfire
 Fecha: 2026-02-28
 version: 1.0

 REQUISITOS:
   - Python 3.8 o superior
   - Credenciales de Spotify Developer (ver GUIA_PASO_A_PASO.md)
   - Cuenta de YouTube Music autenticada (ver GUIA_PASO_A_PASO.md)
============================================================
"""

import os
import re
import sys
import time
import json
from datetime import datetime

# --- Librerías externas ---
try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    import ytmusicapi
    from ytmusicapi import YTMusic
    from ytmusicapi.auth.oauth import OAuthCredentials
    from dotenv import load_dotenv
    from tqdm import tqdm
except ImportError as e:
    print("=" * 60)
    print("❌ ERROR: Faltan librerías por instalar.")
    print(f"   Detalle: {e}")
    print()
    print("   Ejecuta este comando para instalarlas:")
    print("   pip install -r requirements.txt")
    print("=" * 60)
    sys.exit(1)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================


def limpiar_nombre_cancion(nombre):
    """
    Limpia el nombre de una canción para mejorar la búsqueda.
    Elimina cosas como "(feat. ...)", "(Remix)", etc.
    que pueden hacer que la búsqueda falle en YouTube Music.
    """
    # Eliminar texto entre paréntesis que suele causar problemas
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

    # Eliminar espacios extra
    nombre_limpio = " ".join(nombre_limpio.split())
    return nombre_limpio.strip()


def extraer_playlist_id(url_playlist):
    """
    Extrae el ID de la playlist desde la URL de Spotify.
    Soporta URLs como:
      - https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
      - https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=abc123
      - spotify:playlist:37i9dQZF1DXcBWIGoYBM5M
    """
    # Si es una URI de Spotify (spotify:playlist:ID)
    if url_playlist.startswith("spotify:playlist:"):
        return url_playlist.split(":")[-1]

    # Si es una URL web
    match = re.search(r"playlist[/:]([a-zA-Z0-9]+)", url_playlist)
    if match:
        return match.group(1)

    # Si parece ser directamente un ID
    if re.match(r"^[a-zA-Z0-9]+$", url_playlist):
        return url_playlist

    return None


def obtener_canciones_spotify(sp, playlist_id):
    """
    Obtiene TODAS las canciones de una playlist de Spotify.
    Maneja la paginación automáticamente (Spotify devuelve máx. 100 por request).

    Retorna una lista de diccionarios con la info de cada canción:
    [{"nombre": "...", "artista": "...", "album": "..."}, ...]
    """
    canciones = []
    offset = 0
    limite = 100  # Máximo permitido por Spotify

    print("\n🎵 Obteniendo canciones de Spotify...")

    # Primera llamada para saber el total
    # IMPORTANTE: spotify eliminó el endpoint /tracks en 2026, así que
    # no podemos usar sp.playlist_items() porque internamente usa /tracks y da 403.
    # Tenemos que hacer la petición manualmente al nuevo endpoint /items
    resultados = sp._get(
        f"playlists/{playlist_id}/items",
        offset=offset,
        limit=limite,
        additional_types="track",
    )
    total = resultados["total"]
    print(f"   📊 Total de canciones en la playlist: {total}")

    # Barra de progreso para la descarga de datos de Spotify
    with tqdm(total=total, desc="   Descargando de Spotify", unit="canción") as barra:
        while True:
            resultados = sp._get(
                f"playlists/{playlist_id}/items",
                offset=offset,
                limit=limite,
                additional_types="track",
            )

            for item in resultados["items"]:
                # La nueva API a veces devuelve la info en la llave 'track'
                # y otras veces en la llave 'item' (dependiendo del tipo de request).
                # Si no está en ninguno, asumimos que 'item' ya es el track directo.
                track = item.get("track") or item.get("item") or item

                # Saltar canciones eliminadas o no disponibles
                if not track or not isinstance(track, dict):
                    barra.update(1)
                    continue

                nombre = track.get("name", "Desconocido")
                # Unir todos los artistas con coma
                artistas = ", ".join(
                    artista["name"] for artista in track.get("artists", [])
                )
                album = track.get("album", {}).get("name", "Desconocido")

                canciones.append(
                    {"nombre": nombre, "artista": artistas, "album": album}
                )
                barra.update(1)

            # ¿Hay más páginas?
            if resultados.get("next") is None:
                break

            offset += limite
            # Pequeña pausa para no saturar la API de Spotify
            time.sleep(0.3)

    print(f"   ✅ Se obtuvieron {len(canciones)} canciones de Spotify")
    return canciones


def buscar_en_youtube(ytmusic, nombre_cancion, artista):
    """
    Busca una canción en YouTube Music.
    Intenta primero con el nombre original, y si no encuentra,
    intenta con el nombre limpio (sin feat., remix, etc.)

    Retorna el videoId si la encuentra, o None si no.
    """
    # Intento 1: Búsqueda con nombre original + artista
    consulta = f"{artista} - {nombre_cancion}"
    try:
        resultados = ytmusic.search(consulta, filter="songs", limit=3)
        if resultados:
            return resultados[0]["videoId"]
    except Exception:
        pass  # Si falla, intentamos de otra forma

    # Intento 2: Búsqueda con nombre limpio + artista
    nombre_limpio = limpiar_nombre_cancion(nombre_cancion)
    if nombre_limpio != nombre_cancion:
        consulta_limpia = f"{artista} - {nombre_limpio}"
        try:
            resultados = ytmusic.search(consulta_limpia, filter="songs", limit=3)
            if resultados:
                return resultados[0]["videoId"]
        except Exception:
            pass

    # Intento 3: Solo el nombre de la canción (sin artista)
    try:
        resultados = ytmusic.search(nombre_cancion, filter="songs", limit=3)
        if resultados:
            return resultados[0]["videoId"]
    except Exception:
        pass

    return None


def guardar_canciones_no_encontradas(
    canciones_fallidas, archivo="canciones_no_encontradas.txt"
):
    """
    Guarda la lista de canciones que no se encontraron en YouTube Music
    en un archivo de texto para que el usuario las busque manualmente.
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

    print(f"\n📝 Lista de canciones no encontradas guardada en: {archivo}")


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================


def migrar():
    """
    Función principal que ejecuta todo el proceso de migración.
    """
    print()
    print("=" * 60)
    print("  🎶 MIGRADOR DE SPOTIFY A YOUTUBE MUSIC 🎶")
    print("=" * 60)
    print()

    # ----------------------------------------------------------
    # PASO 1: Cargar configuración desde el archivo .env
    # ----------------------------------------------------------
    print("📋 Paso 1: Cargando configuración...")
    load_dotenv()  # Carga las variables del archivo .env

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    playlist_url = os.getenv("SPOTIFY_PLAYLIST_URL")
    nombre_playlist_yt = os.getenv("YOUTUBE_PLAYLIST_NAME", "Mi Playlist de Spotify")
    yt_client_id = os.getenv("YOUTUBE_CLIENT_ID")
    yt_client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")

    # Verificar que todas las credenciales están configuradas
    if not client_id or client_id == "tu_client_id_aqui":
        print("❌ ERROR: No has configurado el SPOTIFY_CLIENT_ID en el archivo .env")
        print("   Sigue la GUIA_PASO_A_PASO.md para obtener tus credenciales.")
        sys.exit(1)

    if not client_secret or client_secret == "tu_client_secret_aqui":
        print(
            "❌ ERROR: No has configurado el SPOTIFY_CLIENT_SECRET en el archivo .env"
        )
        print("   Sigue la GUIA_PASO_A_PASO.md para obtener tus credenciales.")
        sys.exit(1)

    if not playlist_url or "TU_PLAYLIST_ID_AQUI" in playlist_url:
        print("❌ ERROR: No has configurado la SPOTIFY_PLAYLIST_URL en el archivo .env")
        print("   Copia la URL de tu playlist de Spotify y pégala en el archivo .env")
        sys.exit(1)

    print("   ✅ Configuración cargada correctamente")

    # ----------------------------------------------------------
    # PASO 2: Conectar con Spotify (con autenticación de usuario)
    # ----------------------------------------------------------
    print("\n🔗 Paso 2: Conectando con Spotify...")
    print("   (Se abrirá tu navegador para iniciar sesión si es la primera vez)")
    try:
        # Autenticación OAuth con tu cuenta de Spotify
        # Esto es necesario para poder leer las canciones de playlists
        redirect_uri = os.getenv(
            "SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback"
        )
        auth_spotify = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="playlist-read-private playlist-read-collaborative user-read-private",
            cache_path=".spotify_cache",
        )
        sp = spotipy.Spotify(auth_manager=auth_spotify)

        # Extraer el ID de la playlist desde la URL
        playlist_id = extraer_playlist_id(playlist_url)
        if not playlist_id:
            print(
                f"❌ ERROR: No se pudo extraer el ID de la playlist desde: {playlist_url}"
            )
            print("   Asegúrate de que la URL sea correcta.")
            sys.exit(1)

        # Verificar que la playlist existe obteniendo su nombre
        info_playlist = sp.playlist(playlist_id, fields="name,owner.display_name")
        print(f"   ✅ Playlist encontrada: '{info_playlist['name']}'")
        print(f"   👤 Creada por: {info_playlist['owner']['display_name']}")
    except Exception as e:
        print(f"❌ ERROR al conectar con Spotify: {e}")
        print("   Verifica tus credenciales en el archivo .env")
        sys.exit(1)

    # ----------------------------------------------------------
    # PASO 3: Obtener todas las canciones de Spotify
    # ----------------------------------------------------------
    print("\n📥 Paso 3: Descargando lista de canciones...")
    canciones = obtener_canciones_spotify(sp, playlist_id)

    if not canciones:
        print("❌ La playlist está vacía o no se pudieron obtener las canciones.")
        sys.exit(1)

    # ----------------------------------------------------------
    # PASO 4: Conectar con YouTube Music
    # ----------------------------------------------------------
    print("\n🔗 Paso 4: Conectando con YouTube Music...")

    # Verificar si el usuario proporcionó headers.txt para Browser Auth manual
    archivo_browser = "browser.json"
    archivo_headers_txt = "headers.txt"
    archivo_oauth = "oauth.json"

    if os.path.exists(archivo_headers_txt) and not os.path.exists(archivo_browser):
        print("   ⚙️  Procesando headers.txt para crear browser.json...")
        try:
            with open(archivo_headers_txt, "r", encoding="utf-8") as f:
                lineas = f.read().strip().split("\n")

            # Detectar si el texto está en formato "cuadrícula" (una línea clave, otra línea valor)
            # Esto ocurre al copiar desde Chrome/Edge sin usar Raw format.
            if not any(": " in l for l in lineas):
                headers_corregidos = []
                for i in range(0, len(lineas), 2):
                    if i + 1 < len(lineas):
                        key = lineas[i].strip()
                        val = lineas[i + 1].strip()
                        if key.startswith(":"):
                            key = key[1:]  # Evitar ::authority
                        headers_corregidos.append(f"{key}: {val}")
                headers_raw = "\n".join(headers_corregidos)
            else:
                headers_raw = "\n".join(lineas)

            # Esta función de ytmusicapi convierte headers raw en el JSON necesario
            ytmusicapi.setup(filepath=archivo_browser, headers_raw=headers_raw)
            print("   ✅ Archivo browser.json generado correctamente.")
        except Exception as e:
            print(f"❌ ERROR convirtiendo headers.txt a browser.json: {e}")
            print("   Asegúrate de haber copiado las 'Request headers' correctamente.")
            sys.exit(1)

    if os.path.exists(archivo_browser):
        print("   Conectando con YouTube Music usando browser.json (Browser Auth)...")
        try:
            ytmusic = YTMusic(archivo_browser)

            # Prueba rápida (usamos suggestions porque get_library_playlists falla si está 100% vacía)
            ytmusic.get_search_suggestions("test")
            print("   ✅ Conectado a YouTube Music exitosamente (Browser Auth)")
        except Exception as e:
            print(f"❌ ERROR al conectar con YouTube Music (Browser Auth): {e}")
            print(
                "   Si este error persiste, elimina browser.json e intenta obtener nuevos headers."
            )
            sys.exit(1)
    else:
        # ---- Flujo Original OAuth ----
        if (
            not yt_client_id
            or not yt_client_secret
            or yt_client_id == "tu_youtube_client_id_aqui"
        ):
            print(
                "❌ ERROR: ytmusicapi ahora requiere credenciales de API de YouTube u obtener manualmnete browser.json"
            )
            sys.exit(1)

        if not os.path.exists(archivo_oauth):
            print("   ⚠️  No se encontró el archivo de autenticación de YouTube Music.")
            print("   Se abrirá tu navegador para que inicies sesión en YouTube Music.")

            try:
                ytmusicapi.setup_oauth(
                    client_id=yt_client_id,
                    client_secret=yt_client_secret,
                    filepath=archivo_oauth,
                    open_browser=True,
                )
                print("   ✅ Autenticación completada y guardada")
                # Intentar crear el objeto ahora que ya existe
                ytmusic = YTMusic(
                    archivo_oauth,
                    oauth_credentials=OAuthCredentials(
                        client_id=yt_client_id, client_secret=yt_client_secret
                    ),
                )
                ytmusic.get_search_suggestions("test")
            except Exception as e:
                print(f"❌ ERROR en la autenticación con OAuth: {e}")
                sys.exit(1)
        else:
            print(
                "   Conectando con YouTube Music usando el archivo de autenticación..."
            )
            try:
                ytmusic = YTMusic(
                    archivo_oauth,
                    oauth_credentials=OAuthCredentials(
                        client_id=yt_client_id, client_secret=yt_client_secret
                    ),
                )
                ytmusic.get_search_suggestions("test")

                print("   ✅ Conectado a YouTube Music exitosamente")
            except Exception as e:
                error_str = str(e)
                print(f"❌ ERROR al conectar con YouTube Music: {error_str}")
                if "HTTP 400" in error_str and "invalid argument" in error_str.lower():
                    print(
                        "\n   ⚠️  Este es un error conocido de YouTube Music usando OAuth."
                    )
                    print("   Usualmente ocurre por una de estas razones:")
                    print(
                        "   1. Es la primera vez que usas la cuenta y no has abierto music.youtube.com."
                    )
                    print(
                        "      Solución: Abre https://music.youtube.com en tu navegador, inicia sesión"
                    )
                    print("   2. Estás usando una 'Cuenta de Marca' (Brand Account).")
                    print(
                        "\n   👉 TRUCO RAPIDO: Elimina 'oauth.json' y usa Browser Auth con headers.txt."
                    )
                else:
                    print(
                        "   Intenta eliminar el archivo oauth.json y ejecuta el script de nuevo"
                    )
                sys.exit(1)

    # ----------------------------------------------------------
    # PASO 5: Crear la playlist en YouTube Music
    # ----------------------------------------------------------
    print(f"\n📝 Paso 5: Creando playlist '{nombre_playlist_yt}' en YouTube Music...")
    try:
        import re

        # Youtube Music es muy estricto con los caracteres especiales en nombres y descripciones.
        # Quitamos emojis y caracteres raros para evitar el error HTTP 400 Bad Request
        def limpiar_texto_yt(texto):
            # Mantiene letras, números, espacios y puntuación básica
            return re.sub(r"[^\w\s.,!?-]", "", texto).strip()

        nombre_seguro = limpiar_texto_yt(nombre_playlist_yt)
        if not nombre_seguro:
            nombre_seguro = "Mi Playlist de Spotify"

        desc_original = f"Playlist migrada desde Spotify el {datetime.now().strftime('%d/%m/%Y')}. Original: '{info_playlist['name']}' por {info_playlist['owner']['display_name']}."
        descripcion_segura = limpiar_texto_yt(desc_original)

        # ytmusicapi.create_playlist devuelve directamente el ID en texto
        playlist_yt_id = ytmusic.create_playlist(
            title=nombre_seguro,
            description=descripcion_segura,
            privacy_status="PRIVATE",  # Privada por defecto (puedes cambiarla después)
        )
        if isinstance(playlist_yt_id, dict):
            # A veces la API cambia y devuelve un diccionario
            playlist_yt_id = playlist_yt_id.get("playlistId", "")

        # IMPORTANTE: A veces YouTube Music devuelve el ID con el prefijo "VL"
        # Si intentamos agregar canciones con el prefijo VL, fallará silenciosamente.
        if playlist_yt_id and playlist_yt_id.startswith("VL"):
            playlist_yt_id = playlist_yt_id[2:]

        print(f"   ✅ Playlist creada exitosamente (privada)")
    except Exception as e:
        print(f"❌ ERROR al crear la playlist en YouTube Music: {e}")
        sys.exit(1)

    # ----------------------------------------------------------
    # PASO 6: Buscar y agregar cada canción
    # ----------------------------------------------------------
    print(f"\n🔍 Paso 6: Buscando y agregando canciones en YouTube Music...")
    print(f"   Esto puede tomar un rato con {len(canciones)} canciones...")
    print(f"   (aproximadamente {len(canciones) * 2 // 60} minutos)\n")

    canciones_encontradas = []
    canciones_no_encontradas = []
    errores = []

    # Barra de progreso principal
    with tqdm(total=len(canciones), desc="   Migrando", unit="canción") as barra:
        for i, cancion in enumerate(canciones):
            nombre = cancion["nombre"]
            artista = cancion["artista"]

            try:
                # Buscar la canción en YouTube Music
                video_id = buscar_en_youtube(ytmusic, nombre, artista)

                if video_id:
                    # ¡Encontrada! Agregarla a la playlist
                    try:
                        print(
                            f"      +) Agregando a YT: {artista} - {nombre} (ID: {video_id})"
                        )
                        ytmusic.add_playlist_items(
                            playlistId=playlist_yt_id,
                            videoIds=[video_id],
                            duplicates=False,  # No agregar duplicados
                        )
                        canciones_encontradas.append(cancion)
                    except Exception as e:
                        print(f"      ❌ API Error: {str(e)}")
                        # Si falla al agregar (ej: duplicado), registrar el error
                        errores.append({**cancion, "error": str(e)})
                else:
                    # No se encontró en YouTube Music
                    canciones_no_encontradas.append(cancion)

            except Exception as e:
                errores.append({**cancion, "error": str(e)})

            barra.update(1)

            # Pausa para no saturar la API de YouTube Music
            # (cada 5 canciones esperamos un poco más)
            if (i + 1) % 5 == 0:
                time.sleep(2)
            else:
                time.sleep(1)

    # ----------------------------------------------------------
    # PASO 7: Mostrar reporte final
    # ----------------------------------------------------------
    print("\n")
    print("=" * 60)
    print("  📊 REPORTE FINAL DE MIGRACIÓN")
    print("=" * 60)
    print()
    print(f"  🎵 Total de canciones en Spotify:     {len(canciones)}")
    print(f"  ✅ Encontradas y agregadas a YouTube:  {len(canciones_encontradas)}")
    print(f"  ❌ No encontradas:                     {len(canciones_no_encontradas)}")
    if errores:
        print(f"  ⚠️  Errores al agregar:                {len(errores)}")
    print()

    # Calcular porcentaje de éxito
    if canciones:
        porcentaje = (len(canciones_encontradas) / len(canciones)) * 100
        print(f"  📈 Porcentaje de éxito: {porcentaje:.1f}%")

    print()
    print("=" * 60)

    # Guardar las canciones no encontradas en un archivo
    if canciones_no_encontradas:
        guardar_canciones_no_encontradas(canciones_no_encontradas)
        print("   Puedes buscar esas canciones manualmente en YouTube Music.")

    # Guardar errores si los hay
    if errores:
        with open("errores_migracion.txt", "w", encoding="utf-8") as f:
            f.write("ERRORES DURANTE LA MIGRACIÓN\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for err in errores:
                f.write(f"Canción: {err['artista']} — {err['nombre']}\n")
                f.write(f"Error: {err['error']}\n\n")
        print(f"\n📝 Detalle de errores guardado en: errores_migracion.txt")

    print()
    print("🎉 ¡Migración completada!")
    print(f"   Abre YouTube Music O haz clic en este enlace:")
    print(f"   👉 https://music.youtube.com/playlist?list={playlist_yt_id} 👈")
    print()


# ============================================================
# PUNTO DE ENTRADA
# ============================================================
if __name__ == "__main__":
    try:
        migrar()
    except KeyboardInterrupt:
        # Si el usuario presiona Ctrl+C para cancelar
        print("\n\n⏹️  Migración cancelada por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        print("   Si el error persiste, reporta el problema.")
        sys.exit(1)
