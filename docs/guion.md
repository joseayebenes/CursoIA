# Guion de la sesión

Sesión online de 2 horas para un equipo que desarrolla sobre todo en Ada. La pregunta de
fondo: **¿qué puede hacer nuestra IA por nosotros, dónde no llega y qué haría falta?** El
notebook de la sesión es `curso-ia.ipynb`, y sigue este guion bloque a bloque.

Tres actos:

1. **Cómo funciona** (bloques 0 a 2): qué es un modelo de lenguaje y qué modelos tenemos.
2. **Qué puede hacer ya, bien montada** (bloques 3 a 6): se construye en directo un
   asistente sobre el proyecto inventado de `datos/`: buscar, responder con fuentes, trazar
   requisitos y dejar que el modelo use herramientas.
3. **Dónde no llega y hacia dónde ir** (bloque 7).

El hilo es una sola pregunta, que vuelve en casi todos los bloques: **"¿Cuánto tarda en
borrarse una traza?"** (respuesta: 2 s según el requisito SRS-0004 y el diseño; el manual
dice 3 s).

## Reglas para todo el notebook

- **Una idea por celda**, de 10 líneas como mucho. Lo que no se enseña va en `curso/`.
- **Se enseña el JSON**, no solo el Python: es HTTP con JSON, y un desarrollador Ada lo lee
  sin saber Python (y ve que podría llamarlo desde Ada).
- **Pregunta al chat antes de ejecutar** las celdas clave (marcadas abajo): con la cámara
  apagada, es lo que mantiene a la gente dentro.
- **La lista de límites.** Una lista visible en el notebook (`limits`) a la que se añade cada
  fallo en el momento en que aparece, con su tipo: *cualquier modelo*, *nuestros modelos* o
  *nuestra infraestructura*. El bloque 7 la clasifica (ver `limitaciones.md`).
- **Toda llamada al modelo pasa por `curso.llm`** (caché). El notebook se ejecuta entero
  contra el gateway el día antes; en la sesión, todo sale de la caché.
- **Mostrar tiempos y tokens** (`llm.last`) cuando importen: lo lento y lo caro también es
  una lección.

## 0. Gancho (min 0–5)

**Objetivo:** las dos caras del modelo en dos minutos.

- Celda: se da `track_store.adb` al modelo y se le pide que explique `Purge_Stale`. Lo
  explica muy bien.
- Celda: sin darle nada más, "¿Cuánto tarda en borrarse una traza según el manual del
  operador, y qué prueba lo verifica?". Contesta con seguridad y se lo inventa.
- Variante, si hay `logprobs` en el gateway: completar "The software shall delete a track
  within" y enseñar las probabilidades. En OpenRouter, gemma-4 dice **3** con un 85 % y 2
  con un 2 %. El requisito dice 2.
- **A la lista:** "Inventa con seguridad lo que no sabe" (cualquier modelo).
- Cierre: "en dos horas veremos por qué pasan las dos cosas y cómo se arregla la segunda".

## 1. Qué es un modelo de lenguaje (min 5–22)

**Objetivo:** que entiendan por qué inventa, y que el modelo es una función de texto a
texto sin memoria.

1. **Es HTTP con JSON.** La petición y la respuesta en crudo (`llm.to_json`): `model`,
   `messages`, `usage`. Nada más.
2. **Tokens.** Contar los tokens (`usage.prompt_tokens`) de: un requisito en inglés, el
   mismo en español, `Ada.Text_IO.Put_Line`, `SRS-0004`. Pregunta al chat: *¿cuántos
   tokens tiene SRS-0004?* Con `logprobs`, se ven los trozos: se le pide que repita un texto
   literalmente y se listan los tokens de la respuesta.
3. **El siguiente token.** `top_logprobs` sobre una frase a medias: el modelo no "sabe" la
   respuesta, da probabilidades. Sin `logprobs`: repetir la misma pregunta 5 veces.
4. **Temperatura.** La misma pregunta 5 veces con temperatura 0 y con 1. `n` no funciona en
   OpenRouter: son 5 peticiones (con caché, gratis en la sesión).
5. **Sin memoria.** Una segunda petición sin el historial no recuerda la primera: el chat es
   una lista de mensajes que se reenvía entera cada vez. La ventana de contexto (~200k
   tokens en el gateway) y `max_tokens`.
6. **Por qué inventa.** Predice el texto más plausible; no consulta nada. Se le pregunta por
   algo que no existe: "¿Qué parámetros tiene `Track_Store.Purge_All`?". Lo inventa. En Ada,
   más: han visto mucho menos Ada que Python (en el experimento del servidor de sockets se
   inventó la API de GNAT.Sockets).
- **A la lista:** "No tiene memoria entre peticiones" (cualquier modelo); "Inventa APIs, más
  en Ada" (nuestros modelos, y cualquier modelo en menor grado).

## 2. Nuestros modelos (min 22–32)

**Objetivo:** que sepan qué tienen y por qué se usa gemma-4 por defecto.

- La tabla de `modelos.md`: tamaño total y activo (mezcla de expertos), razonamiento, para
  qué está pensado cada uno.
- **Razonamiento:** el mismo problema con `reasoning_effort` `none` y `low`: tokens de
  razonamiento, tiempo y respuesta. Los tokens de razonamiento cuentan en `max_tokens`.
- **La misma tarea a los tres:** "¿Ves algún fallo en `alarms.adb`?" (fallo sembrado 2, ver
  `datos/README.md`). Respuestas lado a lado, con el tiempo. Pregunta al chat: *¿cuál creéis
  que lo encuentra?* Primero solo con el código: ninguno, y cada uno señala otro fallo que
  suena razonable. Después con la sección 3 de `tms_sdd.md` delante (los identificadores se
  reutilizan): los tres. Lo que decide no es el modelo, es lo que tiene delante.
- **A la lista:** "Sin el contexto del sistema no ve el fallo, y señala otros que no lo son"
  (cualquier modelo).

## 3. Que sepa lo nuestro (min 32–55)

**Objetivo:** que entiendan cómo se le da al modelo el conocimiento que no tiene.

1. **Pegarlo todo.** Todo el proyecto (requisitos, diseño, manual) en el prompt y la
   pregunta del hilo. Con 200k de contexto cabe y contesta, pero con todo delante no ve la
   contradicción entre el manual y el diseño. Se enseñan `prompt_tokens` y el tiempo. Y la
   cuenta para un proyecto real (número de documentos × páginas × tokens por página, que se
   mide aquí): no cabe, y aunque cupiera, **no escala**. En el bloque 4, la respuesta con
   fuentes gasta una fracción de esos tokens.
2. **Trocear.** Por tamaño fijo frente a por sección (los `##` del Markdown); con un tamaño
   elegido para que un trozo corte por la mitad la frase de la purga (SDD 4.4). El código,
   por subprograma, no por caracteres.
3. **BM25** con FTS5 de `sqlite3` (viene con Python): la pregunta en español no encuentra el
   diseño en inglés; en el manual, solo si coinciden las palabras.
4. **Embeddings.** Un texto es un vector; la similitud del coseno son tres líneas. Mapa en
   2D (PCA con `numpy`) de los requisitos, los trozos y la pregunta. Pregunta al chat: *¿qué
   frase saldrá más cerca?* La pregunta en español cae junto a la purga del diseño en inglés.
5. **IDs.** Buscar "SRS-0004" por similitud: con `bge-m3` (OpenRouter) acierta por los pelos
   (0,528 frente a 0,528 de SRS-0005). La búsqueda exacta acierta siempre. **Comprobar con
   `embeddinggemma` en el gateway** (`resultados/gateway.md`).
6. **Búsqueda híbrida.** Las tres listas (IDs exactos, vectores, BM25) combinadas con
   Reciprocal Rank Fusion: la tabla con la posición de cada fragmento en cada lista.
- **A la lista:** "Cada técnica de búsqueda falla en algo" (técnica, no modelo).

## Descanso (min 55–65)

## 4. Preguntar con fuentes (min 65–78)

**Objetivo:** el patrón que más va a usarse: responder solo con lo encontrado, citando.

1. **RAG:** pregunta → búsqueda híbrida → prompt con las fuentes numeradas → respuesta que
   cita `[n]`. La pregunta del hilo.
2. **Dos cifras.** El diseño dice 2 s y el manual 3 s. Pregunta al chat: *¿qué hará el
   modelo con dos cifras?* Con fuentes, debería dar las dos y decir de dónde sale cada una.
3. **"No lo sé".** "¿Qué cifrado usan los mensajes al HMI?": no está en ninguna parte.
4. **Verificar un requisito.** SRS-0012 (recuperar las trazas tras un reinicio) contra los
   documentos: el diseño lo deja abierto y el manual dice que la pantalla aparece vacía. Se
   busca con la pregunta reescrita y con 8 fuentes: el requisito está en inglés, el manual en
   español, y hay que mirar en los dos documentos.
- **A la lista:** "Si la búsqueda no trae el fragmento, la respuesta falla" (técnica).

## 5. Lo que no es semántico (min 78–88)

**Objetivo:** el bloque que más va a convencer a un equipo Ada: trazabilidad sin depender de
que el modelo acierte.

1. "¿Qué código implementa SRS-0004 y qué prueba lo verifica?" no es una pregunta para un
   modelo: se leen los `--  Req:` de `src/` (implementa) y de `tests/` (verifica) con una
   expresión regular.
2. Los `with` y las llamadas entre subprogramas forman un grafo (un `dict`).
3. **Impacto:** "si cambio `Logger.Log`, ¿qué requisitos toco?": sus llamadores
   (`Track_Store.Create`, `Delete`, `Alarms.Check`, `Tms_Main`) y los requisitos de cada uno.
4. **Huecos:** requisitos sin código (SRS-0002, 0012, 0042) y con código pero sin prueba.
5. **El modelo, solo para lo que sabe hacer:** sacar los requisitos de una sección del
   manual a JSON con `json_schema`; y sin esquema, cómo se rompe.
- Mensaje: **determinista primero**; el modelo resume, redacta y juzga.

## 6. Agentes (min 88–103)

**Objetivo:** que vean qué es un agente (un bucle) y qué le pasa con Ada.

1. **Herramientas:** se le dan `search`, `get_requirement`, `read_file` y `trace` (las de los
   bloques 3 a 5). El bucle: el modelo pide una herramienta, se ejecuta, se le devuelve el
   resultado, y así hasta que responde o se acaban los pasos. Se enseña la traza de cada
   paso.
2. **"¿Cumple el código SRS-0004?"** Dos veces. Sin razonamiento, se acerca (cumplir los 2 s
   depende del bucle principal) pero no abre `tms_main.adb`, y se contradice. Con la
   configuración que funcionó escribiendo Ada (razonamiento `low`, temperatura 1,0, hasta 15
   pasos) lee `tms_main.adb` y `sensor_input.adb` y encuentra el fallo sembrado 1 (la purga
   solo corre cuando llega un informe), y explica por qué la prueba no lo ve: **la prueba
   pasa y el requisito no se cumple.** A cambio, 11 peticiones.
3. **MCP:** las mismas herramientas, ofrecidas a cualquier editor (VS Code, OpenCode). Con un
   diagrama basta.
4. **El experimento del servidor Ada** (`limitaciones.md`): lo que funcionó y lo que no.
- **A la lista:** sin razonar no comprueba lo que sospecha; bucles con encargos amplios,
  "compila" sin compilar, adapta el test al código (nuestros modelos); un agente gasta
  decenas de peticiones por tarea frente a un cupo de 28 por minuto (infraestructura).

## 7. Límites y hacia dónde ir (min 103–120)

**Objetivo:** salir con una idea clara de qué usar ya, qué no y qué pedir. El contenido está
en `limitaciones.md`.

1. La lista de límites, clasificada en sus tres columnas.
2. Las medidas: con fuentes, los modelos actuales aciertan; programando con agentes, no
   llegan sin una persona al lado.
3. Hacia dónde ir: integración, capacidad, modelos.
4. El semáforo: verde, ámbar, rojo.
5. El diagrama de lo construido en la sesión.

## Lo visto al ejecutar el notebook

El notebook se ejecutó entero con OpenRouter el 14 de octubre (gemma-4 26b; `bge-m3` para los
embeddings), primero como borrador y después como `.ipynb`. **Los textos que comentan cada
salida describen esta ejecución**: con el gateway hay que releerlos.

- **Gancho:** con un prompt de sistema de «asistente del proyecto», se inventa «24 horas» y
  una «Trace Lifecycle Test». (Sin ese prompt no se ha probado.)
- **Tokens:** `SRS-0004` son 6 tokens, y con `logprobs` se ven: `SRS | - | 0 | 0 | 0 | 4`. La
  frase en español, 14 frente a 11 en inglés. Con `max_tokens=20` se corta a media frase
  (`finish_reason: length`).
- **Siguiente token:** «3» un 72 %, «1» un 15 %, «2» (el del requisito) un 4 %.
- **Los tres modelos y `alarms.adb`:** sin la sección 3 del diseño, ninguno encuentra el fallo
  (gemma-4 y devstral echan en falta un aviso al salir de la zona; gpt-oss-120b da cinco
  fallos genéricos); con ella, los tres.
- **Pegarlo todo** contesta «13 s» (10 + los 3 del manual) y no ve la contradicción. Son 3.509
  tokens: unos 830 por página, así que 200 documentos de 50 páginas serían 8 millones.
- **Trocear a 1200 caracteres** corta el diseño en «removal from the disp|lay»: la cifra
  (1,1 s) queda en un trozo y de qué se habla, en el anterior.
- **Coseno:** «Se borra la traza» y «The track is deleted», 0,79; con «Se dispara una alarma»,
  0,53.
- **La híbrida deja fuera el diseño** para la pregunta en español: el manual sale arriba en
  dos de las tres listas. Hace falta **reescribir la pregunta** antes de buscar, y **con
  glosario**: sin él, tradujo «traza» por *trace* (de un log). Con glosario avisa de que el
  manual (3 s) y el diseño (1,1 s) no cuadran, pero trae SRS-0006 en vez de SRS-0004: la
  trampa de los requisitos casi iguales funciona sola. Con fuentes, 1.045 tokens frente a los
  3.509 de pegarlo todo.
- **«¿Qué cifrado…?»:** «No lo sé.» Bien.
- **Verificar SRS-0012:** buscando con el texto del requisito tal cual, no llega el manual y el
  modelo dice que no tiene información de él. Con la pregunta reescrita, el manual sale el
  séptimo; con 8 fuentes contesta «NO», citando el diseño (OI-2) y el manual (la pantalla
  aparece vacía). Al reescribir, el modelo a veces pone las consultas entre comillas:
  `rewrite` las quita.
- **JSON sin esquema:** lo envuelve en texto y en un bloque ```` ```json ````, con campos
  inventados, y `json.loads` falla.
- **Agente sin razonamiento:** lee el requisito, la traza y `track_store.adb`, dice que cumplir
  los 2 s depende del bucle principal, pero no abre `tms_main.adb`; empieza con «no cumple» y
  acaba con «es funcionalmente correcto».
- **Agente con razonamiento `low` y temperatura 1,0:** 10 herramientas (también pide
  `src/main.adb`, que no existe, y sigue con la lista que le devuelve la herramienta), 11
  peticiones y unos 50 s. Con 10 pasos se quedaba sin pasos; con 15, encuentra el fallo de
  `tms_main.adb` y explica por qué la prueba pasa. Con temperatura 1,0 es una muestra: en el
  gateway puede salir otra cosa.

## Antes de la sesión

1. `python -m curso.llm` desde la red de la empresa: proxy, certificados y clave. Después,
   `scripts/check_gateway.py` contra el gateway: qué admite cada modelo y sus nombres
   exactos. Ajustar las demos que dependan de `logprobs`, `n` y `reasoning_effort`.
2. Comprobar las trampas de embeddings con `embeddinggemma` (bloque 3, puntos 4 y 5).
3. Darle a gpt-oss-120b el mismo encargo del servidor Ada (ver `modelos.md`).
4. Ejecutar el notebook entero contra el gateway, con `CURSO_CACHE=refresh python
   scripts/run_notebook.py` (o «Run All» con esa variable), y revisar cada salida y el texto
   que la comenta: si una demo no enseña lo que debe, cambiar la pregunta, no maquillar la
   salida. Versionar la caché del gateway (`cache/gateway/`) y el notebook ejecutado.
5. Exportar el notebook ejecutado a HTML, por si falla todo: `jupyter nbconvert --to html
   curso-ia.ipynb` (`nbconvert` no está en `requirements.txt`; basta en el equipo del
   presentador) o «Export» en el editor.
6. Ensayo con tiempos: el guion va justo. Si hay que recortar, el bloque 3 (dejar
   embeddings y búsqueda híbrida, quitar el detalle de BM25).
