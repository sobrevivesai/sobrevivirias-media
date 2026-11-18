# Procedimiento diario (lo ejecuta la tarea programada)

Objetivo: cada día crear **1 parte nueva** de la serie en el **formato cartoon 3D** (desde la Parte 10), renderizarla, subirla a GitHub Pages y programarla en Instagram (Reel) y YouTube (Short) vía Metricool a las **12:00** (hora de Argentina). Sin intervención humana.

Formato (aprobado por el dueño el 17/11): personajes cartoon 2D (tarjetas dibujadas con `toon33.ts`) dentro de escenarios 3D con contorno de tinta, texturas pintadas, desenfoque de cámara y cámaras que se deslizan. Voz **Piper** (gratis, local): narrador `es_MX-claude-high`, otros personajes `es_MX-ald-medium`. **Subtítulos abajo** (bloques de 1–3 palabras, palabra activa en amarillo). Portada 0,7 s, resultado de la votación arriba al inicio, opciones A/B al final. Música y efectos a la mitad del volumen de la voz.
El formato viejo (`engine/beanie.py`) queda solo como respaldo si el motor 3D falla sin arreglo.

## 1. Preparar
- `git pull`. Ejecutar `bash engine3d/setup.sh` (three.js, Playwright + Chrome, voces Piper desde GitHub releases).
- Leer `historia/ESTADO.md`, la carpeta de la última parte (`historia/<serie>/parteN/`: `script.json`, `episode.json`, `voices.json`) y su escena `engine3d/src/ep/<serie>-pN.ts`.

## 2. Decidir quién ganó la última elección (regla de predicción)
Predecí qué opción elegiría la mayoría pensando en cuál es la más viable para sobrevivir.
- Opción claramente más lógica: 65–82%. Dilema o dos opciones razonables: 51–58%. Nunca 50/50 ni números redondos.

## 3. Escribir la parte nueva (estructura con GANCHO, obligatoria desde la Parte 12)
Crear `historia/<serie>/parteN+1/` con:
- `script.json`: lista de 12–15 frases, **100–125 palabras ⇒ 35–45 s**. Orden fijo:
  - **Frase 0 = GANCHO (máx. 9 palabras, ~2 s).** El momento más fuerte de ESTE capítulo, dicho en presente y segunda persona, cortado justo antes de resolverse. Tiene que generar una pregunta que solo se responde viendo el video. Nada de "en el capítulo anterior", ni números de parte, ni saludos. Ejemplos: "Tu nombre no está en la lista… pero el de Lucía sí." / "Algo respira en el conducto. Y no es el soldado." / "La puerta se cerró sola. Desde afuera."
  - **Frase 1 = CONTEXTO (máx. 16 palabras).** Para quien llega nuevo: quién eres, con quién y qué está en juego. Ej: "Lucía fue mordida hace seis días y no se transformó. Un científico quiere su sangre."
  - **Frase 2 = RESULTADO de la votación, corto.** Ej: "Votaron ventilación: cincuenta y siete por ciento."
  - Frases 3…: la historia, escalando hasta el momento del gancho (que tiene que aparecer de verdad, mismo plano) y un giro más.
  - **Última frase = la pregunta con las 2 opciones.**
  Segunda persona con "tú", español neutro, frases cortas, verbos de acción. Prohibido arrancar lento.
- `episode.json`: `{"serie","parte","titulo","votos":[[57,"OPCIÓN GANADORA"],[43,"OTRA"]],"opciones":["OPCIÓN A","OPCIÓN B"],"frase_votos":2,"gancho_de":<índice de la frase del clímax>,"gancho_desfase":0.3,"gancho_texto":"2-4 PALABRAS EN MAYÚSCULAS"}`. `gancho_texto` es el texto grande que se ve desde el cuadro 0 (ej. "LA PUERTA SE CERRÓ", "ALGO RESPIRA"). Las palabras deben coincidir con el gancho hablado o reforzarlo.
- `voices.json`: `otra_voz` y `parlante` (índices de frases dichas por otro personaje / por un parlante o radio), `pausas` extra por frase. No hay portada: la voz arranca a los 0,12 s.
- **Coherencia total:** todo lo que dice la voz se ve en el plano de esa frase. Mantener el aspecto de los personajes (`engine3d/src/castdefs.ts`). Nada de lo que un personaje no podría saber.

## 4. Escena 3D
- Copiar la escena de la parte anterior a `engine3d/src/ep/<serie>-pN+1.ts` y adaptarla: se reutilizan los escenarios (`SETS`) y se agregan nuevos con el mismo estilo (primitivas + texturas pintadas con `ctex`, contornos automáticos, luz con `LT`).
- **Plano 0 (gancho):** no se programa aparte. La escena ya trae (desde `piso33-p11.ts`) el bloque `GANCHO`: mientras suena la frase 0 muestra el plano de la frase `gancho_de` con zoom lento. Ese plano tiene que ser el más impactante del video (cara de susto en primer plano, la amenaza visible, luz roja, etc.). Plano 1 (contexto): los personajes juntos y reconocibles. Plano 2 (votos): plano tranquilo de la situación (los porcentajes se dibujan arriba solos).
- Un plano por frase: `S[i]` viene de `TIM.S` (inicio de la frase i). Los momentos clave usan anclas de `py/anchors.py` (editar ahí las palabras que disparan acciones, p. ej. un portazo).
- Variar planos (general, dos personajes, inserto de objeto, reacción). Cámara siempre en movimiento suave. Personajes con `idle`/parpadeo, nunca congelados.
- Encuadre vertical angosto: a 4 m solo entran ±0,8 m de ancho. Nada a menos de 1 m de la cámara tapando caras. Texto en escena legible (no espejado).

## 5. Control de calidad y render
- Hoja de cuadros: `bash engine3d/make.sh historia/<serie>/parteN+1 src/ep/<serie>-pN+1.ts stills` (~30 s). Mirar `stills/sheet.jpg` y corregir encuadres, personajes cortados, incoherencias. Repetir hasta que esté bien.
- Render completo en segundo plano (≈ 50 min, 810×1440 escalado a 1080×1920): `bash engine3d/make.sh historia/<serie>/parteN+1 src/ep/<serie>-pN+1.ts full`. Si se corta, volver a correrlo: retoma los cuadros que faltan.
- En la hoja de cuadros revisar SIEMPRE el cuadro 0: tiene que ser la imagen más fuerte del video, con el texto del gancho legible.
- Verificar: duración 35–45 s, y revisar 6 cuadros de `ofr/` (subtítulos legibles abajo, opciones al final).

## Ahorro de uso (obligatorio)
- **Reutilizar todo lo posible:** copiar la escena de la parte anterior y cambiar solo los planos, posiciones y textos. Mientras la historia siga en un lugar ya construido (`ext`, `lab`, `cor`, `cage`…), NO construir escenarios nuevos. Si hace falta uno, armarlo con piezas existentes (`room`, `bench`, `box`, `cyl`, texturas `ctex` ya hechas) y sumarlo a la misma escena para que lo reutilicen las partes siguientes.
- Personajes: usar siempre `castdefs.ts` (no redibujar). Si aparece un personaje nuevo, agregarlo ahí una sola vez.
- No releer archivos completos que ya leíste. Para editar, usar reemplazos puntuales en vez de reescribir el archivo entero.
- Hoja de cuadros: **como máximo 2 rondas** (una para ver y otra después de corregir). No mirar cuadros sueltos uno por uno.
- Render: lanzarlo en segundo plano y controlar con esperas largas (cada ~10 min), sin leer el log entero.
- Verificación final: una sola hoja de 8–16 cuadros del video terminado.

## 6. Subir y programar
- Copiar `historia/<serie>/parteN/out.mp4` a `videos/<serie>-parteN.mp4`, commit y push a `main`. Esperar al menos 3 minutos para que GitHub Pages lo publique. Si Metricool responde que la URL "is not publicly accessible", esperar 2 minutos más y reintentar (hasta 3 veces).
- URL pública: `https://sobrevivesai.github.io/sobrevivirias-media/videos/<serie>-parteN.mp4`
- Metricool `createScheduledPost`, blogId `8008179`:
  - Parte N+1 hoy a las 12:00, timezone America/Argentina/Buenos_Aires. Si ya pasó la hora, programar 10 minutos después de ahora.
  - `providers: [{"network":"instagram"}]`, `instagramData: {"type":"REEL","showReelOnFeed":true,"isAiGenerated":true}`, `videoCoverMilliseconds: 300`, `autoPublish: true`.
  - Texto: 1ª línea con PALABRAS CLAVE EN MAYÚSCULA + ` | PISO 33 · Parte N`; una línea de contexto; `👇 Comenta A o B: ... La mayoría decide la Parte N+1.`; máximo 5 hashtags.
- **YouTube Shorts:** antes de programar, llamar a `getBrandSettings`. Si `networksData` incluye YouTube, agregar `{"network":"youtube"}` a `providers` en la misma publicación, con `youtubeData`: `{"title": "<título de hasta 100 caracteres con PALABRAS CLAVE EN MAYÚSCULA> | <SERIE> Parte N #shorts", "type": "short", "privacy": "public", "madeForKids": false, "isAiGeneratedContent": false, "category": "FILM_ANIMATION", "tags": ["zombies", "supervivencia", "historias interactivas", "tú decides", "<serie>"]}`. Si YouTube no está conectado, publicar solo en Instagram.
- Si Metricool devuelve error (por ejemplo, el límite de 20 publicaciones por mes del plan gratis), no reintentar en bucle: dejarlo anotado y avisar.

## 7. Cerrar
- Actualizar `historia/ESTADO.md`: última parte, resumen de lo que pasó, elección pendiente, hilos abiertos y registro de publicaciones. Commit y push.
- Enviar un resumen corto al dueño: qué parte se programó, a qué hora, quién ganó cada votación y cualquier problema.
