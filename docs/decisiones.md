# Decisiones

Lo que se decidió al preparar el curso y por qué, para no volver a discutirlo.

| Decisión | Por qué |
|---|---|
| **Una sola sesión de 2 horas, online** | Es el formato disponible. Obliga a una pregunta por bloque y a un ritmo con cambios cada 10-15 minutos. |
| **Un notebook como hilo, con los gráficos dentro** | La audiencia son desarrolladores. Online, cambiar de ventana entre diapositivas y código hace que la gente se pierda. |
| **Construir en directo, no explicar conceptos sueltos** | Cada concepto aparece cuando hace falta para resolver un problema del asistente que se construye. Al final, el diagrama de lo construido es la arquitectura de un sistema real. |
| **Todo en Ada** | El equipo desarrolla en Ada. El proyecto inventado tiene requisitos, diseño, manual y código Ada con trazabilidad, como los proyectos de verdad. |
| **El proyecto inventado tiene trampas** | Cada técnica tiene que fallar a la vista en el momento justo del guion. Ver `datos/README.md`. |
| **La API corporativa, nada de Ollama** | Es la IA que tienen de verdad; el curso trata de qué puede hacer *esa*. |
| **OpenRouter con gemma-4 26b para desarrollar** | El mismo modelo que el gateway, sin cupo corporativo. No tiene `embeddinggemma`: en desarrollo se usa `baai/bge-m3`, también multilingüe. |
| **Caché de todas las llamadas** | El cupo de 28 peticiones por minuto, la reproducibilidad (lo mismo que se ensayó) y que la sesión no dependa del gateway. La caché del gateway se versiona; la de OpenRouter, no. |
| **Se enseña el JSON** | Es lenguaje neutro: lo lee un desarrollador Ada sin saber Python. |
| **Pregunta al chat antes de ejecutar** | Es la forma de mantener dentro a una audiencia online con la cámara apagada. |
| **Una lista de límites que crece durante la sesión** | Al final se clasifica en tres columnas, y la clasificación ya es la hoja de ruta. |
| **Honestidad sobre Ada y sobre los fallos** | Un equipo Ada desconfiado se cree más a quien le enseña los fallos. El experimento del servidor de sockets es el mejor material. |
| **Dependencias mínimas** | Los puestos son Windows y quizá sin acceso a pip. `openai`, `truststore`, `numpy` e `ipykernel`. BM25 con FTS5 de `sqlite3`, PCA con `numpy`, figuras en SVG. |
| **Figuras en HTML y SVG, sin matplotlib** | `curso/show.py` las dibuja: siguen el tema del editor (claro u oscuro), el mapa de embeddings dice qué es cada punto al pasar el ratón, se exportan a HTML con el notebook y no añaden ninguna dependencia. |
| **El bloque 2 compara sin contexto y con contexto** | Con la sección 3 del diseño delante, los tres modelos encuentran el fallo de `alarms.adb`; sin ella, ninguno. Enseña más que «cuál es mejor»: lo que decide es lo que tiene delante. |
| **El agente, dos veces** | Sin razonamiento, se acerca y no lo comprueba; con razonamiento `low` y temperatura 1,0, encuentra el fallo de `tms_main.adb` a cambio de 11 peticiones. Las dos cosas son verdad y las dos importan. |
| **MCP con un diagrama** | Un servidor de verdad sería otra dependencia y no añade nada que no se vea ya en el bucle del agente. |
| **El notebook ejecutado se versiona** | Sus salidas se revisan como el código. Hasta la ejecución con el gateway, son las de OpenRouter. |
| **La red de la empresa, como en las demás herramientas** | La API solo se alcanza con el proxy (con credenciales y `NO_PROXY`) y la CA corporativa, a veces con certificado de cliente, y rechaza con 409 o 429 al pasar el cupo. `curso/llm.py` cubre todo eso y dice qué cambiar cuando falla. |
| **Sin `VERIFY_X509_STRICT` con una CA en PEM** | Python 3.13 rechaza los certificados sin Authority Key Identifier, como los que emiten algunos proxies que inspeccionan TLS. Se siguen verificando la cadena y el nombre del servidor, como hacen `curl` y el almacén del sistema. |
| **Secretos solo por entorno** | El notebook se comparte después; la clave no puede acabar en él. |
| **El notebook se comparte después, no antes** | Así nadie se pelea con la instalación durante la sesión. |
| **Código en inglés, textos en español** | Como en el resto de proyectos del equipo. |
| **No se nombra la herramienta interna que se presentará después** | El curso tiene que entenderse solo. Ver `CLAUDE.md`. |

## Pendiente

- Los nombres exactos de los modelos del gateway y lo que admite cada uno
  (`scripts/check_gateway.py`).
