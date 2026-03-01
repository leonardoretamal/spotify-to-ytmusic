import os
import sys
import ytmusicapi
from ytmusicapi.auth.oauth import OAuthCredentials
from ytmusicapi import YTMusic
from .utils import limpiar_nombre_cancion, limpiar_texto_yt


def conectar_youtube(yt_client_id, yt_client_secret):
    """
    Conecta con YouTube Music, prefiriendo Browser Auth si está disponible,
    o cayendo en OAuth si están las credenciales.
    """
    archivo_browser = "browser.json"
    archivo_headers_txt = "headers.txt"
    archivo_oauth = "oauth.json"

    # Procesar headers.txt si existe
    if os.path.exists(archivo_headers_txt) and not os.path.exists(archivo_browser):
        print("   ⚙️  Procesando headers.txt para crear browser.json...")
        try:
            with open(archivo_headers_txt, "r", encoding="utf-8") as f:
                lineas = f.read().strip().split("\n")

            if not any(": " in l for l in lineas):
                headers_corregidos = []
                for i in range(0, len(lineas), 2):
                    if i + 1 < len(lineas):
                        key = lineas[i].strip()
                        val = lineas[i + 1].strip()
                        if key.startswith(":"):
                            key = key[1:]
                        headers_corregidos.append(f"{key}: {val}")
                headers_raw = "\n".join(headers_corregidos)
            else:
                headers_raw = "\n".join(lineas)

            ytmusicapi.setup(filepath=archivo_browser, headers_raw=headers_raw)
            print("   ✅ Archivo browser.json generado correctamente.")
        except Exception as e:
            print(f"❌ ERROR convirtiendo headers.txt a browser.json: {e}")
            sys.exit(1)

    # Conectar usando Browser Auth
    if os.path.exists(archivo_browser):
        print("   Conectando con YouTube Music usando browser.json (Browser Auth)...")
        try:
            ytmusic = YTMusic(archivo_browser)
            ytmusic.get_search_suggestions("test")
            print("   ✅ Conectado a YouTube Music exitosamente (Browser Auth)")
            return ytmusic
        except Exception as e:
            print(f"❌ ERROR al conectar con YouTube Music (Browser Auth): {e}")
            sys.exit(1)

    # Flujo Original OAuth
    if (
        not yt_client_id
        or not yt_client_secret
        or yt_client_id == "tu_youtube_client_id_aqui"
    ):
        print(
            "❌ ERROR: ytmusicapi requiere credenciales de API de YouTube u obtener manualmente browser.json"
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
        except Exception as e:
            print(f"❌ ERROR en la autenticación con OAuth: {e}")
            sys.exit(1)

    try:
        print("   Conectando con YouTube Music usando OAuth...")
        ytmusic = YTMusic(
            archivo_oauth,
            oauth_credentials=OAuthCredentials(
                client_id=yt_client_id, client_secret=yt_client_secret
            ),
        )
        ytmusic.get_search_suggestions("test")
        print("   ✅ Conectado a YouTube Music exitosamente")
        return ytmusic
    except Exception as e:
        print(f"❌ ERROR al conectar con YouTube Music: {e}")
        sys.exit(1)


def buscar_en_youtube(ytmusic, nombre_cancion, artista):
    """
    Busca una canción en YouTube Music.
    Intenta primero con el nombre original, y si no encuentra,
    intenta con el nombre limpio.
    """
    consulta = f"{artista} - {nombre_cancion}"
    try:
        resultados = ytmusic.search(consulta, filter="songs", limit=3)
        if resultados:
            return resultados[0]["videoId"]
    except Exception:
        pass

    nombre_limpio = limpiar_nombre_cancion(nombre_cancion)
    if nombre_limpio != nombre_cancion:
        consulta_limpia = f"{artista} - {nombre_limpio}"
        try:
            resultados = ytmusic.search(consulta_limpia, filter="songs", limit=3)
            if resultados:
                return resultados[0]["videoId"]
        except Exception:
            pass

    try:
        resultados = ytmusic.search(nombre_cancion, filter="songs", limit=3)
        if resultados:
            return resultados[0]["videoId"]
    except Exception:
        pass

    return None


def crear_playlist_yt(ytmusic, nombre_playlist_yt, desc_original):
    """Crea la playlist en YouTube Music y retorna su ID."""
    try:
        nombre_seguro = limpiar_texto_yt(nombre_playlist_yt)
        if not nombre_seguro:
            nombre_seguro = "Mi Playlist de Spotify"

        descripcion_segura = limpiar_texto_yt(desc_original)

        playlist_yt_id = ytmusic.create_playlist(
            title=nombre_seguro,
            description=descripcion_segura,
            privacy_status="PRIVATE",
        )

        if isinstance(playlist_yt_id, dict):
            playlist_yt_id = playlist_yt_id.get("playlistId", "")

        if playlist_yt_id and playlist_yt_id.startswith("VL"):
            playlist_yt_id = playlist_yt_id[2:]

        print(f"   ✅ Playlist '{nombre_seguro}' creada exitosamente (privada)")
        return playlist_yt_id
    except Exception as e:
        print(f"❌ ERROR al crear la playlist en YouTube Music: {e}")
        sys.exit(1)
