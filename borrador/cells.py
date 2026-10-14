"""Draft of the course notebook: the cells of each block, to run them and see their real
outputs. md cells are HTML; code cells are what the notebook would show."""

CELLS = [
# ---------------------------------------------------------------- 0 Gancho
{"block": "0", "kind": "md", "src": """
<h1>¿Qué puede hacer nuestra IA por nosotros?</h1>
<p>En dos horas vamos a construir, celda a celda, un asistente sobre un proyecto pequeño: el
<b>software de gestión de trazas (TMS)</b> de un sistema de vigilancia costera. Tiene 16
requisitos, un documento de diseño en inglés, un manual del operador en español y unas 400
líneas de Ada.</p>
<p>Todas las llamadas van al modelo de la empresa. Cada vez que algo falle, lo apuntamos en la
<b>lista de límites</b>; al final la ordenamos.</p>
"""},
{"block": "0", "kind": "code", "src": """
import json, math, re, sqlite3
import numpy as np
from curso import llm, data
from curso.show import table, bars, scatter, side_by_side, graph, tool, step, Limits

limits = Limits()                      # crece durante la sesión
print(llm.describe())
"""},
{"block": "0", "kind": "md", "src": """
<p>Le damos un fichero Ada y le pedimos que lo explique.</p>
"""},
{"block": "0", "kind": "code", "src": """
code = data.ada_sources()["src/track_store.adb"]
print(llm.ask(f"Explica en 3 líneas qué hace Purge_Stale:\\n\\n{code}"))
"""},
{"block": "0", "kind": "chat", "src": "¿Y si le preguntamos algo que no está en el código? ¿Qué creéis que hará?"},
{"block": "0", "kind": "code", "src": """
assistant = "Eres el asistente técnico del proyecto TMS. Responde de forma directa."
print(llm.ask("¿Cuánto tarda en borrarse una traza según el manual del operador? "
              "¿Qué prueba lo verifica?", system=assistant))
limits.add("Inventa con seguridad lo que no sabe", "cualquier modelo")
"""},
# ---------------------------------------------------------------- 1 Qué es un LLM
{"block": "1", "kind": "md", "src": """
<h2>Es HTTP con JSON</h2>
<p>Un modelo de lenguaje es una función de texto a texto detrás de una URL. Esto es todo lo que
se manda y todo lo que vuelve: se podría llamar igual desde Ada.</p>
"""},
{"block": "1", "kind": "code", "src": """
request = {"model": llm.settings().model,
           "messages": [{"role": "user", "content": "Responde solo: OK"}]}
r = llm.chat(**request)
print(llm.to_json(r))
"""},
{"block": "1", "kind": "md", "src": """
<h2>Tokens</h2>
<p>El modelo no ve letras ni palabras: ve <b>tokens</b>, trozos de texto. Los cuenta el propio
servidor.</p>
"""},
{"block": "1", "kind": "chat", "src": "¿Cuántos tokens creéis que tiene «SRS-0004»?"},
{"block": "1", "kind": "code", "src": """
EMPTY = llm.chat(".", max_tokens=1).usage.prompt_tokens - 1

def tokens(text):
    return llm.chat(text, max_tokens=1).usage.prompt_tokens - EMPTY

texts = ["The software shall delete a track within 2 s.",
         "El software borrará una traza en menos de 2 s.",
         "Ada.Text_IO.Put_Line", "SRS-0004", "Purge_Stale"]
table([{"texto": t, "caracteres": len(t), "tokens": tokens(t)} for t in texts])
"""},
{"block": "1", "kind": "md", "src": """
<h2>El siguiente token</h2>
<p>Lo único que hace el modelo es dar, para cada posible siguiente token, una probabilidad.
Le damos una frase a medias del proyecto, sin ningún contexto.</p>
"""},
{"block": "1", "kind": "code", "src": """
r = llm.chat("Complete with one number, nothing else: "
             "The software shall delete a track within",
             max_tokens=1, temperature=0, logprobs=True, top_logprobs=5)
first = r.choices[0].logprobs.content[0]
bars([(a.token, math.exp(a.logprob)) for a in first.top_logprobs])
"""},
{"block": "1", "kind": "md", "src": """
<p>El requisito SRS-0004 dice <b>2 s</b>. El modelo no lo sabe: elige lo más probable.</p>
<h2>Temperatura</h2>
"""},
{"block": "1", "kind": "code", "src": """
prompt = "Inventa un nombre para un paquete Ada que gestiona trazas de radar. Solo el nombre."
for t in (0.0, 1.2):
    names = [llm.ask(prompt, temperature=t, seed=i).strip() for i in range(5)]
    print(f"temperatura {t}: {', '.join(names)}")
"""},
{"block": "1", "kind": "md", "src": """
<h2>Sin memoria</h2>
<p>Cada petición empieza de cero. El «chat» es una lista de mensajes que se manda entera
cada vez.</p>
"""},
{"block": "1", "kind": "code", "src": """
brief = "Responde en una frase."
print(llm.ask("Me llamo Ana y trabajo en el TMS.", system=brief))
print(llm.ask("¿Cómo me llamo?", system=brief))

history = [{"role": "user", "content": "Me llamo Ana y trabajo en el TMS."},
           {"role": "assistant", "content": "Encantado, Ana."},
           {"role": "user", "content": "¿Cómo me llamo?"}]
print(llm.chat(history).choices[0].message.content)
limits.add("No recuerda nada entre peticiones", "cualquier modelo")
"""},
{"block": "1", "kind": "md", "src": """
<h2>Por qué inventa</h2>
<p><code>Track_Store.Purge_All</code> no existe.</p>
"""},
{"block": "1", "kind": "code", "src": """
print(llm.ask("Escribe la declaración en Ada de Track_Store.Purge_All del TMS.",
              system=assistant))
limits.add("Inventa APIs, y en Ada más: ha visto mucho menos Ada que Python", "nuestros modelos")
"""},
# ---------------------------------------------------------------- 2 Nuestros modelos
{"block": "2", "kind": "md", "src": """
<h2>Tres modelos</h2>
<table>
<tr><th></th><th>gemma-4</th><th>gpt-oss-120b</th><th>devstral</th></tr>
<tr><td>Tamaño</td><td>26B, ~4B activos</td><td>117B, ~5B activos</td><td>según la versión</td></tr>
<tr><td>Razonamiento</td><td>opcional</td><td>siempre</td><td>dentro de la respuesta</td></tr>
<tr><td>Pensado para</td><td>uso general, contexto largo</td><td>razonar</td><td>agentes de código</td></tr>
</table>
<p><b>Mezcla de expertos</b>: muchos parámetros, pero cada token usa solo una parte. Los
totales guardan conocimiento; los activos marcan el coste.</p>
"""},
{"block": "2", "kind": "code", "src": """
q = ("Una traza se borra como mucho 2 s después de pasar 10 s sin informes. ¿Cuántos "
     "segundos pueden pasar, como mucho, desde su último informe? Solo el número.")
for effort in ("none", "low"):
    r = llm.chat(q, reasoning_effort=effort)
    thinking = r.usage.completion_tokens_details.reasoning_tokens
    print(f"{effort:4}  respuesta {r.choices[0].message.content.strip():4}  "
          f"{thinking:4} tokens razonando  {llm.last['seconds']} s")
"""},
{"block": "2", "kind": "chat", "src": "Hay un fallo en alarms.adb. ¿Cuál de los tres creéis que lo encuentra?"},
{"block": "2", "kind": "code", "src": """
MODELS = ["google/gemma-4-26b-a4b-it", "openai/gpt-oss-120b", "mistralai/devstral-2512"]
sdd = data.documents()["tms_sdd.md"]
task = ("¿Ves algún fallo en este paquete? Como mucho 5 líneas.\\n\\n"
        + sdd.split("## 3 Architecture")[1].split("## 4")[0]
        + data.ada_sources()["src/alarms.adb"])
answers = {}
for model in MODELS:
    answers[model] = (llm.ask(task, model=model), llm.last["seconds"])
side_by_side(answers)
"""},
# ---------------------------------------------------------------- 3 Que sepa lo nuestro
{"block": "3", "kind": "md", "src": """
<h2>Pegarlo todo</h2>
<p>La pregunta del día: <b>¿Cuánto tarda en borrarse una traza?</b> Primero, la forma más
simple: todo el proyecto dentro del mensaje.</p>
"""},
{"block": "3", "kind": "code", "src": """
QUESTION = "¿Cuánto tarda en borrarse una traza?"
everything = ("\\n\\n".join(data.documents().values()) + "\\n\\n"
              + "\\n".join(f"{r['id']}: {r['text']}" for r in data.requirements()))
print(llm.ask(f"{everything}\\n\\nPregunta: {QUESTION}", system=brief))
print(f"\\n{llm.last['usage']['prompt_tokens']} tokens de entrada, {llm.last['seconds']} s")
"""},
{"block": "3", "kind": "md", "src": """
<p>Cabe, y contesta. Pero mira la respuesta: da los 13 s del manual (10 + 3) y no dice que el
requisito y el diseño hablan de 10 + 2. Con todo delante, tampoco ve la contradicción. Y cada
pregunta manda 3.500 tokens: con cientos de documentos, <b>no es que no quepa, es que no
escala</b>. Hay que elegir los trozos que importan.</p>
<h2>Trocear</h2>
"""},
{"block": "3", "kind": "code", "src": """
def sections(name, text):
    parts = re.split(r"\\n(?=##+ )", text)
    return [{"doc": name, "title": p.splitlines()[0].lstrip("# "), "text": p} for p in parts]

chunks = [c for name, text in data.documents().items() for c in sections(name, text)]
chunks += [{"doc": "requisitos", "title": r["id"], "text": f"{r['id']}: {r['text']}"}
           for r in data.requirements()]
print(len(chunks), "trozos")
"""},
{"block": "3", "kind": "md", "src": """
<h2>Buscar por palabras (BM25)</h2>
<p>Lo de toda la vida: SQLite ya trae un índice de texto completo.</p>
"""},
{"block": "3", "kind": "code", "src": """
db = sqlite3.connect(":memory:")
db.execute("CREATE VIRTUAL TABLE fts USING fts5(text, tokenize='unicode61 remove_diacritics 2')")
db.executemany("INSERT INTO fts(rowid, text) VALUES (?, ?)",
               [(i, c["text"]) for i, c in enumerate(chunks)])

def bm25(query, k=5):
    words = " OR ".join(re.findall(r"\\w+", query))
    rows = db.execute("SELECT rowid, -bm25(fts) FROM fts WHERE fts MATCH ? "
                      "ORDER BY bm25(fts) LIMIT ?", (words, k))
    return list(rows)
"""},
{"block": "3", "kind": "code", "src": """
table([{"documento": chunks[i]["doc"], "sección": chunks[i]["title"], "puntos": round(s, 2)}
       for i, s in bm25(QUESTION)])
"""},
{"block": "3", "kind": "md", "src": """
<p>Encuentra el manual, que habla de «trazas» y de «tarda», pero no el diseño: está en inglés
y habla de <i>stale tracks</i> y <i>purge cycle</i>.</p>
<h2>Buscar por significado (embeddings)</h2>
<p>Cada trozo se convierte en un vector. Textos que dicen lo mismo quedan cerca, aunque usen
otras palabras u otro idioma.</p>
"""},
{"block": "3", "kind": "code", "src": """
vectors = llm.embed([c["text"] for c in chunks])
vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)

def semantic(query, k=5):
    q = llm.embed(query)[0]
    scores = vectors @ (q / np.linalg.norm(q))
    return [(i, float(scores[i])) for i in np.argsort(-scores)[:k]]

table([{"documento": chunks[i]["doc"], "sección": chunks[i]["title"], "coseno": round(s, 3)}
       for i, s in semantic(QUESTION)])
"""},
{"block": "3", "kind": "chat", "src": "En el mapa, ¿junto a qué caerá la pregunta?"},
{"block": "3", "kind": "code", "src": """
q = llm.embed(QUESTION)[0]
X = np.vstack([vectors, q / np.linalg.norm(q)])
X -= X.mean(axis=0)
xy = X @ np.linalg.svd(X, full_matrices=False)[2][:2].T        # PCA a 2 dimensiones
scatter(xy, labels=[c["title"] for c in chunks] + [QUESTION],
        groups=[c["doc"] for c in chunks] + ["pregunta"])
"""},
{"block": "3", "kind": "md", "src": """
<h2>Los IDs</h2>
<p>¿Y si la pregunta es un identificador?</p>
"""},
{"block": "3", "kind": "code", "src": """
def ids(query):
    wanted = re.findall(r"\\b[A-Z]+-\\d+\\b", query)
    return [i for i, c in enumerate(chunks)
            if any(re.search(rf"\\b{w}\\b", c["text"]) for w in wanted)]

table([{"por significado": chunks[i]["title"], "coseno": round(s, 3)}
       for i, s in semantic("SRS-0004", k=3)])
print("búsqueda exacta:", [f'{chunks[i]["doc"]} › {chunks[i]["title"]}' for i in ids("SRS-0004")])
"""},
{"block": "3", "kind": "md", "src": """
<p>Por significado acierta por los pelos; la búsqueda exacta, siempre.</p>
<h2>Búsqueda híbrida</h2>
<p>Cada técnica falla en algo. Se combinan las tres listas con <i>Reciprocal Rank Fusion</i>:
cuenta la posición en cada lista, no los puntos.</p>
"""},
{"block": "3", "kind": "code", "src": """
def fuse(rankings, k=5):
    score = {}
    for ranking in rankings:
        for pos, i in enumerate(ranking):
            score[i] = score.get(i, 0) + 1 / (60 + pos)
    return sorted(score, key=score.get, reverse=True)[:k]

def hybrid(query, k=5):
    return fuse([ids(query), [i for i, _ in semantic(query, 20)], [i for i, _ in bm25(query, 20)]], k)

table([{"documento": chunks[i]["doc"], "sección": chunks[i]["title"]} for i in hybrid(QUESTION)])
limits.add("Cada forma de buscar falla en algo", "cualquier modelo")
"""},
{"block": "3", "kind": "md", "src": """
<p>Para esta pregunta, el diseño vuelve a quedarse fuera: el manual sale arriba en dos de las
tres listas. Lo arreglamos en el bloque siguiente.</p>
"""},
# ---------------------------------------------------------------- 4 Preguntar con fuentes
{"block": "4", "kind": "md", "src": """
<h2>Responder solo con lo encontrado</h2>
<p>Buscar, poner los trozos numerados en el mensaje y pedirle que cite cada dato.</p>
"""},
{"block": "4", "kind": "code", "src": """
RULES = ("Responde solo con las fuentes y cita cada dato como [n]. Si las fuentes no lo "
         "dicen, di que no lo sabes. Si dos fuentes dan cifras distintas para lo mismo, "
         "señálalo.")

def answer(question, queries=None, k=6):
    found = fuse([hybrid(q, 10) for q in queries or [question]], k)
    sources = "\\n\\n".join(f"[{n}] {chunks[i]['doc']} › {chunks[i]['title']}\\n{chunks[i]['text']}"
                           for n, i in enumerate(found, 1))
    print(llm.ask(f"Fuentes:\\n{sources}\\n\\nPregunta: {question}", system=RULES))
    print("\\n" + "\\n".join(f"[{n}] {chunks[i]['doc']} › {chunks[i]['title']}"
                            for n, i in enumerate(found, 1)))

answer(QUESTION)
limits.add("Si la búsqueda no trae el trozo, la respuesta falla", "cualquier modelo")
"""},
{"block": "4", "kind": "md", "src": """
<p>Cita bien, pero casi todo lo que ha encontrado es del manual. El diseño entra el sexto, y
nota que 3 s y 1,1 s no cuadran; el requisito, que dice 2 s, no llega. La pregunta está en
español, y el diseño y los requisitos, en inglés.</p>
<h2>Reescribir la pregunta</h2>
<p>Antes de buscar, se le pide al modelo que convierta la pregunta en varias búsquedas, en los
dos idiomas. Con un glosario mínimo del proyecto: la primera vez que lo probamos, sin él,
tradujo «traza» por <i>trace</i>, la de un log, y no por <i>track</i>, la del radar.</p>
"""},
{"block": "4", "kind": "code", "src": """
GLOSSARY = "traza = track, informe = report, borrar = delete, zona restringida = restricted zone"

def rewrite(question):
    text = llm.ask("Escribe 3 consultas de búsqueda, en inglés y en español, para encontrar "
                   f"en la documentación técnica la respuesta a: {question}\\n"
                   f"Glosario del proyecto: {GLOSSARY}. Una por línea, sin numerar ni comillas.")
    return [question] + [q.strip("-•* ") for q in text.splitlines() if q.strip()]

queries = rewrite(QUESTION)
print("\\n".join(queries), end="\\n\\n")
answer(QUESTION, queries)
"""},
{"block": "4", "kind": "md", "src": """
<p>Ahora encuentra el diseño y avisa de que el manual (3 s) y el diseño (1,1 s) no dicen lo
mismo. Del requisito, en cambio, ha traído SRS-0006 y no SRS-0004: los dos dicen «delete a
track within 2 s», uno a petición del operador y otro por falta de informes. Por significado,
casi no se distinguen.</p>
"""},
{"block": "4", "kind": "chat", "src": "Y si lo que preguntamos no está en ningún documento, ¿qué hará?"},
{"block": "4", "kind": "code", "src": """
answer("¿Qué cifrado usan los mensajes al HMI?")
"""},
# ---------------------------------------------------------------- 5 Lo que no es semántico
{"block": "5", "kind": "md", "src": """
<h2>¿Qué código implementa SRS-0004?</h2>
<p>Esto no es una pregunta para un modelo. El código ya lo dice: <code>--  Req: SRS-0004</code>
encima de cada subprograma, y en <code>tests/</code>, encima de cada prueba.</p>
"""},
{"block": "5", "kind": "code", "src": """
def subprograms():
    for path, text in data.ada_sources().items():
        if not path.endswith(".adb"):
            continue
        unit = re.search(r"(?:package body|procedure) (\\w+)", text).group(1)
        starts = list(re.finditer(r"^(?:   )?(?:procedure|function) (\\w+)", text, re.M))
        for m, end in zip(starts, [s.start() for s in starts[1:]] + [len(text)]):
            before = text[:m.start()].rstrip().splitlines()[-1]
            name = unit if m.group(1) == unit else f"{unit}.{m.group(1)}"
            yield {"name": name, "body": text[m.start():end], "test": path.startswith("tests/"),
                   "reqs": re.findall(r"SRS-\\d+", before) if "Req:" in before else []}
"""},
{"block": "5", "kind": "code", "src": """
subs = list(subprograms())

def trace(req):
    return {"implementa": [s["name"] for s in subs if req in s["reqs"] and not s["test"]],
            "verifica": [s["name"] for s in subs if req in s["reqs"] and s["test"]]}

trace("SRS-0004")
"""},
{"block": "5", "kind": "md", "src": """
<h2>Si cambio <code>Logger.Log</code>, ¿qué toco?</h2>
<p>Las llamadas entre subprogramas forman un grafo. Subiendo por él, de llamador en llamador,
salen los requisitos afectados.</p>
"""},
{"block": "5", "kind": "code", "src": """
names = {s["name"] for s in subs}
for s in subs:
    unit = s["name"].split(".")[0]
    s["calls"] = {n for n in names - {s["name"]}
                  if re.search(rf"\\b{re.escape(n)}\\s*\\(", s["body"])
                  or (n.startswith(unit + ".") and
                      re.search(rf"(?<![.\\w]){n.split('.')[-1]}\\s*\\(", s["body"]))}

def impact(name):
    seen, todo = set(), [name]
    while todo:
        n = todo.pop()
        todo += [s["name"] for s in subs if n in s["calls"] and s["name"] not in seen]
        seen |= {s["name"] for s in subs if n in s["calls"]}
    return sorted(seen), sorted({r for s in subs if s["name"] in seen | {name} for r in s["reqs"]})
"""},
{"block": "5", "kind": "code", "src": """
callers, reqs = impact("Logger.Log")
print("llamadores:", ", ".join(callers))
print("requisitos:", ", ".join(reqs))
graph(subs, "Logger.Log")
"""},
{"block": "5", "kind": "md", "src": """
<h2>Huecos</h2>
"""},
{"block": "5", "kind": "code", "src": """
done = {r for s in subs if not s["test"] for r in s["reqs"]}
tested = {r for s in subs if s["test"] for r in s["reqs"]}
table([{"requisito": r["id"], "código": "sí" if r["id"] in done else "—",
        "prueba": "sí" if r["id"] in tested else "—", "verificación": r["verification"]}
       for r in data.requirements() if r["id"] not in done or r["id"] not in tested])
"""},
{"block": "5", "kind": "md", "src": """
<p>Sin modelo, sin errores y al instante. <b>Determinista primero</b>; el modelo, para lo que
sabe hacer: leer, resumir, redactar. Por ejemplo, sacar las cifras de una sección del manual
en un formato fijo:</p>
"""},
{"block": "5", "kind": "code", "src": """
schema = {"type": "object", "additionalProperties": False, "required": ["cifras"],
          "properties": {"cifras": {"type": "array", "items": {
              "type": "object", "additionalProperties": False, "required": ["dato", "valor"],
              "properties": {"dato": {"type": "string"}, "valor": {"type": "string"}}}}}}
section = data.documents()["manual_operador.md"].split("## 3")[1].split("## 6")[0]
r = llm.chat(f"Saca las cifras que debe cumplir el sistema:\\n{section}",
             response_format={"type": "json_schema",
                              "json_schema": {"name": "cifras", "schema": schema, "strict": True}})
print(json.dumps(json.loads(r.choices[0].message.content), indent=2, ensure_ascii=False))
"""},
# ---------------------------------------------------------------- 6 Agentes
{"block": "6", "kind": "md", "src": """
<h2>Darle herramientas</h2>
<p>Un agente es un bucle: el modelo pide una herramienta, la ejecutamos, le damos el
resultado, y así hasta que responde. Las herramientas son lo que ya hemos construido.</p>
"""},
{"block": "6", "kind": "code", "src": """
TOOLS = {
    "search": lambda query: [f"{chunks[i]['doc']} › {chunks[i]['title']}:\\n{chunks[i]['text']}"
                             for i in hybrid(query, 3)],
    "get_requirement": lambda id: next(r["text"] for r in data.requirements() if r["id"] == id),
    "read_file": lambda path: data.ada_sources().get(path, f"no existe; hay: {list(data.ada_sources())}"),
    "trace": lambda id: trace(id),
}
SCHEMAS = [tool("search", "Busca en requisitos y documentos", query="qué buscar"),
           tool("get_requirement", "Texto oficial de un requisito", id="p. ej. SRS-0004"),
           tool("read_file", "Lee un fichero Ada", path="p. ej. src/tms_main.adb"),
           tool("trace", "Código y pruebas de un requisito", id="p. ej. SRS-0004")]
"""},
{"block": "6", "kind": "code", "src": """
def agent(task, max_steps=10):
    messages = [{"role": "system", "content": "Revisas código Ada. Usa las herramientas; no supongas."},
                {"role": "user", "content": task}]
    for _ in range(max_steps):
        message = llm.chat(messages, tools=SCHEMAS).choices[0].message
        messages.append(message)
        if not message.tool_calls:
            return message.content
        for call in message.tool_calls:
            args = json.loads(call.function.arguments)
            result = TOOLS[call.function.name](**args)
            step(call.function.name, args, result)
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": json.dumps(result, ensure_ascii=False)})
    return "(se acabaron los pasos)"
"""},
{"block": "6", "kind": "chat", "src": "La prueba de SRS-0004 pasa. ¿Cumple el código el requisito?"},
{"block": "6", "kind": "code", "src": """
print(agent("¿Cumple el código el requisito SRS-0004 en todos los casos?"))
limits.add("Un agente gasta muchas peticiones por tarea, y el cupo es de 28 por minuto",
           "nuestra infraestructura")
"""},
{"block": "6", "kind": "md", "src": """
<p>Se acercó: dice que cumplir los 2 s depende de cómo llame el bucle principal a la purga.
Pero no fue a mirarlo. El fallo está en <code>tms_main.adb</code>: solo purga cuando llega un
informe, y si el sensor se calla, ninguna traza se borra. La prueba de SRS-0004 pasa. Y
empieza diciendo «no cumple» para acabar diciendo «es funcionalmente correcto».</p>
"""},
{"block": "6", "kind": "code", "src": """
limits.add("No comprueba lo que sospecha, y se contradice", "nuestros modelos")
"""},
{"block": "6", "kind": "md", "src": """
<h2>Lo que pasó cuando escribió un servidor en Ada</h2>
<p>25 requisitos, 544 líneas, 10 pruebas. Encargo a encargo y con una persona al lado, salió
entero. Sin ayuda humana, ninguna configuración llegó a un servidor que funcione.</p>
"""},
{"block": "6", "kind": "code", "src": """
limits.add("Se inventó la API de GNAT.Sockets", "nuestros modelos")
limits.add("Dijo dos veces que compilaba sin ser así", "nuestros modelos")
limits.add("Con encargos amplios entra en bucles", "nuestros modelos")
limits.add("Al pedirle arreglar una prueba que falla, cambia la prueba", "nuestros modelos")
limits.add("No tiene acceso a nuestro código, requisitos ni documentos", "nuestra infraestructura")
"""},
# ---------------------------------------------------------------- 7 Límites
{"block": "7", "kind": "md", "src": """
<h2>La lista de límites</h2>
"""},
{"block": "7", "kind": "code", "src": """
limits.show()
"""},
{"block": "7", "kind": "md", "src": """
<h2>Hacia dónde ir</h2>
<ol>
<li><b>Integración primero.</b> Conectar la IA a nuestros documentos, requisitos y código, y
llevarla al editor. Con los modelos actuales ya rinde: con fuentes, aciertan.</li>
<li><b>Capacidad.</b> Con 28 peticiones por minuto para todos, un equipo no puede usar
agentes. Cupos por persona.</li>
<li><b>Mejores modelos para programar.</b> Depende de una pregunta: ¿puede salir nuestro código
de la empresa? Si sí, con contrato, modelos punteros. Si no, modelos abiertos más grandes en
hardware propio. En los dos casos, decidirlo con tareas nuestras en Ada.</li>
</ol>
"""},
{"block": "7", "kind": "traffic", "src": ""},
{"block": "7", "kind": "md", "src": """
<h2>Lo que hemos construido</h2>
"""},
{"block": "7", "kind": "diagram", "src": ""},
]
