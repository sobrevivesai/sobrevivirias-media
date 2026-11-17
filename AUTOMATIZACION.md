# Procedimiento diario (lo ejecuta la tarea programada)

Objetivo: cada día crear **1 parte nueva** de la serie en el **formato cartoon 3D** (desde la Parte 10), renderizarla, subirla a GitHub Pages y programarla en Instagram (Reel) y YouTube (Short) vía Metricool a las **16:00** (hora de Argentina). Sin intervención humana.

Formato (aprobado por el dueño el 17/11): personajes cartoon 2D (tarjetas dibujadas con `toon33.ts`) dentro de escenarios 3D con contorno de tinta, texturas pintadas, desenfoque de cámara y cámaras que se deslizan. Voz **Piper** (gratis, local): narrador `es_MX-claude-high`, otros personajes `es_MX-ald-medium`. **Subtítulos abajo** (bloques de 1–3 palabras, palabra activa en amarillo). Portada 0,7 s, resultado de la votación arriba al inicio, opciones A/B al final. Música y efectos a la mitad del volumen de la voz.
El formato viejo (`engine/beanie.py`) queda solo como respaldo si el motor 3D falla sin arreglo.

## 1. Preparar
- `git pull`. Ejecutar `bash engine3d/setup.sh` (three.js, Playwright + Chrome, voces Piper desde GitHub releases).
- Leer `historia/ESTADO.md`, la carpeta de la última parte (`historia/<serie>/parteN/`: `script.json`, `episode.json`, `voices.json`) y su escena `engine3d/src/ep/<serie>-pN.ts`.

## 2. Decidir quién ganó la última elección (regla de predicción)
Predecí qué opción elegiría la mayoría pensando en cuál es la más viable para sobrevivir.
- Opción claramente más lógica: 65–82%. Dilema o dos opciones razonables: 51–58%. Nunca 50/50 ni números redondos.

## 3. Escribir la parte nueva
Crear `historia/<serie>/parteN+1/` con:
- `script.json`: lista de 14–17 frases (~140–160 palabras ⇒ 55–62 s). Frase 0 = resultado ("El 63 por ciento eligió…", números escritos en palabras). Última frase = la pregunta con las 2 opciones. Segunda persona con "tú", español neutro, frases cortas, gancho fuerte, giro al final.
- `episode.json`: `{"serie","parte","titulo" (2–3 palabras en MAYÚSCULAS),"votos":[[63,"OPCIÓN GANADORA"],[37,"OTRA"]],"opciones":["OPCIÓN A","OPCIÓN B"]}`.
- `voices.json`: `otra_voz` y `parlante` (índices de frases dichas por otro personaje / por un parlante o radio) y `pausas` extra por frase.
- **Coherencia total:** todo lo que dice la voz se ve en el plano de esa frase. Mantener el aspecto de los personajes (`engine3d/src/castdefs.ts`). Nada de lo que un personaje no podría saber.

## 4. Escena 3D
- Copiar la escena de la parte anterior a `engine3d/src/ep/<serie>-pN+1.ts` y adaptarla: se reutilizan los escenarios (`SETS`) y se agregan nuevos con el mismo estilo (primitivas + texturas pintadas con `ctex`, contornos automáticos, luz con `LT`).
- Un plano por frase: `S[i]` viene de `TIM.S` (inicio de la frase i). Los momentos clave usan anclas de `py/anchors.py` (editar ahí las palabras que disparan acciones, p. ej. un portazo).
- Variar planos (general, dos personajes, inserto de objeto, reacción). Cámara siempre en movimiento suave. Personajes con `idle`/parpadeo, nunca congelados.
- Encuadre vertical angosto: a 4 m solo entran ±0,8 m de ancho. Nada a menos de 1 m de la cámara tapando caras. Texto en escena legible (no espejado).

## 5. Control de calidad y render
- Hoja de cuadros: `bash engine3d/make.sh historia/<serie>/parteN+1 src/ep/<serie>-pN+1.ts stills` (~30 s). Mirar `stills/sheet.jpg` y corregir encuadres, personajes cortados, incoherencias. Repetir hasta que esté bien.
- Render completo en segundo plano (≈ 50 min, 810×1440 escalado a 1080×1920): `bash engine3d/make.sh historia/<serie>/parteN+1 src/ep/<serie>-pN+1.ts full`. Si se corta, volver a correrlo: retoma los cuadros que faltan.
- Verificar: duración 50–65 s, y revisar 6 cuadros de `ofr/` (subtítulos legibles abajo, opciones al final).

## 6. Subir y programar
- Copiar `historia/<serie>/parteN/out.mp4` a `videos/<serie>-parteN.mp4`, commit y push a `main`. Esperar al menos 3 minutos para que GitHub Pages lo publique. Si Metricool responde que la URL "is not publicly accessible", esperar 2 minutos más y reintentar (hasta 3 veces).
- URL pública: `https://sobrevivesai.github.io/sobrevivirias-media/videos/<serie>-parteN.mp4`
- Metricool `createScheduledPost`, blogId `8008179`:
  - Parte N+1 hoy a las 16:00, timezone America/Argentina/Buenos_Aires. Si ya pasó la hora, programar 10 minutos después de ahora.
  - `providers: [{"network":"instagram"}]`, `instagramData: {"type":"REEL","showReelOnFeed":true,"isAiGenerated":true}`, `videoCoverMilliseconds: 300`, `autoPublish: true`.
  - Texto: 1ª línea con PALABRAS CLAVE EN MAYÚSCULA + ` | PISO 33 · Parte N`; una línea de contexto; `👇 Comenta A o B: ... La mayoría decide la Parte N+1.`; máximo 5 hashtags.
- **YouTube Shorts:** antes de programar, llamar a `getBrandSettings`. Si `networksData` incluye YouTube, agregar `{"network":"youtube"}` a `providers` en la misma publicación, con `youtubeData`: `{"title": "<título de hasta 100 caracteres con PALABRAS CLAVE EN MAYÚSCULA> | <SERIE> Parte N #shorts", "type": "short", "privacy": "public", "madeForKids": false, "isAiGeneratedContent": false, "category": "FILM_ANIMATION", "tags": ["zombies", "supervivencia", "historias interactivas", "tú decides", "<serie>"]}`. Si YouTube no está conectado, publicar solo en Instagram.
- Si Metricool devuelve error (por ejemplo, el límite de 20 publicaciones por mes del plan gratis), no reintentar en bucle: dejarlo anotado y avisar.

## 7. Cerrar
- Actualizar `historia/ESTADO.md`: última parte, resumen de lo que pasó, elección pendiente, hilos abiertos y registro de publicaciones. Commit y push.
- Enviar un resumen corto al dueño: qué parte se programó, a qué hora, quién ganó cada votación y cualquier problema.
