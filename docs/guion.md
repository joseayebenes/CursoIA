# Guion de la sesión

Sesión online de 2 horas para un equipo que desarrolla sobre todo en Ada. La pregunta de
fondo: **¿qué puede hacer nuestra IA por nosotros, dónde no llega y qué haría falta?**

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
  `datos/README.md`), con `tms_sdd.md` sección 3 como contexto. Respuestas lado a lado, con
  tiempo y tokens. Pregunta al chat: *¿cuál creéis que lo encuentra?*
- **A la lista:** lo que salga de la comparación (nuestros modelos).

## 3. Que sepa lo nuestro (min 32–55)

**Objetivo:** que entiendan cómo se le da al modelo el conocimiento que no tiene.

1. **Pegarlo todo.** Todo el proyecto (requisitos, diseño, manual) en el prompt y la
   pregunta del hilo. Con 200k de contexto cabe y acierta. Se enseñan `prompt_tokens` y el
   tiempo. Después, la misma pregunta con solo 5 fragmentos: misma respuesta, una fracción
   de tokens y de tiempo. Y la cuenta para un proyecto real (número de documentos × páginas
   × tokens por página, que se mide aquí): **no es que no quepa, es que no escala.**
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
   documentos: el diseño lo deja abierto y el manual dice que la pantalla aparece vacía.
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
2. **"¿Cumple el código SRS-0004?"** Con suerte, lee el requisito, el diseño,
   `track_store.adb` y `tms_main.adb` y encuentra el fallo sembrado 1 (la purga solo corre
   cuando llega un informe). La prueba de SRS-0004 pasa: **la prueba pasa y el requisito no
   se cumple.**
3. **MCP:** las mismas herramientas, ofrecidas a cualquier editor (VS Code, OpenCode). Con un
   diagrama basta.
4. **El experimento del servidor Ada** (`limitaciones.md`): lo que funcionó y lo que no.
- **A la lista:** bucles con encargos amplios, "compila" sin compilar, adapta el test al
  código (nuestros modelos); un agente gasta decenas de peticiones por tarea frente a un
  cupo de 28 por minuto (infraestructura).

## 7. Límites y hacia dónde ir (min 103–120)

**Objetivo:** salir con una idea clara de qué usar ya, qué no y qué pedir. El contenido está
en `limitaciones.md`.

1. La lista de límites, clasificada en sus tres columnas.
2. Las medidas: con fuentes, los modelos actuales aciertan; programando con agentes, no
   llegan sin una persona al lado.
3. Hacia dónde ir: integración, capacidad, modelos.
4. El semáforo: verde, ámbar, rojo.
5. El diagrama de lo construido en la sesión.

## Antes de la sesión

1. `python -m curso.llm` desde la red de la empresa: proxy, certificados y clave. Después,
   `scripts/check_gateway.py` contra el gateway: qué admite cada modelo y sus nombres
   exactos. Ajustar las demos que dependan de `logprobs`, `n` y `reasoning_effort`.
2. Comprobar las trampas de embeddings con `embeddinggemma` (bloque 3, puntos 4 y 5).
3. Darle a gpt-oss-120b el mismo encargo del servidor Ada (ver `modelos.md`).
4. Ejecutar el notebook entero contra el gateway con `CURSO_CACHE=refresh` y revisar cada
   salida: si una demo no enseña lo que debe, cambiar la pregunta, no maquillar la salida.
5. Exportar el notebook ejecutado a HTML, por si falla todo.
6. Ensayo con tiempos: el guion va justo. Si hay que recortar, el bloque 3 (dejar
   embeddings y búsqueda híbrida, quitar el detalle de BM25).
