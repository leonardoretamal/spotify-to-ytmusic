import sys
import time

import spotipy
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth
from tqdm import tqdm


def _mensaje_spotify_403(entidad):
    print(f"❌ ERROR: Spotify devolvio 403 al acceder a {entidad}.")
    print("   Posibles causas:")
    print("   - La playlist es privada y no tienes acceso.")
    print("   - La playlist colaborativa no te incluye como participante.")
    print("   - El token local esta cacheado con permisos/scopes desactualizados.")
    print("   Recomendaciones:")
    print("   - Verifica que la playlist sea publica o tuya.")
    print("   - Borra '.spotify_cache' y autentica de nuevo.")
    print("   - Prueba con una playlist propia para validar el flujo.")


def _leer_items_playlist(sp, playlist_id, limite):
    """
    Lee items de playlist con compatibilidad entre endpoints de Spotify.
    """
    try:
        resultados = sp.playlist_items(
            playlist_id,
            limit=limite,
            offset=0,
            additional_types=("track",),
        )
        return resultados, "tracks"
    except SpotifyException as e:
        # En algunos entornos, /tracks puede devolver 403 y /items funciona.
        if getattr(e, "http_status", None) == 403:
            resultados = sp._get(
                f"playlists/{playlist_id}/items",
                offset=0,
                limit=limite,
                additional_types="track",
            )
            return resultados, "items"
        raise


def conectar_spotify(client_id, client_secret, redirect_uri):
    """
    Conecta con Spotify usando OAuth.
    """
    print("\n🔗 Conectando con Spotify...")
    print("   (Se abrira tu navegador para iniciar sesion si es la primera vez)")
    try:
        auth_spotify = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="playlist-read-private playlist-read-collaborative user-read-private",
            cache_path=".spotify_cache",
        )
        return spotipy.Spotify(auth_manager=auth_spotify)
    except Exception as e:
        print(f"❌ ERROR al conectar con Spotify: {e}")
        print("   Verifica tus credenciales en el archivo .env")
        sys.exit(1)


def obtener_info_playlist(sp, playlist_id):
    """
    Obtiene informacion basica de la playlist.
    """
    try:
        info = sp.playlist(playlist_id, fields="name,owner.display_name")
        print(f"   ✅ Playlist encontrada: '{info['name']}'")
        print(f"   👤 Creada por: {info['owner']['display_name']}")
        return info
    except SpotifyException as e:
        if getattr(e, "http_status", None) == 403:
            _mensaje_spotify_403("los metadatos de la playlist")
        else:
            print(f"❌ ERROR de Spotify al obtener informacion de la playlist: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR al obtener informacion de la playlist: {e}")
        sys.exit(1)


def obtener_canciones_spotify(sp, playlist_id):
    """
    Obtiene TODAS las canciones de una playlist de Spotify.
    Maneja la paginacion automaticamente (Spotify devuelve max. 100 por request).

    Retorna:
      {
        "ok": bool,
        "canciones": list,
        "error_type": str | None,
        "error_message": str | None,
      }
    """
    canciones = []
    limite = 100

    print("\n🎵 Obteniendo canciones de Spotify...")

    try:
        resultados, modo_endpoint = _leer_items_playlist(sp, playlist_id, limite)
        total = resultados["total"]
        print(f"   📊 Total de canciones en la playlist: {total}")
        if modo_endpoint == "items":
            print("   ℹ️ Usando endpoint compatible '/items' por fallback de Spotipy.")

        with tqdm(total=total, desc="   Descargando de Spotify", unit="cancion") as barra:
            while True:
                for item in resultados.get("items", []):
                    track = item.get("track") or item.get("item") or item

                    if not track or not isinstance(track, dict) or "name" not in track:
                        barra.update(1)
                        continue

                    nombre = track.get("name", "Desconocido")
                    artistas = ", ".join(
                        artista.get("name", "") for artista in track.get("artists", [])
                    ).strip(", ")
                    album = track.get("album", {}).get("name", "Desconocido")
                    duracion_ms = track.get("duration_ms", 0)

                    canciones.append(
                        {
                            "nombre": nombre,
                            "artista": artistas or "Desconocido",
                            "album": album,
                            "duracion_ms": duracion_ms,
                        }
                    )
                    barra.update(1)

                if resultados.get("next") is None:
                    break

                if modo_endpoint == "tracks":
                    resultados = sp.next(resultados)
                else:
                    siguiente_offset = len(canciones)
                    resultados = sp._get(
                        f"playlists/{playlist_id}/items",
                        offset=siguiente_offset,
                        limit=limite,
                        additional_types="track",
                    )
                time.sleep(0.3)

        print(f"   ✅ Se obtuvieron {len(canciones)} canciones de Spotify")
        return {
            "ok": True,
            "canciones": canciones,
            "error_type": None,
            "error_message": None,
        }

    except SpotifyException as e:
        if getattr(e, "http_status", None) == 403:
            _mensaje_spotify_403("las canciones de la playlist")
            return {
                "ok": False,
                "canciones": [],
                "error_type": "spotify_forbidden",
                "error_message": str(e),
            }

        print(f"❌ ERROR de Spotify al obtener canciones: {e}")
        return {
            "ok": False,
            "canciones": [],
            "error_type": "spotify_api_error",
            "error_message": str(e),
        }

    except Exception as e:
        print(f"❌ ERROR al obtener canciones de Spotify: {e}")
        return {
            "ok": False,
            "canciones": [],
            "error_type": "unknown_error",
            "error_message": str(e),
        }
