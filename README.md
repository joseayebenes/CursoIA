# Curso de IA para el equipo

Material de una sesión online de 2 horas para un equipo que desarrolla sobre todo en Ada:
**qué puede hacer por nosotros la IA de la empresa, dónde no llega y qué haría falta.**

En la sesión se construye en directo, en un notebook, un asistente sobre un proyecto
inventado (requisitos, diseño, manual y código Ada): tokens, embeddings, búsqueda,
respuestas con fuentes, trazabilidad y agentes, cada cosa cuando hace falta. Todas las
demos usan la API corporativa.

## Qué hay

| Carpeta | Qué tiene |
|---|---|
| `docs/guion.md` | el guion de la sesión, bloque a bloque: **empieza por aquí** |
| `docs/decisiones.md` | qué se decidió y por qué |
| `docs/modelos.md` | gemma-4, gpt-oss-120b y devstral: lo que son y lo medido |
| `docs/limitaciones.md` | el bloque final: limitaciones, hacia dónde ir, el semáforo |
| `datos/` | el proyecto inventado y sus trampas (ver `datos/README.md`) |
| `curso/` | ayudas del notebook: el cliente del modelo con caché (`llm`) y los datos (`data`) |
| `scripts/check_gateway.py` | qué admite cada modelo del servidor |
| `resultados/` | lo que sale de `check_gateway.py` |
| `cache/` | las respuestas guardadas de los modelos (se crea al usarlo) |

El notebook está por hacer.

## Preparar el entorno

Python 3.10 o posterior.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

En un puesto Windows sin acceso a pip, se descargan los paquetes en otro equipo y se
instalan desde la carpeta:

```bash
pip download -r requirements.txt -d wheels --platform win_amd64 --python-version 3.12 --only-binary=:all:
pip install --no-index --find-links wheels -r requirements.txt
```

## Acceso al modelo

Solo por variables de entorno: la clave nunca va en un fichero ni en el notebook.

```bash
export CURSO_BASE_URL="https://<gateway>/v1"
export CURSO_API_KEY="<clave>"
```

En Windows, `setx CURSO_BASE_URL "https://<gateway>/v1"` (y abrir otra terminal).

Por defecto: modelo `gemma-4`, embeddings `embeddinggemma`, 28 peticiones por minuto como
mucho, los certificados del sistema (donde está la raíz corporativa) y el proxy de
`HTTPS_PROXY`. Todas las variables están al principio de `curso/llm.py`.

Para desarrollar sin gastar cupo del gateway, el perfil `openrouter` usa el mismo gemma-4
26b en OpenRouter (y `baai/bge-m3` para los embeddings):

```bash
export CURSO_PROFILE=openrouter
export OPENROUTER_API_KEY="<clave de OpenRouter>"
```

Con OpenRouter, solo los datos inventados de `datos/`: es un servicio externo.

## Qué admite cada modelo

```bash
python scripts/check_gateway.py
```

Unas 25 peticiones (un minuto con el cupo de 28). Deja el resultado en
`resultados/<perfil>.md`. El de OpenRouter ya está en `resultados/openrouter.md`; el del
gateway hay que sacarlo desde la red de la empresa.

## La caché

Cada llamada de `curso.llm` se guarda en `cache/<perfil>/`. La segunda vez sale de ahí, al
instante y sin gastar cupo. Por eso el notebook se ejecuta entero contra el gateway el día
antes, y en la sesión todo sale de la caché.

- `CURSO_CACHE=refresh` vuelve a llamar y sobrescribe.
- `CURSO_CACHE=off` no la usa.

La caché del gateway se versiona, para que el notebook se pueda ejecutar después sin
acceso al gateway. La de OpenRouter, no.
