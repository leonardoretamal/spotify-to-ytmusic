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
from .utils import (
    extraer_playlist_id,
    formato_tiempo_estimado,
    guardar_canciones_no_encontradas,
    guardar_reporte_migracion,
)
from .youtube_client import (
    agregar_cancion_a_playlist,
    buscar_en_youtube,
    conectar_youtube,
    crear_playlist_yt,
)


def _pedir_playlist_spotify():
    while True:
        valor = input(
            "👉 Ingresa la URL (o ID) de la playlist de Spotify que deseas migrar: "
        ).strip()
        if not valor:
            print("   ⚠️ Este dato es obligatorio. Intenta nuevamente.")
            continue

        playlist_id = extraer_playlist_id(valor)
        if not playlist_id:
            print("   ⚠️ URL/ID invalido. Ejemplo valido:")
            print("      https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")
            continue

        return valor, playlist_id


def _pedir_nombre_playlist_youtube():
    while True:
        valor = input("👉 Ingresa el nombre para la playlist en YouTube Music: ").strip()
        if valor:
            return valor
        print("   ⚠️ El nombre no puede estar vacio. Intenta nuevamente.")


def _normalizar_privacidad_youtube(valor):
    valor_limpio = valor.strip().lower()
    if valor_limpio in ("", "privada", "private"):
        return "PRIVATE", "privada"
    if valor_limpio in ("publica", "pública", "public"):
        return "PUBLIC", "publica"
    if valor_limpio in ("no listada", "oculta", "unlisted"):
        return "UNLISTED", "no listada"
    return None, None


def _pedir_privacidad_youtube():
    print("👉 Visibilidad de la playlist en YouTube Music:")
    print("   - privada (por defecto)")
    print("   - no listada")
    print("   - publica")

    while True:
        entrada = input(
            "   Escribe una opcion y presiona ENTER (si dejas vacio sera privada): "
        )
        privacidad_api, privacidad_legible = _normalizar_privacidad_youtube(entrada)
        if privacidad_api:
            return privacidad_api, privacidad_legible
        print("   ⚠️ Opcion invalida. Usa: privada, no listada o publica.")


def _ofrecer_reintento_por_cache():
    while True:
        respuesta = input(
            "\n¿Deseas borrar '.spotify_cache' y reintentar una vez? [S/n]: "
        ).strip().lower()
        if respuesta in ("", "s", "si", "sí", "y", "yes"):
            if os.path.exists(".spotify_cache"):
                os.remove(".spotify_cache")
                print("   ✅ Archivo '.spotify_cache' eliminado.")
            else:
                print("   ℹ️ No existia '.spotify_cache'. Se reintentara igualmente.")
            return True
        if respuesta in ("n", "no"):
            return False
        print("   ⚠️ Respuesta invalida. Escribe S o N.")


def _spotify_error_reintento(error_type):
    return error_type in ("spotify_forbidden", "spotify_unauthorized")


def _limpiar_archivos_obsoletos():
    archivos_obsoletos = ["errores_migracion.txt"]
    eliminados = []
    for archivo in archivos_obsoletos:
        if os.path.exists(archivo):
            os.remove(archivo)
            eliminados.append(archivo)
    if eliminados:
        print("   🧹 Limpieza automatica: se eliminaron archivos obsoletos:")
        for archivo in eliminados:
            print(f"      - {archivo}")


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
    _limpiar_archivos_obsoletos()

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
    yt_client_id = os.getenv("YOUTUBE_CLIENT_ID")
    yt_client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")

    if not client_id or client_id == "tu_client_id_aqui":
        print("❌ ERROR: No has configurado el SPOTIFY_CLIENT_ID en el archivo .env")
        sys.exit(1)
    if not client_secret or client_secret == "tu_client_secret_aqui":
        print("❌ ERROR: No has configurado el SPOTIFY_CLIENT_SECRET en el archivo .env")
        sys.exit(1)

    print("   ✅ Configuracion cargada correctamente")

    # ----------------------------------------------------------
    # PASO 2: Pedir datos obligatorios por CLI
    # ----------------------------------------------------------
    print("\n🧾 Paso 2: Datos de migracion (ingresados por ti)...")
    playlist_url, playlist_id = _pedir_playlist_spotify()
    nombre_playlist_yt = _pedir_nombre_playlist_youtube()
    privacidad_yt_api, privacidad_yt_legible = _pedir_privacidad_youtube()

    print()
    print("ℹ️ Aviso importante antes de continuar con Spotify:")
    print(
        "   La playlist debe ser tuya o debes ser co-creador/colaborador"
        " con permisos reales de acceso."
    )
    print("   Si Spotify devuelve 403 real, el script te explicara como corregirlo.")

    # ----------------------------------------------------------
    # PASO 3 y 4: Conectar con Spotify y obtener datos
    # ----------------------------------------------------------
    intento_spotify = 0
    max_intentos_spotify = 2
    info_playlist = None
    canciones = []

    while intento_spotify < max_intentos_spotify:
        intento_spotify += 1
        sp = conectar_spotify(client_id, client_secret, redirect_uri)

        resultado_info = obtener_info_playlist(sp, playlist_id)
        if not resultado_info.get("ok"):
            error_type = resultado_info.get("error_type")
            if _spotify_error_reintento(error_type) and intento_spotify < max_intentos_spotify:
                print(
                    "\n⚠️ Spotify devolvio un error de autorizacion/permisos "
                    f"({error_type})."
                )
                if _ofrecer_reintento_por_cache():
                    continue
            print("❌ No se pudo obtener informacion de la playlist de Spotify.")
            sys.exit(1)
        info_playlist = resultado_info.get("info")

        resultado_spotify = obtener_canciones_spotify(sp, playlist_id)
        if not resultado_spotify.get("ok"):
            error_type = resultado_spotify.get("error_type")
            if _spotify_error_reintento(error_type) and intento_spotify < max_intentos_spotify:
                print(
                    "\n⚠️ Spotify devolvio un error de autorizacion/permisos "
                    f"({error_type})."
                )
                if _ofrecer_reintento_por_cache():
                    continue
            if error_type == "spotify_forbidden":
                print("❌ No se pudieron leer las canciones por permisos/autorizacion (403).")
            else:
                mensaje = resultado_spotify.get("error_message") or "Sin detalle"
                print(f"❌ No se pudieron obtener canciones de Spotify: {mensaje}")
            sys.exit(1)

        canciones = resultado_spotify.get("canciones", [])
        break

    if len(canciones) == 0:
        print("⚠️ La playlist existe pero no tiene canciones para migrar.")
        sys.exit(1)

    # ----------------------------------------------------------
    # PASO 5: Conectar con YouTube Music
    # ----------------------------------------------------------
    print("\n🔗 Paso 5: Conectando con YouTube Music...")
    ytmusic = conectar_youtube(yt_client_id, yt_client_secret)

    # ----------------------------------------------------------
    # PASO 6: Crear la playlist en YouTube Music
    # ----------------------------------------------------------
    print(
        f"\n📝 Paso 6: Creando playlist '{nombre_playlist_yt}' "
        f"({privacidad_yt_legible}) en YouTube Music..."
    )
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    desc_original = (
        f"Playlist migrada desde Spotify el {fecha_hoy}. "
        f"Original: '{info_playlist['name']}' por {info_playlist['owner']['display_name']}."
    )
    playlist_yt_id = crear_playlist_yt(
        ytmusic, nombre_playlist_yt, desc_original, privacidad_yt_api
    )
    link_playlist_youtube = f"https://music.youtube.com/playlist?list={playlist_yt_id}"

    # ----------------------------------------------------------
    # PASO 7: Buscar y agregar cada cancion
    # ----------------------------------------------------------
    print("\n🔍 Paso 7: Buscando y agregando canciones en YouTube Music...")

    segundos_por_cancion = 2
    tiempo_estimado_segundos = len(canciones) * segundos_por_cancion
    tiempo_estimado_formato = formato_tiempo_estimado(tiempo_estimado_segundos)

    print(f"   Esto puede tomar un rato con {len(canciones)} canciones...")
    print(f"   (Tiempo estimado: ~{tiempo_estimado_formato})\n")

    canciones_agregadas = []
    canciones_no_encontradas = []
    canciones_ya_existian = []
    canciones_error_api = []

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
                procesada = False

                while intentos < max_intentos and not procesada:
                    try:
                        video_id = buscar_en_youtube(ytmusic, nombre, artista)
                        if video_id:
                            barra.write(
                                f"      +) Agregando a YT: {artista} - {nombre} (ID: {video_id})"
                            )
                            estado_agregado, motivo = agregar_cancion_a_playlist(
                                ytmusic, playlist_yt_id, video_id
                            )
                            if estado_agregado == "agregada":
                                canciones_agregadas.append(cancion)
                                procesada = True
                            elif estado_agregado == "ya_existia":
                                canciones_ya_existian.append(
                                    {
                                        **cancion,
                                        "motivo": motivo or "La cancion ya estaba en la playlist.",
                                    }
                                )
                                barra.write(
                                    "      ℹ️ Ya existia en la playlist: "
                                    f"{artista} - {nombre}"
                                )
                                procesada = True
                            else:
                                cancion_con_motivo = {
                                    **cancion,
                                    "motivo": motivo
                                    or "Error API al insertar en YouTube Music.",
                                }
                                canciones_error_api.append(cancion_con_motivo)
                                barra.write(
                                    "      ❌ Error API al agregar: "
                                    f"{artista} - {nombre} ({cancion_con_motivo['motivo']})"
                                )
                                procesada = True
                        else:
                            canciones_no_encontradas.append(cancion)
                            procesada = True
                    except Exception as e_api:
                        intentos += 1
                        if intentos == max_intentos:
                            barra.write(f"      ❌ API Error final tras reintentos: {str(e_api)}")
                            canciones_error_api.append(
                                {
                                    **cancion,
                                    "motivo": f"Intento {intentos}: {str(e_api)}",
                                }
                            )
                            procesada = True
                        else:
                            time.sleep(2)

            except Exception as e:
                canciones_error_api.append({**cancion, "motivo": str(e)})

            barra.update(1)
            time.sleep(1)

    # ----------------------------------------------------------
    # PASO 8: Mostrar reporte final
    # ----------------------------------------------------------
    print("\n")
    print("=" * 60)
    print("  📊 REPORTE FINAL DE MIGRACION")
    print("=" * 60)
    print()
    print(f"  📁 Playlist origen (Spotify):          {info_playlist['name']}")
    print(f"  🔗 Link Spotify:                        {playlist_url}")
    print(f"  📁 Playlist destino (YouTube Music):   {nombre_playlist_yt}")
    print(f"  🔗 Link YouTube Music:                  {link_playlist_youtube}")
    print()
    print(f"  🎵 Total de canciones en Spotify:     {len(canciones)}")
    print(f"  ✅ agregadas:                          {len(canciones_agregadas)}")
    print(f"  ❌ no_encontradas:                     {len(canciones_no_encontradas)}")
    print(f"  ℹ️ ya_existian:                        {len(canciones_ya_existian)}")
    print(f"  ⚠️ error_api:                          {len(canciones_error_api)}")
    print()

    porcentaje = (len(canciones_agregadas) / len(canciones)) * 100
    print(f"  📈 Porcentaje de exito: {porcentaje:.1f}%")

    print()
    print("=" * 60)

    pendientes = canciones_no_encontradas + canciones_error_api
    if pendientes:
        guardar_canciones_no_encontradas(pendientes)

    archivo_reporte = "reporte_migracion_spotify_a_youtube.txt"
    guardar_reporte_migracion(
        archivo=archivo_reporte,
        playlist_spotify_nombre=info_playlist["name"],
        playlist_spotify_url=playlist_url,
        playlist_youtube_nombre=nombre_playlist_yt,
        playlist_youtube_url=link_playlist_youtube,
        total_spotify=len(canciones),
        agregadas=canciones_agregadas,
        no_encontradas=canciones_no_encontradas,
        ya_existian=canciones_ya_existian,
        error_api=canciones_error_api,
    )
    print(f"\n📝 Reporte detallado guardado en: {archivo_reporte}")

    print()
    print("🎉 ¡Migracion completada!")
    print("   Abre YouTube Music O haz clic en este enlace:")
    print(f"   👉 {link_playlist_youtube} 👈")
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
