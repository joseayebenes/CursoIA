# Limitaciones y hacia dónde ir

El contenido del bloque 7. Es la parte de la sesión que puede acabar llegando a quien decide,
así que el tono importa: **"con lo que tenemos ya podemos X; para Y hace falta Z"**, con datos.
Convence más que una queja.

## Las tres columnas

Durante la sesión, cada fallo se apunta en la lista de límites. Al final se clasifica así:

| Tipo | Lo que habrán visto | Qué lo arregla |
|---|---|---|
| **De cualquier modelo** | Inventa lo que no sabe (gancho, bloque 1). No recuerda nada entre peticiones. No conoce nuestros documentos. No sabe quién llama a qué. Si la búsqueda no trae el fragmento, falla. | **Software, no un modelo mejor:** darle las fuentes, un grafo del código y los requisitos, herramientas; compilar y probar fuera del modelo. |
| **De nuestros modelos** | Se inventa la API de GNAT.Sockets. Dice que compila sin haber compilado. Entra en bucles con encargos amplios. No depura errores de ejecución. Cambia la prueba en vez del código. | **Modelos más capaces** para programar. |
| **De nuestra infraestructura** | 28 peticiones por minuto, y un agente gasta decenas por tarea. No tiene acceso a nuestro código, requisitos ni documentos. No está en el editor. | **Capacidad, acceso a las fuentes e integración.** |

La primera columna es la más importante: **un modelo mejor no la arregla.** Hace falta
montarlo bien, y eso se puede hacer ya.

## Lo que dicen las medidas

Los detalles están en `modelos.md`.

- **Para conocimiento y trazabilidad, los modelos actuales ya valen.** Preguntas con
  fuentes: 24 de 24. Lo que falta es conectarlos a lo nuestro.
- **Para programar con agentes, falta modelo.** Con encargos pequeños y una persona al lado,
  gemma-4 escribió un servidor Ada de 544 líneas con 10 pruebas que pasan. Sin ayuda humana,
  ninguna configuración llegó a un servidor que funcione. devstral es rápido pero no depura.

## Hacia dónde ir

1. **Integración primero.** Es barato y se puede hacer ya: conectar la IA a nuestros
   documentos, requisitos y código (búsqueda con fuentes, trazabilidad, herramientas) y
   llevarla al editor. Con los modelos actuales ya rinde.
2. **Capacidad.** Si el cupo de 28 peticiones por minuto es para todos, no da para que un
   equipo use agentes. Hacen falta cupos por persona. (Comprobar si el cupo es por clave o
   compartido.)
3. **Mejores modelos para programar.** La decisión depende de una pregunta: **¿puede salir
   nuestro código de la empresa?**
   - **Sí, con contrato:** modelos punteros, con garantías de que los datos no se retienen
     ni se usan para entrenar.
   - **No:** modelos abiertos más grandes, en hardware propio.

   En los dos casos, decidirlo con tareas nuestras en Ada (como el servidor de sockets), no
   con benchmarks de Python.

## El semáforo

La respuesta directa a "¿en qué nos ayuda, entonces?":

- **Verde, útil ya:** explicar código ajeno; buscar y preguntar a la documentación con
  citas; resumir; redactar.
- **Ámbar, con revisión:** escribir pruebas y código pequeño, un encargo de una sola cosa
  cada vez; comprobar un requisito contra un documento; revisar un cambio.
- **Rojo, nunca solo:** fiarse de "compila" o "pasa" sin haberlo ejecutado; dejarle arreglar
  la prueba que falla; encargos grandes sin supervisión.
