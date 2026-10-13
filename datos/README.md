# Datos: el proyecto inventado

Un sistema pequeño pero creíble para las demos: el software de gestión de trazas (TMS) de
un sistema de vigilancia costera, con sus requisitos, su diseño, su manual y su código Ada.
Todo es inventado, así que se puede mandar a cualquier modelo.

| Fichero | Qué es | Idioma |
|---|---|---|
| `requisitos.csv` | 16 requisitos del módulo `SRS_TMS`, como saldrían de DOORS: id, módulo, encabezado, texto, método de verificación | inglés |
| `documentos/tms_sdd.md` | el documento de diseño (SDD), edición 3: arquitectura, ciclo de vida de las trazas, alarmas, rendimiento y puntos abiertos | inglés |
| `documentos/manual_operador.md` | el manual del operador, edición 1 (escrito con la edición 2 del diseño) | español |
| `ada/src/` | 8 paquetes y el programa principal, unas 400 líneas | Ada 2012 |
| `ada/tests/` | dos programas de prueba | Ada 2012 |
| `ada/tms.gpr` | el proyecto de GNAT | |

## Convención de trazabilidad en el código

- `--  Req: SRS-0004` en la línea anterior a un subprograma: el subprograma implementa ese
  requisito (o esos, separados por comas).
- El mismo comentario en un procedimiento de `tests/`: la prueba verifica el requisito.

Con eso, y con los `with` y las llamadas entre paquetes, se construye el grafo del bloque 5
del guion sin preguntar nada al modelo.

## Las trampas

Cada una está pensada para que una técnica falle a la vista en un momento concreto del
guion (ver `docs/guion.md`).

| Trampa | Dónde | Qué enseña |
|---|---|---|
| **La pregunta en español y el diseño en inglés.** "¿Cuánto tarda en borrarse una traza?" frente a "stale track", "purge cycle", "removal from the display" | `tms_sdd.md` 4.4 | BM25 no encuentra nada en el diseño; los embeddings multilingües sí |
| **Dos cifras.** El requisito y el diseño dicen 2 s; el manual dice "como mucho 3 segundos" (se escribió con la edición 2, que purgaba cada 2 s) | `requisitos.csv` SRS-0004, `manual_operador.md` 3 | una respuesta con fuentes enseña las dos y cita de dónde sale cada una; sin fuentes, el modelo elige una |
| **IDs parecidos.** SRS-0004, SRS-0044 (también de borrado) y SRS-0040 | `requisitos.csv` | buscar "SRS-0004" por similitud puede traer SRS-0044; la búsqueda exacta no se equivoca. **Hay que comprobarlo en el gateway** con `embeddinggemma` |
| **Requisitos casi iguales.** SRS-0004 y SRS-0006 son los dos "delete a track within 2 s" | `requisitos.csv` | la similitud no distingue bien por qué se borra |
| **Un requisito que el manual contradice.** SRS-0012 pide recuperar las trazas tras un reinicio; el diseño lo deja abierto (OI-2) y el manual dice que la pantalla aparece vacía | `requisitos.csv`, `tms_sdd.md` 9, `manual_operador.md` 7 | verificar un requisito contra los documentos |
| **Una pregunta sin respuesta.** "¿Qué cifrado usan los mensajes al HMI?" | ninguna parte | con fuentes, el modelo debería decir que no lo sabe |
| **Huecos de trazabilidad.** SRS-0002, SRS-0012 y SRS-0042 no tienen código; SRS-0001, 0003, 0005, 0008, 0009, 0040, 0041 y 0044 tienen código pero no prueba | código | el grafo los encuentra sin modelo |

## Los dos fallos sembrados en el código

Para las demos de revisión de código y de agentes. **No están en ningún comentario**: hay que
descubrirlos.

1. **La purga solo corre cuando llega un informe** (`tms_main.adb`). El diseño (4.4) dice
   que la purga se hace una vez por segundo "independently of the arrival of reports",
   pero el bucle principal se bloquea en `Sensor_Input.Read` y solo purga después de un
   informe. Si el sensor deja de mandar informes (por ejemplo, porque ya no detecta ningún
   blanco), ninguna traza se borra: no se cumple SRS-0004. La prueba de SRS-0004
   (`test_track_store.adb`) pasa, porque prueba `Purge_Stale` por separado. **La prueba
   pasa y el requisito no se cumple.**
2. **Las alarmas no se enteran de que un identificador se reutiliza** (`alarms.adb`).
   `Alarms` guarda si cada identificador estaba dentro de una zona. Si una traza dentro de
   una zona se borra y un blanco nuevo recibe el mismo identificador (el diseño, sección 3,
   dice que se reutilizan) y ya está dentro de una zona, no salta la alarma: no se cumple
   SRS-0007.

## Compilar y probar

Con GNAT y gprbuild en el `PATH`:

```bash
cd datos/ada
gprbuild -P tms.gpr
./bin/test_track_store
./bin/test_alarms
printf '1 100 200\n2 1500 0\n' | ./bin/tms_main
```

Compila sin avisos con `-gnatwa` y el estilo de `tms.gpr` (comprobado con GNAT 16.1).
