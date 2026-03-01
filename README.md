# 🎶 Migrador de Spotify a YouTube Music 🎶

Un potente script en Python de código abierto (Open Source) diseñado para ayudarte a exportar tus listas de reproducción (playlists) desde Spotify directamente hacia tu cuenta de YouTube Music.

Este proyecto se enfoca en resolver los problemas comunes de migración entre plataformas utilizando las APIs nativas de ambas plataformas, e incluye métodos de autenticación resistentes mediante análisis de cookies de navegador.

---

## ⚠️ Disclaimer (Descargo de Responsabilidad)

**Por favor lee esto antes de clonar y usar este proyecto:**

1. **Legalidad (Copyright)**: El uso y distribución de este código fuente es completamente legal y se ampara bajo la [Licencia MIT](LICENSE) adjunta. No piratea música (no descarga MP3s), ni rompe cifrados DRM. Es simplemente una herramienta de automatización para leer texto de un proveedor y buscarlo en otro.
2. **Términos de Servicio (ToS)**:
   - **Spotify**: Sus términos prohíben explícitamente el uso comercial o masivo de su API para "transferir contenido a plataformas competitivas". Este script está desarrollado con fines puramente **educativos y personales**.
   - **YouTube Music**: El proyecto utiliza la librería `ytmusicapi` que emula a un cliente web. YouTube a veces restringe cuentas que abusan de la automatización masiva.
3. **Uso responsable**: El script incluye pausas explícitas (`time.sleep()`) para no saturar los endpoints y evitar denegaciones de servicio (DoS). **Úsalo bajo tu propia responsabilidad.** Los desarrolladores no se hacen responsables de suspensiones de cuentas o bloqueos.

---

## 🚀 Características

- **Rápido y automático:** Extrae nombres de canciones, artistas y álbumes usando la API de Spotify (compatible con los nuevos endpoints de 2026).
- **Eficiencia de búsqueda:** Emplea algoritmos de "limpieza" inteligente para omitir palabras como _Remix_, _feat._, o _Radio Edit_ que perjudican los resultados en YouTube.
- **Resistente a bloqueos:** Evita los masivos `HTTP 400 Bad Request` en cuentas nuevas de YouTube al soportar tanto `OAuth` como **Browser Authentication** (extracción manual de headers).
- **Reporte detallado:** Genera reportes en formato `.txt` de las canciones que no se pudieron cruzar.

---

## 🛠️ Instalación y Requisitos

1. Asegúrate de tener **Python 3.8 o superior** instalado en tu sistema.
2. Clona este repositorio (siempre ten la precaución de no subir tu archivo `.env` o credenciales una vez lo inicies):
   ```bash
   git clone https://github.com/TU_USUARIO/Script_Spotify_playlist_to_youtube.git
   cd Script_Spotify_playlist_to_youtube
   ```
3. Instala las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```
4. Sigue la [GUIA_PASO_A_PASO.md](GUIA_PASO_A_PASO.md) para configurar el script.

---
