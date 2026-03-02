# 🎶 Guía Paso a Paso: Migrar Spotify a YouTube Music

Esta guía te explica **todo desde cero** para migrar tus canciones de Spotify a YouTube Music. No necesitas saber programar.

---

## 📋 Resumen de lo que haremos

1. Instalar Python (el lenguaje del script)
2. Instalar las dependencias del script
3. Crear credenciales de Spotify (gratis)
4. Elegir método de autenticación de YouTube Music:
   - Browser Auth con `headers.txt` (recomendado)
   - OAuth con Google Cloud (opcional)
5. Configurar el archivo `.env` (solo credenciales)
6. Ejecutar el script y responder preguntas por terminal
7. Revisar el reporte final detallado

**Tiempo estimado de preparación:** 15-25 minutos  
**Tiempo de migración:** ~2 segundos por canción (1000 canciones ≈ 35 minutos)

---

## Paso 1: Instalar Python

Python es el lenguaje de programación que usa nuestro script. Necesitas instalarlo una sola vez.

### En Windows:

1. Ve a **[python.org/downloads](https://www.python.org/downloads/)**
2. Haz clic en **"Download Python 3.x.x"**
3. Abre el archivo descargado (`.exe`)
4. **MUY IMPORTANTE:** marca **"Add Python to PATH"**
5. Haz clic en **"Install Now"**
6. Espera a que termine y cierra

### Verificar instalación

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

```bash
cd ruta\a\la\carpeta\Script_Spotify_playlist_to_youtube
```

---

## Paso 3: Crear un entorno virtual (recomendado)

Un entorno virtual es como una "burbuja" que mantiene las librerías del script separadas del resto de tu computadora. No es obligatorio pero sí recomendable.
```bash
# Crear entorno
python -m venv venv

# Activarlo (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activarlo (Windows CMD)
.\venv\Scripts\activate.bat
```

> **💡 Sabrás que está activado** si ves `(venv)` al inicio de la línea en la terminal.

> **⚠️ Si PowerShell da error de permisos**, ejecuta esto primero:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Paso 4: Instalar dependencias

Con la terminal abierta en la carpeta del proyecto (y el entorno virtual activado si lo creaste), ejecuta:

```bash
pip install -r requirements.txt
```

Si `pip` falla:

```bash
python -m pip install -r requirements.txt
```

---

## Paso 5: Crear credenciales de Spotify

Necesitamos credenciales para que el script pueda leer tu playlist. Es gratuito.

### 5.1 Crear cuenta de desarrollador

1. Ve a **[developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)**
2. Inicia sesión con tu cuenta de Spotify (la misma de siempre)
3. Si es la primera vez, acepta los términos de uso

### 5.2 Crear aplicación

1. Haz clic en **"Create app"** (o "Crear aplicación")
2. Completa los campos:
   - **App name:** `Mi Migrador` (o cualquier nombre)
   - **App description:** `Script para migrar playlists` (o lo que quieras)
   - **Redirect URI:** escribe `http://127.0.0.1:8888/callback` y haz clic en **Add**
   - **Which API/SDKs are you planning to use?:** Selecciona **Web API**
3. Marca la casilla de los términos y haz clic en **"Save"**

### 5.3 Obtener credenciales

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
## Método 1: Browser Auth con `headers.txt` (RECOMENDADO)

Es más rápido para la mayoría de usuarios.
_(Nota: Puedes no crear el headers.txt inmediatamente ya que el script al momento de ejecutarlo a traves de cli te ayudara paso a paso a obtener y crear este archivo)._

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

El script convertirá `headers.txt` en `browser.json` automáticamente.

## Método 2: OAuth con Google Cloud (OPCIONAL)

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

# Pega aquí tu ID de Cliente de YouTube (del paso 6 método 2)
YOUTUBE_CLIENT_ID=abc123tuClientIdReal.apps.googleusercontent.com

# Pega aquí tu Secreto de Cliente de YouTube (del paso 6 método 2)
YOUTUBE_CLIENT_SECRET=xyz789tuClientSecretReal
```

5. **Guarda el archivo**

> **🔒 IMPORTANTE:** El archivo `.env` contiene tus credenciales secretas. NUNCA lo compartas ni lo subas a internet. El `.gitignore` ya está configurado para ignorarlo.

---

## Paso 8: Ejecutar el script

¡Ya estamos listos! Ejecuta el script con:
```bash
python migrar_spotify_a_youtube.py
```

### El script te pedirá por terminal

1. URL o ID de playlist Spotify (**obligatorio**)
2. Nombre de playlist YouTube Music (**obligatorio**)
3. Privacidad de playlist YouTube:
   - `privada` (si dejas vacío, esta es la opción por defecto)
   - `no listada`
   - `publica`

Si dejas URL o nombre vacío, el script volverá a preguntarte.

### Aviso de permisos Spotify (muy importante)

La playlist de Spotify debe cumplir al menos una condición:
1. Es tuya
2. Eres co-creador/colaborador con permisos reales

Si no, Spotify puede responder `403`.

### ¿Qué pasa con `.spotify_cache`?

- No se borra en cada ejecución
- Solo si Spotify devuelve `401/403`, el script te preguntará si deseas borrar `.spotify_cache` y reintentar una vez
- Esto evita logins repetidos cuando no son necesarios

### ¿Qué pasa si no existe `headers.txt`?

Si no existe `headers.txt` (y tampoco `browser.json`), el script:
1. Te avisa en terminal
2. Te muestra mini guía para obtener `headers.txt`
3. Espera a que lo crees
4. Continúa automáticamente

También puedes escribir `omitir` para seguir con OAuth si ya lo configuraste.

---

## Paso 9: Revisar resultados

Al finalizar, verás reporte en terminal con 4 categorías:

1. `agregadas`
2. `no_encontradas`
3. `ya_existian`
4. `error_api`

También se generan archivos:

1. `reporte_migracion_spotify_a_youtube.txt`  
   Incluye contexto (playlist origen/destino, links, resumen y detalle por categoría)
2. `canciones_no_encontradas.txt`  
   Lista de canciones pendientes para revisión manual

---

## ❓ Preguntas frecuentes

### "El script se detuvo a la mitad, ¿pierdo progreso?"

No. Lo que ya se agregó a YouTube Music permanece agregado.

### "¿Puedo migrar varias playlists?"

Sí. Ejecuta de nuevo el script y responde nuevos datos en CLI.

### "¿Puedo seguir usando OAuth en vez de headers.txt?"

Sí. Puedes usar Browser Auth o OAuth. Ambas rutas siguen disponibles.

### "Error 403 en Spotify"

Revisa esto:

1. La playlist es tuya o eres colaborador real
2. Estás con la cuenta Spotify correcta
3. Si el script lo ofrece, acepta regenerar `.spotify_cache`

### "Error 429 (Too Many Requests)"

Espera unos minutos y vuelve a ejecutar.

---

## 📁 Archivos del proyecto

| Archivo | Descripción |
| --- | --- |
| `migrar_spotify_a_youtube.py` | Script principal |
| `src/main.py` | Flujo principal y prompts CLI |
| `src/spotify_client.py` | Lectura de Spotify y manejo de errores 401/403 |
| `src/youtube_client.py` | Conexión YouTube (Browser Auth/OAuth) |
| `.env.ejemplo` | Plantilla de configuración |
| `.env` | Tus credenciales privadas |
| `headers.txt` | Headers manuales (Browser Auth) |
| `browser.json` | Generado desde `headers.txt` |
| `oauth.json` | Sesión OAuth (si eliges OAuth) |
| `.spotify_cache` | Cache de sesión Spotify |
| `reporte_migracion_spotify_a_youtube.txt` | Reporte final completo |
| `canciones_no_encontradas.txt` | Canciones no encontradas |

---

## 🔒 Seguridad básica

Nunca compartas públicamente estos archivos:

- `.env`
- `headers.txt`
- `browser.json`
- `oauth.json`
- `.spotify_cache`

Contienen datos sensibles de autenticación.
