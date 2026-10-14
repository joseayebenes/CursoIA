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
| `curso-ia.ipynb` | el notebook de la sesión |
| `docs/guion.md` | el guion de la sesión, bloque a bloque: **empieza por aquí** |
| `docs/decisiones.md` | qué se decidió y por qué |
| `docs/modelos.md` | gemma-4, gpt-oss-120b y devstral: lo que son y lo medido |
| `docs/limitaciones.md` | el bloque final: limitaciones, hacia dónde ir, el semáforo |
| `datos/` | el proyecto inventado y sus trampas (ver `datos/README.md`) |
| `curso/` | ayudas del notebook: el cliente del modelo con caché (`llm`), los datos (`data`) y las tablas, figuras y la lista de límites (`show`) |
| `scripts/check_gateway.py` | qué admite cada modelo del servidor |
| `scripts/run_notebook.py` | ejecuta el notebook entero y guarda sus salidas |
| `resultados/` | lo que sale de `check_gateway.py` |
| `cache/` | las respuestas guardadas de los modelos (se crea al usarlo) |

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

Por defecto: modelo `gemma-4`, embeddings `embeddinggemma` y 28 peticiones por minuto como
mucho. Todas las variables están al principio de `curso/llm.py`.

### La red de la empresa: proxy y certificados

La API de la empresa solo se alcanza a través del proxy corporativo y confiando en su
certificado raíz, porque el proxy inspecciona TLS:

| Variable | Para qué | Por defecto |
|---|---|---|
| `CURSO_PROXY` | el proxy, con usuario y contraseña si los pide: `http://usuario:contraseña@proxy:8080` | `HTTPS_PROXY` o `HTTP_PROXY` |
| `CURSO_NO_PROXY` | hosts que van directos, separados por comas (un gateway interno puede no necesitar el proxy) | `NO_PROXY`, o `localhost` |
| `CURSO_CA_CERT` | `system`: el almacén de certificados de Windows o macOS, donde ya está la raíz corporativa; o la ruta de un PEM (o carpeta) con la CA corporativa, que se añade a las habituales | `system` (o `SSL_CERT_FILE`) |
| `CURSO_CLIENT_CERT`, `CURSO_CLIENT_KEY`, `CURSO_CLIENT_KEY_PASSWORD` | certificado de cliente, si el servidor lo pide (TLS mutuo) | ninguno |
| `CURSO_MAX_WAIT` | segundos esperando mientras el servidor rechaza por el cupo (409 o 429) | 900 |

Lo primero en un equipo nuevo:

```bash
python -m curso.llm
```

Enseña la configuración efectiva (con la clave y las contraseñas enmascaradas) y hace una
petición real al chat y otra a los embeddings. Si algo falla, dice qué cambiar: el
certificado no es de confianza (falta la CA corporativa), el proxy pide credenciales (407),
el servidor pide certificado de cliente, la clave no vale, la URL no acaba en `/v1`, o no
conecta (quizá el gateway va sin proxy: `CURSO_NO_PROXY`).

Cuando el servidor rechaza por el cupo (409 o 429), se espera lo que diga (`Retry-After`) o
cada vez más, hasta `CURSO_MAX_WAIT`; esas esperas no cuentan como reintentos. Los 5xx y los
cortes se reintentan 5 veces; los errores de certificado o de credenciales del proxy, no.

Para desarrollar sin gastar cupo del gateway, el perfil `openrouter` usa el mismo gemma-4
26b en OpenRouter (y `baai/bge-m3` para los embeddings):

```bash
export CURSO_PROFILE=openrouter
export OPENROUTER_API_KEY="<clave de OpenRouter>"
```

Con OpenRouter, solo los datos inventados de `datos/`: es un servicio externo.

## El notebook

`curso-ia.ipynb`, en la raíz del repositorio para que encuentre `curso/`. Se abre con VS Code
(extensión de Jupyter, eligiendo el Python de `.venv`) o con JupyterLab, si está instalado.

Para ejecutarlo entero desde la terminal y guardar las salidas, como «Run All» y «Save»:

```bash
python scripts/run_notebook.py
```

A diferencia de «Run All», no se para en un error: ejecuta todas las celdas y al final dice
cuáles fallaron. Las salidas que tiene ahora son de OpenRouter; el día antes de la sesión se
sustituyen por las del gateway (`docs/guion.md`, «Antes de la sesión»).

## Qué admite cada modelo

```bash
python scripts/check_gateway.py
```

Antes, la configuración efectiva (como `python -m curso.llm`). Prueba los modelos de
`CURSO_MODELS` (por defecto, los tres del perfil: los mismos que compara el notebook). Unas 25
peticiones (un minuto con el cupo de 28). Deja el resultado en
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
