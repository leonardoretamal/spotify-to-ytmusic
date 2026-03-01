import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv
from tqdm import tqdm

from .spotify_client import (
    conectar_spotify,
    obtener_canciones_spotify,
    obtener_info_playlist,
)
from .utils import formato_tiempo_estimado, guardar_canciones_no_encontradas
from .youtube_client import buscar_en_youtube, conectar_youtube, crear_playlist_yt


def migrar():
    """
    Funcion principal que ejecuta todo el proceso de migracion.
    """
    print()
    print("=" * 60)
    print("  🎶 MIGRADOR DE SPOTIFY A YOUTUBE MUSIC 🎶")
    print("=" * 60)
    print()

    # ----------------------------------------------------------
    # PASO 1: Cargar configuracion
    # ----------------------------------------------------------
    print("📋 Paso 1: Cargando configuracion...")
    load_dotenv()

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
    playlist_url = os.getenv("SPOTIFY_PLAYLIST_URL")
    nombre_playlist_yt = os.getenv("YOUTUBE_PLAYLIST_NAME", "Mi Playlist de Spotify")
    yt_client_id = os.getenv("YOUTUBE_CLIENT_ID")
    yt_client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")

    if not client_id or client_id == "tu_client_id_aqui":
        print("❌ ERROR: No has configurado el SPOTIFY_CLIENT_ID en el archivo .env")
        sys.exit(1)
    if not client_secret or client_secret == "tu_client_secret_aqui":
        print("❌ ERROR: No has configurado el SPOTIFY_CLIENT_SECRET en el archivo .env")
        sys.exit(1)
    if not playlist_url or "TU_PLAYLIST_ID_AQUI" in playlist_url:
        print("❌ ERROR: No has configurado la SPOTIFY_PLAYLIST_URL en el archivo .env")
        sys.exit(1)

    print("   ✅ Configuracion cargada correctamente")

    # ----------------------------------------------------------
    # PASO 2: Conectar con Spotify y obtener playlist
    # ----------------------------------------------------------
    sp = conectar_spotify(client_id, client_secret, redirect_uri)

    from .utils import extraer_playlist_id

    playlist_id = extraer_playlist_id(playlist_url)

    if not playlist_id:
        print(f"❌ ERROR: No se pudo extraer el ID de la playlist desde: {playlist_url}")
        sys.exit(1)

    info_playlist = obtener_info_playlist(sp, playlist_id)

    # ----------------------------------------------------------
    # PASO 3: Obtener todas las canciones de Spotify
    # ----------------------------------------------------------
    resultado_spotify = obtener_canciones_spotify(sp, playlist_id)

    if not resultado_spotify.get("ok"):
        error_type = resultado_spotify.get("error_type")
        if error_type == "spotify_forbidden":
            print("❌ No se pudieron leer las canciones por permisos/autorizacion (403).")
        else:
            mensaje = resultado_spotify.get("error_message") or "Sin detalle"
            print(f"❌ No se pudieron obtener canciones de Spotify: {mensaje}")
        sys.exit(1)

    canciones = resultado_spotify.get("canciones", [])

    if len(canciones) == 0:
        print("⚠️ La playlist existe pero no tiene canciones para migrar.")
        sys.exit(1)

    # ----------------------------------------------------------
    # PASO 4: Conectar con YouTube Music
    # ----------------------------------------------------------
    print("\n🔗 Paso 4: Conectando con YouTube Music...")
    ytmusic = conectar_youtube(yt_client_id, yt_client_secret)

    # ----------------------------------------------------------
    # PASO 5: Crear la playlist en YouTube Music
    # ----------------------------------------------------------
    print(f"\n📝 Paso 5: Creando playlist '{nombre_playlist_yt}' en YouTube Music...")
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    desc_original = (
        f"Playlist migrada desde Spotify el {fecha_hoy}. "
        f"Original: '{info_playlist['name']}' por {info_playlist['owner']['display_name']}."
    )
    playlist_yt_id = crear_playlist_yt(ytmusic, nombre_playlist_yt, desc_original)

    # ----------------------------------------------------------
    # PASO 6: Buscar y agregar cada cancion
    # ----------------------------------------------------------
    print("\n🔍 Paso 6: Buscando y agregando canciones en YouTube Music...")

    segundos_por_cancion = 2
    tiempo_estimado_segundos = len(canciones) * segundos_por_cancion
    tiempo_estimado_formato = formato_tiempo_estimado(tiempo_estimado_segundos)

    print(f"   Esto puede tomar un rato con {len(canciones)} canciones...")
    print(f"   (Tiempo estimado: ~{tiempo_estimado_formato})\n")

    canciones_encontradas = []
    canciones_no_encontradas = []
    errores = []

    bar_format = (
        "   {desc}: {percentage:3.0f}%|{bar}| "
        "{n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
    )

    with tqdm(total=len(canciones), desc="Migrando", unit="cancion", bar_format=bar_format) as barra:
        for cancion in canciones:
            nombre = cancion["nombre"]
            artista = cancion["artista"]

            try:
                intentos = 0
                max_intentos = 3
                agregada = False

                while intentos < max_intentos and not agregada:
                    try:
                        video_id = buscar_en_youtube(ytmusic, nombre, artista)
                        if video_id:
                            barra.write(
                                f"      +) Agregando a YT: {artista} - {nombre} (ID: {video_id})"
                            )

                            ytmusic.add_playlist_items(
                                playlistId=playlist_yt_id,
                                videoIds=[video_id],
                                duplicates=False,
                            )
                            canciones_encontradas.append(cancion)
                            agregada = True
                        else:
                            canciones_no_encontradas.append(cancion)
                            break
                    except Exception as e_api:
                        intentos += 1
                        if intentos == max_intentos:
                            barra.write(f"      ❌ API Error final tras reintentos: {str(e_api)}")
                            errores.append(
                                {
                                    **cancion,
                                    "error": f"Intento {intentos}: {str(e_api)}",
                                }
                            )
                        else:
                            time.sleep(2)

            except Exception as e:
                errores.append({**cancion, "error": str(e)})

            barra.update(1)
            time.sleep(1)

    # ----------------------------------------------------------
    # PASO 7: Mostrar reporte final
    # ----------------------------------------------------------
    print("\n")
    print("=" * 60)
    print("  📊 REPORTE FINAL DE MIGRACION")
    print("=" * 60)
    print()
    print(f"  🎵 Total de canciones en Spotify:     {len(canciones)}")
    print(f"  ✅ Encontradas y agregadas a YouTube:  {len(canciones_encontradas)}")
    print(f"  ❌ No encontradas:                     {len(canciones_no_encontradas)}")
    if errores:
        print(f"  ⚠️  Errores al agregar:                {len(errores)}")
    print()

    porcentaje = (len(canciones_encontradas) / len(canciones)) * 100
    print(f"  📈 Porcentaje de exito: {porcentaje:.1f}%")

    print()
    print("=" * 60)

    if canciones_no_encontradas:
        guardar_canciones_no_encontradas(canciones_no_encontradas)

    if errores:
        with open("errores_migracion.txt", "w", encoding="utf-8") as f:
            f.write("ERRORES DURANTE LA MIGRACION\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for err in errores:
                f.write(f"Cancion: {err['artista']} - {err['nombre']}\n")
                f.write(f"Error: {err['error']}\n\n")
        print("\n📝 Detalle de errores guardado en: errores_migracion.txt")

    print()
    print("🎉 ¡Migracion completada!")
    print("   Abre YouTube Music O haz clic en este enlace:")
    print(f"   👉 https://music.youtube.com/playlist?list={playlist_yt_id} 👈")
    print()


if __name__ == "__main__":
    try:
        migrar()
    except KeyboardInterrupt:
        print("\n\n⏹️  Migracion cancelada por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)
