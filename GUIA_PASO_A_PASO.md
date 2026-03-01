# 🎶 Guía Paso a Paso: Migrar Spotify a YouTube Music

Esta guía te explica **todo desde cero** para migrar tus canciones de Spotify a YouTube Music. No necesitas saber programar.

---

## 📋 Resumen de lo que haremos

1. Instalar Python (el lenguaje del script)
2. Instalar las dependencias del script
3. Crear credenciales de Spotify (gratuito)
4. Crear credenciales de YouTube (gratuito)
5. Autenticarte en YouTube Music
6. Configurar el script con tus datos
7. Ejecutar el script y esperar 🎉

**Tiempo estimado de preparación:** 15-20 minutos  
**Tiempo de migración:** ~2 segundos por canción (1000 canciones ≈ 35 minutos)

---

## Paso 1: Instalar Python

Python es el lenguaje de programación que usa nuestro script. Necesitas instalarlo una vez.

### En Windows:

1. Ve a **[python.org/downloads](https://www.python.org/downloads/)**
2. Haz clic en el botón amarillo **"Download Python 3.x.x"**
3. Abre el archivo descargado (`.exe`)
4. **⚠️ MUY IMPORTANTE:** Marca la casilla **"Add Python to PATH"** (está abajo en la ventana del instalador)
5. Haz clic en **"Install Now"**
6. Espera a que termine y cierra

### Verificar que se instaló correctamente:

1. Abre la **Terminal** (busca "cmd" o "PowerShell" en el menú inicio)
2. Escribe este comando y presiona Enter:

```
python --version
```

3. Deberías ver algo como: `Python 3.12.x` — si ves eso, ¡está instalado! ✅

> **💡 Si dice "python no se reconoce..."**, cierra y vuelve a abrir la terminal. Si sigue sin funcionar, desinstala Python y vuelve a instalarlo asegurándote de marcar "Add Python to PATH".

---

## Paso 2: Abrir la terminal en la carpeta del proyecto

1. Abre el **Explorador de archivos** y navega hasta la carpeta donde está este proyecto
2. En la barra de dirección del explorador, escribe `cmd` y presiona Enter  
   (Esto abrirá una terminal directamente en esa carpeta)

**Método alternativo:** Abre PowerShell/CMD y navega con:

```
cd ruta\a\la\carpeta\Script_Spotify_playlist_to_youtube
```

---

## Paso 3: Crear un entorno virtual (recomendado)

Un entorno virtual es como una "burbuja" que mantiene las librerías del script separadas del resto de tu computadora. No es obligatorio pero sí recomendable.

```bash
# Crear el entorno virtual
python -m venv venv

# Activarlo (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activarlo (Windows CMD)
.\venv\Scripts\activate.bat
```

> **💡 Sabrás que está activado** si ves `(venv)` al inicio de la línea en la terminal.

> **⚠️ Si PowerShell da error de permisos**, ejecuta esto primero:
>
> ```
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

---

## Paso 4: Instalar las dependencias

Con la terminal abierta en la carpeta del proyecto (y el entorno virtual activado si lo creaste), ejecuta:

```
pip install -r requirements.txt
o
python -m pip install -r requirements.txt

```

Esto instalará automáticamente todas las librerías necesarias. Espera a que termine (puede tomar 1-2 minutos).

---

## Paso 5: Crear credenciales de Spotify

Necesitamos credenciales para que el script pueda leer tu playlist. Es gratuito.

### 5.1 — Crear cuenta de desarrollador

1. Ve a **[developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)**
2. Inicia sesión con tu cuenta de Spotify (la misma de siempre)
3. Si es la primera vez, acepta los términos de uso

### 5.2 — Crear una aplicación

1. Haz clic en **"Create app"** (o "Crear aplicación")
2. Completa los campos:
   - **App name:** `Mi Migrador` (o cualquier nombre)
   - **App description:** `Script para migrar playlists` (o lo que quieras)
   - **Redirect URI:** escribe `http://127.0.0.1:8888/callback` y haz clic en **Add**
   - **Which API/SDKs are you planning to use?:** Selecciona **Web API**
3. Marca la casilla de los términos y haz clic en **"Save"**

### 5.3 — Obtener tus credenciales

1. En la página de tu app, haz clic en **"Settings"** (Configuración)
2. Verás tu **Client ID** — cópialo
3. Haz clic en **"View client secret"** — cópialo también
4. **Guárdalos en un lugar seguro**, los necesitarás en el paso 7

---

## Paso 6: Autenticarse en YouTube Music

> **⚠️ REQUISITO MUY IMPORTANTE ANTES DE SEGUIR:**
> Para que el script pueda crear playlists, tu cuenta de Google **DEBE** tener un Canal de YouTube abierto e inicializado.
>
> 1. Ve a [music.youtube.com](https://music.youtube.com/)
> 2. Asegúrate de haber iniciado sesión con tu cuenta principal (no una "Cuenta de Marca").

Existen dos métodos para autenticarse con YouTube Music. Te recomendamos el **Método 1 (Browser Auth)** porque es el más rápido, más seguro y evita el conocido error `HTTP 400 Bad Request`.

### Método 1: Browser Auth (RECOMENDADO ⭐)

No necesitas crear un proyecto en Google Cloud. Solo necesitas extraer tus "headers" de red desde el navegador:

1. Abre tu navegador (Chrome, Edge o Firefox) e ingresa a [music.youtube.com](https://music.youtube.com).
2. Toca la tecla `F12` (o haz clic derecho en la página > "Inspeccionar") para abrir las **Herramientas de Desarrollador**.
3. Ve a la pestaña **Red** (o **Network**).
4. En la casilla de "Filtro" (arriba a la izquierda en esa pestaña), escribe `browse`.
5. En la página de YouTube Music, haz clic en "Inicio" o "Explorar" para recargar contenido. Verás que aparecen nuevos elementos en la lista de red.
6. Haz clic en el primer elemento de la lista que empiece por `browse`.
7. En el panel que se divide a la derecha, busca la pestaña **Headers** (Cabeceras).
8. Baja hasta encontrar el título **Request Headers** (Cabeceras de petición).
9. Selecciona **TODO el texto que hay debajo** de "Request Headers" (desde `accept:` hasta abajo) y **cópialo**.
10. En la carpeta de este proyecto, crea un archivo de texto llamado exactamente **`headers.txt`**.
11. Pega lo que copiaste y guarda el archivo. El script convertirá estos datos automáticamente.
    _(Nota: Si usas este método, en el Paso 7 puedes dejar los campos de YOUTUBE_CLIENT_ID en blanco o con cualquier texto, ya no se usarán)._

---

### Método 2: OAuth desde Google Cloud (Alternativa)

Si prefieres usar la API oficial, debes seguir estos pasos (no funciona con Cuentas de Marca/Canales Secundarios):

1. Ve a **[Google Cloud Console](https://console.cloud.google.com/)**, inicia sesión, y crea un **"Proyecto nuevo"**.
2. En el menú izquierdo ve a **"API y servicios"** > **"Biblioteca"**.
3. Busca "YouTube Data API v3" y hazle clic en **"Habilitar"**.
4. Ve a **"Pantalla de consentimiento de OAuth"**. Selecciona _Usuarios Externos_ -> _Siguiente_. Ponle nombre a la App y a los correos de asistencia.
5. En la sección "Usuarios de prueba", agrega **tu propio correo de YouTube**. Guarda.
6. Ve a **"Credenciales"** > **"+ Crear credenciales"** > **"ID de cliente de OAuth"**.
7. Tipo de aplicación: Selecciona **"TVs y dispositivos de entrada limitada"** (muy importante).
8. Haz clic en Crear. **Copia tu ID de cliente y Secreto de cliente** para usarlos en el Paso 7.

---

## Paso 7: Configurar el archivo .env

1. En la carpeta del proyecto, busca el archivo **`.env.ejemplo`**
2. **Copia** ese archivo y renómbralo a **`.env`** (sin la parte "ejemplo")

   En la terminal puedes hacerlo con:

   ```
   copy .env.ejemplo .env
   ```

3. Abre el archivo **`.env`** con cualquier editor de texto (Bloc de notas, VS Code, etc.)
4. Reemplaza los valores:

```env
# Pega aquí tu Client ID de Spotify (del paso 5.3)
SPOTIFY_CLIENT_ID=abc123tuClientIdReal

# Pega aquí tu Client Secret de Spotify (del paso 5.3)
SPOTIFY_CLIENT_SECRET=xyz789tuClientSecretReal

# Pega la URL de tu playlist de Spotify
SPOTIFY_PLAYLIST_URL=https://open.spotify.com/playlist/tu_playlist_id

# El nombre que quieres para la playlist en YouTube Music
YOUTUBE_PLAYLIST_NAME=Mi Música de Spotify

# Pega aquí tu ID de Cliente de YouTube (del paso 6.4)
YOUTUBE_CLIENT_ID=abc123tuClientIdReal.apps.googleusercontent.com

# Pega aquí tu Secreto de Cliente de YouTube (del paso 6.4)
YOUTUBE_CLIENT_SECRET=xyz789tuClientSecretReal
```

5. **Guarda el archivo**

> **🔒 IMPORTANTE:** El archivo `.env` contiene tus credenciales secretas. NUNCA lo compartas ni lo subas a internet. El `.gitignore` ya está configurado para ignorarlo.

---

## Paso 8: Ejecutar el script

¡Ya estamos listos! Ejecuta el script con:

```
python migrar_spotify_a_youtube.py
```

### ¿Qué va a pasar?

1. **Conexión a Spotify** — El script leerá todas las canciones de tu playlist
2. **Autenticación de YouTube Music** — La primera vez se abrirá tu navegador:
   - Selecciona tu cuenta de Google (la que usas en YouTube Music)
   - Autoriza la aplicación
   - Se guardará la autenticación en `oauth.json` para la próxima vez
3. **Creación de playlist** — Se creará una nueva playlist privada en YouTube Music
4. **Migración** — El script buscará cada canción y la agregará automáticamente
5. **Reporte** — Al final verás un resumen con cuántas canciones se migraron

### Ejemplo de cómo se ve:

```
============================================================
  🎶 MIGRADOR DE SPOTIFY A YOUTUBE MUSIC 🎶
============================================================

📋 Paso 1: Cargando configuración...
   ✅ Configuración cargada correctamente

🔗 Paso 2: Conectando con Spotify...
   ✅ Playlist encontrada: 'Mi playlist favorita'

📥 Paso 3: Descargando lista de canciones...
   📊 Total de canciones: 1042
   Descargando de Spotify: 100%|████████████| 1042/1042

🔍 Paso 6: Buscando y agregando canciones...
   Migrando: 45%|██████░░░░░░░| 469/1042
```

---

## Paso 9: Revisar los resultados

Cuando termine, el script te mostrará un reporte como este:

```
============================================================
  📊 REPORTE FINAL DE MIGRACIÓN
============================================================

  🎵 Total de canciones en Spotify:     1042
  ✅ Encontradas y agregadas:            987
  ❌ No encontradas:                      55

  📈 Porcentaje de éxito: 94.7%
============================================================
```

### ¿Qué hago con las canciones no encontradas?

Las canciones que no se pudieron encontrar automáticamente se guardan en el archivo **`canciones_no_encontradas.txt`**. Puedes:

1. Abrir ese archivo
2. Buscar cada canción manualmente en YouTube Music
3. Agregarla a tu playlist manualmente

> **💡** Es normal que un 5-10% de las canciones no se encuentren. Puede ser porque el título es diferente en YouTube Music o porque simplemente no está disponible.

---

## ❓ Preguntas Frecuentes

### "El script se detuvo a la mitad, ¿pierdo el progreso?"

No. Las canciones que ya se agregaron a YouTube Music siguen ahí. Puedes ejecutar el script de nuevo y las canciones duplicadas no se agregarán dos veces.

### "¿Puedo migrar varias playlists?"

Sí. Cambia la `SPOTIFY_PLAYLIST_URL` y el `YOUTUBE_PLAYLIST_NAME` en el archivo `.env` y ejecuta el script de nuevo.

### "¿Puedo migrar mis 'me gusta' de Spotify?"

Este script está diseñado para playlists específicas. Para los "me gusta" necesitarías otra configuración de autenticación (OAuth de Spotify), que es más compleja.

### "Error: No se reconoce python"

Asegúrate de haber marcado "Add Python to PATH" durante la instalación. Si no lo hiciste, desinstala Python y vuelve a instalarlo marcando esa casilla.

### "Error al conectar con YouTube Music"

- Elimina el archivo `oauth.json`
- Ejecuta el script de nuevo
- Se abrirá el navegador para que te autentiques de nuevo

### "Error 429 o 'Too Many Requests'"

El script tiene pausas para evitar esto, pero si sucede, espera unos minutos y ejecuta el script de nuevo.

---

## 📁 Archivos del proyecto

| Archivo                        | Descripción                                           |
| ------------------------------ | ----------------------------------------------------- |
| `migrar_spotify_a_youtube.py`  | El script principal                                   |
| `requirements.txt`             | Lista de librerías necesarias                         |
| `.env.ejemplo`                 | Plantilla de configuración                            |
| `.env`                         | **Tu** configuración (la creas tú en el paso 6)       |
| `GUIA_PASO_A_PASO.md`          | Esta guía                                             |
| `.gitignore`                   | Protege tus archivos secretos                         |
| `oauth.json`                   | Se crea automáticamente al autenticar YouTube         |
| `canciones_no_encontradas.txt` | Se crea al finalizar (si hay canciones sin encontrar) |
