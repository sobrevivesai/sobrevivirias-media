# Procedimiento diario (lo ejecuta la tarea programada)

Objetivo: cada día crear las 2 partes siguientes de la serie, renderizarlas, subirlas a GitHub Pages y programarlas en Instagram vía Metricool a las 12:00 y 16:00 (hora de Argentina). Sin intervención humana.

## 1. Preparar
- `git pull` del repo. Ejecutar `bash engine/setup.sh` (instala la voz Kokoro desde npm/PyPI en /home/claude/tts).
- Leer `historia/ESTADO.md` y las 2 últimas partes en `historia/<serie>/parteN.json` (el formato de los JSON es el ejemplo a seguir).

## 2. Decidir quién ganó la última elección (regla de predicción)
Predecí qué opción elegiría la mayoría de la gente pensando en cuál es la más viable para sobrevivir.
- Si una opción es claramente la más lógica: gana con un porcentaje alto (65–82%).
- Si las dos son razonables o es un dilema moral: resultado peleado (51–58%).
- Nunca 50/50 ni porcentajes redondos (usar, por ejemplo, 63, 57, 71).
La parte de las 16:00 también arranca con el resultado de la elección de la parte de las 12:00 (predicho con la misma regla).

## 3. Escribir las 2 partes nuevas (parteN+1.json y parteN+2.json)
Reglas de guion (pedidas por el dueño de la cuenta):
- Narración en segunda persona con "tú", español neutro. Voz em_alex.
- 50–65 s por parte, 10–12 escenas de 3–6 s. Gancho fuerte en el primer segundo.
- La primera escena es `results` con el resultado de la elección anterior. La última es `choice` con 2 opciones (sin texto "¿qué hago?").
- Una ficha `card` por parte con un dato real y verificable de supervivencia (sin símbolos raros como ≈ o →).
- Contadores `hud` (día, agua, comida) coherentes con la historia.
- **Coherencia total:** todo lo que dice la voz se tiene que ver y estar sincronizado (si alguien "trae una mochila", se le ve; si algo se llena, empieza vacío). Mantener el aspecto de los personajes.
- Portada: campos `serie`, `titulo` (2–3 palabras) y `cover` con una escena de fondo.
- Si hace falta un escenario nuevo, agregarlo en `engine/beanie.py` (funciones `bg` y `dynamic`) con el mismo estilo: paleta apagada, contornos temblorosos (clase SK), figuras con `figure()`.

## 4. Control de calidad antes de renderizar
- Vista previa de varios momentos: `python3 engine/beanie.py p6 historia/<serie>/parteN.json <escena> <segundo> /tmp/x.png`. Armar una hoja con 10–14 cuadros, mirarla y corregir errores (texto tapado, personajes fuera de cuadro, incoherencias).

## 5. Renderizar y verificar
- `python3 engine/beanie.py v6 historia/<serie>/parteN.json out/<SERIE>_ParteN.mp4` (unos 4 min por parte).
- Verificar duración (50–65 s) y revisar 6 cuadros del video final.

## 6. Subir y programar
- Copiar a `videos/<serie>-parteN.mp4`, commit y push a `main`. Esperar unos 2 minutos para que GitHub Pages lo publique.
- URL pública: `https://sobrevivesai.github.io/sobrevivirias-media/videos/<serie>-parteN.mp4`
- Metricool `createScheduledPost`, blogId `8008179`, una por parte:
  - Parte N+1 hoy 12:00 y Parte N+2 hoy 16:00, timezone America/Argentina/Buenos_Aires. Si ya pasó la hora, programar 10 minutos después de ahora.
  - `providers: [{"network":"instagram"}]`, `instagramData: {"type":"REEL","showReelOnFeed":true,"isAiGenerated":true}`, `videoCoverMilliseconds: 300`, `autoPublish: true`.
  - Texto: 1ª línea con PALABRAS CLAVE EN MAYÚSCULA + ` | PISO 33 · Parte N`; una línea de contexto; `👇 Comenta A o B: ... La mayoría decide la Parte N+1.`; máximo 5 hashtags.
- **YouTube Shorts:** antes de programar, llamar a `getBrandSettings`. Si `networksData` incluye YouTube, agregar `{"network":"youtube"}` a `providers` en la misma publicación, con `youtubeData`: `{"title": "<título de hasta 100 caracteres con PALABRAS CLAVE EN MAYÚSCULA> | <SERIE> Parte N #shorts", "type": "short", "privacy": "public", "madeForKids": false, "isAiGeneratedContent": false, "category": "FILM_ANIMATION", "tags": ["zombies", "supervivencia", "historias interactivas", "tú decides", "<serie>"]}`. Si YouTube no está conectado, publicar solo en Instagram.
- Si Metricool devuelve error (por ejemplo, el límite de 20 publicaciones por mes del plan gratis), no reintentar en bucle: dejarlo anotado y avisar.

## 7. Cerrar
- Actualizar `historia/ESTADO.md`: última parte, resumen de lo que pasó, elección pendiente, hilos abiertos y registro de publicaciones. Commit y push.
- Enviar un resumen corto al dueño: qué partes se programaron, a qué hora, quién ganó cada votación y cualquier problema.
