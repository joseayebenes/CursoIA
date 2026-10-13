# Curso de IA para el equipo

Material de una sesión online de 2 horas para compañeros que desarrollan sobre todo en Ada.
La pregunta de la sesión: qué puede hacer por ellos la IA corporativa (gemma-4,
gpt-oss-120b, devstral), dónde no llega y hacia dónde debería ir la empresa. El presentador
prefiere gemma-4 por verlo el más capaz.

## Estado

Hecho: el guion (`docs/guion.md`), las decisiones, los modelos, las limitaciones, el
proyecto Ada inventado con sus trampas (`datos/`), las ayudas (`curso/`) y la comprobación
de modelos (`scripts/check_gateway.py`, ya ejecutada con OpenRouter).

Siguiente: **el notebook**, siguiendo `docs/guion.md` bloque a bloque. Antes, si se puede,
`check_gateway.py` contra el gateway (lo ejecuta el presentador desde la red de la empresa).

## Reglas

- **No se nombra ninguna herramienta interna** que no aparezca ya en este repositorio: el
  curso prepara el terreno para presentar una más adelante, y tiene que entenderse solo.
  Lo que hay que saber de ella está en las notas privadas (abajo), que no se versionan.
- **Toda llamada al modelo pasa por `curso.llm`** (`chat`, `ask`, `embed`): caché, límite
  de peticiones, certificados y proxy. Nada de clientes sueltos en el notebook.
- **Para desarrollar y probar, el perfil `openrouter`** (gemma-4 26b; embeddings
  `baai/bge-m3`), solo con los datos de `datos/`. La sesión usa el perfil `gateway`.
- **Secretos solo por entorno.** Nunca una clave en un fichero, en una celda ni en una
  salida.
- **Código en inglés** (nombres, comentarios, mensajes); **textos en español** (Markdown
  del notebook, documentación).
- **Dependencias mínimas** (`requirements.txt`): los puestos son Windows y quizá sin pip.
  Antes de añadir una, mirar `docs/decisiones.md`.
- **Las trampas y los fallos sembrados** de `datos/README.md` son la base de las demos: si
  se cambian los datos, comprobar que siguen funcionando y actualizar ese README.
- **El código Ada tiene que compilar sin avisos** con `datos/ada/tms.gpr`.
- **Cada salida del notebook se revisa**: si una demo no enseña lo que debe, se cambia la
  pregunta o los datos, nunca se maquilla la salida.

## Git

Gitflow: cada tarea en `feature/<nombre>` desde `develop`, un commit por parte lógica,
mensajes en español al estilo de commits convencionales (`feat(curso): …`, `docs: …`) y
`git merge --no-ff` en `develop` al terminar, sin PR. Push solo si se pide.

@privado/contexto.md
