# Nuestros modelos

Los tres modelos de chat del gateway corporativo, más el de embeddings. Lo que hay aquí sale
de sus fichas públicas, de `resultados/openrouter.md` (OpenRouter, 2026-10-13) y del
experimento del servidor Ada. **Lo del gateway está por comprobar** con
`scripts/check_gateway.py` (`resultados/gateway.md`).

## Resumen para la diapositiva

| | gemma-4 | gpt-oss-120b | devstral |
|---|---|---|---|
| Tamaño | 26B, ~4B activos por token (mezcla de expertos) | 117B, ~5B activos (mezcla de expertos) | según la versión del gateway |
| Razonamiento | opcional: `none` lo apaga | siempre: `low`, `medium`, `high`; `none` da error | no razona aparte: piensa en voz alta dentro de la respuesta |
| Pensado para | uso general, contexto largo (~200k en el gateway) | razonar | agentes de código |
| Por defecto en el curso | sí | | |

**Mezcla de expertos:** el modelo tiene muchos parámetros pero solo usa una parte en cada
token. Los parámetros totales guardan conocimiento (cuánto Ada ha "visto"); los activos
marcan el coste de cálculo de cada token. gpt-oss-120b tiene cuatro veces más parámetros que
gemma-4 con un coste por token parecido.

## Lo comprobado en OpenRouter

| | gemma-4-26b | gpt-oss-120b | devstral-2512 |
|---|---|---|---|
| `logprobs` | sí | no | no |
| `n` > 1 | no | no | no |
| herramientas | sí | sí | sí |
| `json_schema` | sí | sí | sí |
| `reasoning_effort: none` | sí | **400**: el razonamiento es obligatorio | se acepta, pero lo ignora |

- **gemma-4** completa "The software shall delete a track within" con un 3 (85 %), un 1
  (8 %) y un 2 (2 %). Buen gancho: sin contexto, la cifra más probable no es la del
  requisito.
- **gpt-oss-120b** escribe "2 seconds" con espacios estrechos de Unicode (` `): quien
  compare cadenas lo tiene que saber.
- **devstral** empieza "Alright, let's tackle…": razona dentro de la respuesta aunque se le
  pida `none`.

## Lo medido con agentes (antes del curso)

**Preguntas con fuentes.** 24 preguntas de respuesta conocida sobre un proyecto de ejemplo:
gemma-4-26b, qwen3.6-35b y gemma-4-31b, 24 de 24, sin razonamiento, con una mediana de 5 a
6 s por respuesta. Para buscar y responder con fuentes, los modelos de este nivel ya bastan.

**Escribir Ada con agentes** (un servidor de comandos por sockets: 25 requisitos, 544
líneas, 10 pruebas en Ada y en Python):

- Con **gemma-4**, encargo a encargo y con una persona al lado, salió entero y las 10 pruebas
  pasan. Hizo falta:
  - razonamiento `low` y temperatura 1,0: con el razonamiento apagado entraba en bucles o
    escribía su razonamiento dentro del fichero;
  - encargos de una sola cosa: los amplios acababan en bucles o gastaban todo `max_tokens`
    razonando;
  - poner en sus instrucciones lo que no sabe: un resumen de la API de GNAT.Sockets (la
    inventaba) y reglas de Ada en las que fallaba (cadenas de longitud fija, un `with` por
    unidad, `raise ... with`, variables de entorno);
  - comprobar fuera del agente: dos veces dijo que compilaba sin ser así.
- **Sin ayuda humana**, con un protocolo automático, ninguna configuración dio un servidor
  que funcione: de las 6 ejecuciones que llegaron a las 5 pruebas de aceptación, ninguna
  pasó ni una.
- **devstral** escribe unas 8 veces más rápido que gemma-4 y sin bucles, pero no depura
  errores de ejecución, ni con la excepción y su línea.
- **Los dos modelos, al pedirles arreglar una prueba que falla, cambian la prueba**: devstral
  cambió las respuestas esperadas; gemma-4, el fin de línea a CR LF.

## Lo que falta medir

- **gpt-oss-120b escribiendo Ada.** Es la pregunta que va a salir: "¿y el de 120B?". Antes de
  la sesión, darle el mismo encargo del servidor. Si se dice "nuestros modelos no llegan",
  tiene que valer también para él.
- Todo lo de la tabla de OpenRouter, en el gateway.
- `embeddinggemma` con las trampas del bloque 3.
