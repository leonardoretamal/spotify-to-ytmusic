import os
import sys

import ytmusicapi
from ytmusicapi import YTMusic
from ytmusicapi.auth.oauth import OAuthCredentials

from .utils import limpiar_nombre_cancion, limpiar_texto_yt


def _mostrar_guia_headers_txt():
    print("\n⚠️ No se encontro 'headers.txt' ni 'browser.json'.")
    print("   Para continuar con Browser Auth (recomendado), sigue estos pasos:")
    print("   1) Abre https://music.youtube.com e inicia sesion.")
    print("   2) Presiona F12 y entra a la pestana Network/Red.")
    print("   3) Filtra por 'browse' y recarga la pagina (Inicio/Explorar).")
    print("   4) Abre una request 'browse' y copia TODO 'Request Headers'.")
    print("   5) Crea 'headers.txt' en la carpeta del proyecto y pega ese contenido.")
    print("   6) Guarda el archivo y vuelve a esta terminal.")


def _esperar_headers_txt(archivo_headers_txt):
    while not os.path.exists(archivo_headers_txt):
        _mostrar_guia_headers_txt()
        respuesta = input(
            "   Presiona ENTER cuando ya creaste 'headers.txt' "
            "o escribe 'omitir' para continuar sin ese metodo: "
        ).strip().lower()
        if respuesta == "omitir":
            return False
    return True


def _extraer_mensajes_respuesta(respuesta):
    mensajes = []
    for item in respuesta.get("actions", []):
        if not isinstance(item, dict):
            continue
        add_toast = item.get("addToToastAction", {})
        runs = (
            add_toast.get("item", {})
            .get("notificationActionRenderer", {})
            .get("responseText", {})
            .get("runs", [])
        )
        if runs:
            mensajes.append("".join(t.get("text", "") for t in runs).strip())
    return [m for m in mensajes if m]


def conectar_youtube(yt_client_id, yt_client_secret):
    """
    Conecta con YouTube Music, prefiriendo Browser Auth si esta disponible,
    o cayendo en OAuth si estan las credenciales.
    """
    archivo_browser = "browser.json"
    archivo_headers_txt = "headers.txt"
    archivo_oauth = "oauth.json"

    if not os.path.exists(archivo_browser) and not os.path.exists(archivo_headers_txt):
        _esperar_headers_txt(archivo_headers_txt)

    # Procesar headers.txt si existe
    if os.path.exists(archivo_headers_txt) and not os.path.exists(archivo_browser):
        print("   ⚙️ Procesando headers.txt para crear browser.json...")
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

    # Flujo OAuth (fallback)
    if (
        not yt_client_id
        or not yt_client_secret
        or yt_client_id == "tu_youtube_client_id_aqui"
    ):
        print(
            "❌ ERROR: No hay Browser Auth disponible y faltan credenciales OAuth de YouTube."
        )
        print("   Crea 'headers.txt' siguiendo la guia o configura YOUTUBE_CLIENT_ID/SECRET.")
        sys.exit(1)

    if not os.path.exists(archivo_oauth):
        print("   ⚠️ No se encontro el archivo de autenticacion de YouTube Music.")
        print("   Se abrira tu navegador para que inicies sesion en YouTube Music.")
        try:
            ytmusicapi.setup_oauth(
                client_id=yt_client_id,
                client_secret=yt_client_secret,
                filepath=archivo_oauth,
                open_browser=True,
            )
            print("   ✅ Autenticacion completada y guardada")
        except Exception as e:
            print(f"❌ ERROR en la autenticacion con OAuth: {e}")
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
    Busca una cancion en YouTube Music.
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


def crear_playlist_yt(ytmusic, nombre_playlist_yt, desc_original, privacy_status="PRIVATE"):
    """Crea la playlist en YouTube Music y retorna su ID."""
    try:
        nombre_seguro = limpiar_texto_yt(nombre_playlist_yt)
        if not nombre_seguro:
            nombre_seguro = "Mi Playlist de Spotify"

        descripcion_segura = limpiar_texto_yt(desc_original)

        playlist_yt_id = ytmusic.create_playlist(
            title=nombre_seguro,
            description=descripcion_segura,
            privacy_status=privacy_status,
        )

        if isinstance(playlist_yt_id, dict):
            playlist_yt_id = playlist_yt_id.get("playlistId", "")

        if playlist_yt_id and playlist_yt_id.startswith("VL"):
            playlist_yt_id = playlist_yt_id[2:]

        print(
            f"   ✅ Playlist '{nombre_seguro}' creada exitosamente "
            f"({privacy_status.lower()})"
        )
        return playlist_yt_id
    except Exception as e:
        print(f"❌ ERROR al crear la playlist en YouTube Music: {e}")
        sys.exit(1)


def agregar_cancion_a_playlist(ytmusic, playlist_yt_id, video_id):
    """
    Agrega una cancion a una playlist y clasifica el resultado real de la API.

    Retorna:
      (estado: str, motivo: str | None)
      estado en {"agregada", "ya_existia", "error_api"}
    """
    try:
        respuesta = ytmusic.add_playlist_items(
            playlistId=playlist_yt_id,
            videoIds=[video_id],
            duplicates=False,
        )
    except Exception as e:
        return "error_api", f"Error API al agregar: {e}"

    if isinstance(respuesta, str):
        if "SUCCEEDED" in respuesta:
            return "agregada", None
        if "ALREADY_EXISTS" in respuesta or "EXISTS" in respuesta:
            return "ya_existia", "La cancion ya existia en la playlist."
        return "error_api", f"Estatus no exitoso: {respuesta}"

    if not isinstance(respuesta, dict):
        return "error_api", f"Respuesta inesperada: {type(respuesta).__name__}"

    status = str(respuesta.get("status", ""))
    mensajes = _extraer_mensajes_respuesta(respuesta)
    detalle = " | ".join(mensajes)
    detalle_l = detalle.lower()

    if "SUCCEEDED" in status:
        if "already" in detalle_l or "ya est" in detalle_l or "ya existe" in detalle_l:
            return "ya_existia", detalle or "La cancion ya existia en la playlist."
        return "agregada", None

    if "ALREADY" in status or "EXIST" in status:
        return "ya_existia", detalle or "La cancion ya existia en la playlist."

    if "already" in detalle_l or "ya est" in detalle_l or "ya existe" in detalle_l:
        return "ya_existia", detalle

    if detalle:
        return "error_api", f"{status or 'SIN_STATUS'}: {detalle}"
    return "error_api", f"Estatus no exitoso: {status or 'SIN_STATUS'}"
