# Estado de la serie — PISO 33

## Datos fijos
- Cuenta: Instagram @sobrevivirias.z (Metricool blogId 8008179, zona horaria America/Argentina/Buenos_Aires).
- Serie actual: **PISO 33**. Última parte publicada o programada: **Parte 7**.
- Publicación: **1 parte por día a las 16:00** (hora de Argentina), en Instagram (Reel) y YouTube (Short).

## Personajes (no cambiar su aspecto)
- **Tú (protagonista):** figura de palitos, cabeza blanca, ojos de punto, **bandana roja** con nudo, campera verde oliva, mochila verde. La narración siempre le habla a él en segunda persona ("tú").
- **Lucía:** vecina del departamento 3302. Pelo castaño largo, campera violeta, mochila. Tiene una **mordida en el brazo** desde hace más de 3 días, sin fiebre: podría ser inmune. Es leal y está asustada.
- **Zombis:** figuras gris verdosas, cabeza verde pálido, ojos oscuros, brazos estirados. Los atrae el ruido.
- **Soldados:** casco verde, en el portón del Hospital Central.

## Cómo va la historia
1. Parte 1, LA PUERTA: Día 1, piso 33, la ciudad cae. Bañera con 150 L de agua, comida para 6 días. La vecina golpea la puerta.
2. Parte 2, LA VENDA: ganó abrir (64%). Lucía entra. La comida baja a 3 días. Día 4: señales de linterna desde la terraza de enfrente. Lucía tiene el brazo vendado.
3. Parte 3, EL ÚLTIMO RESCATE: ganó revisar el brazo (58%). Es una mordida. Día 6: radio anuncia el último rescate desde la terraza del Hospital Central, mañana a las 7, a 12 cuadras.
4. Parte 4, LA ESCALERA: ganó ir juntos (61%). Día 7, 5:30: bajan 33 pisos. Un zombi pasa a centímetros en el piso 12. Cruzan la calle. 6:50: portón del hospital, los soldados revisan brazos, cuello y piernas. **Elección pendiente:** A) decir la verdad sobre la mordida / B) esconder la mordida bajo la campera.
5. Parte 5, LA VERDAD: ganó decir la verdad (57%). Los soldados los frenan; Lucía muestra la mordida: 6 días, sin fiebre. "Si es verdad, vale más que todo este hospital". La llevan en el helicóptero a un laboratorio en el norte, pero tú no estás en la lista. Lucía no quiere irse sin ti. El ruido de las aspas atrae a la calle entera. Quedan 3 minutos para el despegue. Elección: A) dejar que Lucía se vaya sola / B) subir a escondidas al helicóptero.
6. Parte 6, EL POLIZÓN: ganó subir a escondidas (68%). Mientras los soldados corren al portón (la horda lo empuja), subes detrás de Lucía a la terraza y te metes al helicóptero. Te escondes detrás de las cajas de medicinas. Suben Lucía y un soldado; despegan. Veinte minutos después el soldado revisa la carga y te descubre ("¡hay un polizón a bordo!"). Lucía se pone delante: si tú bajas, ella también. El piloto avisa: con tu peso el combustible no alcanza para llegar al norte. Elección: A) aterrizar a cargar combustible en zona infectada / B) tirar las cajas de medicinas.
7. Parte 7, LA SEÑAL: ganó tirar las medicinas (66%). Lucía abre la puerta lateral; tiras las tres cajas al vacío (el soldado te ayuda con la última). Sin la carga, el combustible alcanza por poco. Dos horas después aparece el laboratorio en las montañas nevadas: ni una luz, la radio no responde. En el techo, una figura hace tres destellos con una linterna (señal de auxilio). El combustible se acaba: hay que bajar ya. **Elección pendiente:** A) aterrizar en el laboratorio / B) bajar lejos y llegar a pie.

## Correcciones de coherencia (aplicar desde la Parte 6)
- **Agua:** los 50 L quedaron en el departamento del piso 33. Fuera del edificio el contador de agua tiene que mostrar solo lo que llevan encima (por ejemplo 2 L en las mochilas), no 50 L.
- **Títulos y textos:** siempre en segunda persona ("Dices la verdad…"), nunca en primera ("Dije…"), igual que la narración.

## Hilos abiertos para usar
- Quién hacía señales con la linterna en la terraza de enfrente.
- ¿Lucía es inmune? (un hospital con soldados podría querer estudiarla).
- El helicóptero va hacia el norte: hay un laboratorio (posible destino de Lucía).
- Una horda rodea el hospital (atraída por el rotor).
- Recursos: dejaron 50 L de agua en el departamento; llevan 2 L en las mochilas y nada de comida (HUD Parte 7: día 7, 2 L, 0). Ya no hay cajas de medicinas a bordo (en `heli_in` usar `"boxes": []`).
- El laboratorio del norte está a oscuras y sin radio; alguien en el techo pide auxilio con tres destellos (¿sobreviviente? ¿trampa? ¿relación con las linternas de la terraza de enfrente?). El soldado está molesto por perder las medicinas.
- A bordo: un soldado (casco verde) y un piloto que no se ve; cajas de medicinas con cruz roja para el laboratorio.
- Escenarios nuevos en engine/beanie.py: `rooftop` (terraza del hospital con helipuerto y helicóptero) y `heli_in` (cabina con ventanillas, banco y cajas; en `cast`, `"behind": true` dibuja al personaje detrás de las cajas). Ícono de ficha nuevo: `snow`. Desde la Parte 7: `heli_in` admite `boxes` (cajas que quedan), `toss` ([[caja, fracción]] para tirarlas), `door_open` y `door_t`; escenario `snow_lab` (laboratorio en montañas nevadas, con `heli_fly` y `flashes`/`flash_t`); ícono de ficha `sos`.
- Fichas ya usadas: agua, comida, ruta, escalera, mordidas (OMS), frío en altura, señal de auxilio de a tres.

## Cuando la historia termine
Cuando PISO 33 se acerque a su fin (unas 12 a 16 partes en total), prepará un cierre fuerte en 1 o 2 partes y arrancá una serie nueva al día siguiente. La cuenta es genérica: cada serie tiene su propio nombre, portada y carpeta `historia/<serie>/`.

Ideas para próximas series (elegí la más atrapante y variá el tipo de escenario):
- **EL BÚNKER:** encerrado bajo tierra con aire, comida y energía contados; alguien golpea la escotilla.
- **ISLA:** naufragio en una isla sin agua dulce; señales de otros sobrevivientes.
- **APAGÓN:** la ciudad sin electricidad hace semanas; invierno, saqueos, el edificio se organiza.
- **ESTACIÓN POLAR:** -40°C, la radio se corta, algo afuera no es humano.
- **TÚNEL DEL SUBTE:** atrapado bajo la ciudad tras un derrumbe.

Reglas para cada serie nueva:
- Protagonista propio y reconocible (nada copiado de otros creadores), con los mismos personajes de palitos y el mismo estilo de dibujo.
- Mismo formato: segunda persona, 50–65 s, ficha con un dato real de supervivencia, contadores, elección A/B al final, portada "<SERIE> · PARTE N".
- La primera parte presenta el escenario con un gancho fuerte; los recursos y las reglas del lugar se explican con datos reales.
- Coherencia total entre narración, escenarios y contadores. Escenarios nuevos se agregan en engine/beanie.py con el mismo estilo.
- Actualizar este archivo: serie actual, personajes, estado e hilos abiertos.

## Registro de publicaciones
| Parte | Fecha (ART) | Resultado anunciado en la parte siguiente |
| --- | --- | --- |
| 1 | 10/11 12:37 | 64% abrir |
| 2 | 10/11 16:00 | 58% revisar el brazo |
| 3 | 11/11 12:00 (IG + YouTube) | 61% ir juntos |
| 4 | 11/11 16:00 (IG + YouTube) | 57% decir la verdad |
| 5 | 12/11 16:00 (IG + YouTube) | 68% subir a escondidas |
| 6 | 13/11 16:00 (IG + YouTube, Metricool id 426790343) | 66% tirar las medicinas |
| 7 | 14/11 16:00 (IG + YouTube, Metricool id 427902136) | (pendiente) |

Nota: las Partes 1 y 2 se subieron a YouTube el 11/11 por la mañana.
