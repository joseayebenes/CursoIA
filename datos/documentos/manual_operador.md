# Manual del operador del TMS

Sistema de vigilancia costera. Edición 1.

## 1 Introducción

Este manual explica cómo usar la pantalla de situación del sistema de gestión de trazas
(TMS): qué muestra, cómo se borran las trazas y qué hacer cuando aparece una alarma. Está
pensado para los operadores de la sala de control; no hace falta ningún conocimiento previo
del sistema.

## 2 La pantalla de situación

La pantalla muestra el mapa de la zona vigilada, centrado en el sensor principal. Sobre el
mapa aparecen:

- las trazas, una por cada blanco que detecta el sensor;
- las zonas restringidas, con un borde rojo: la bocana del puerto y la terminal de
  combustible;
- la lista de alarmas, a la derecha.

En la parte inferior, la barra de estado indica la hora y el número de trazas en pantalla.

## 3 Las trazas

Cada blanco que detecta el sensor aparece en pantalla como una traza: un símbolo con su
número. La posición de la traza se actualiza cada vez que el sensor vuelve a detectar el
blanco, normalmente varias veces por segundo.

Cuando el sensor deja de detectar un blanco (porque ha salido de la zona de cobertura o
porque algo lo oculta), su traza no desaparece enseguida: se queda en pantalla, inmóvil,
durante 10 segundos, por si el blanco vuelve a detectarse. Si en esos 10 segundos no llega
ninguna detección nueva, la traza desaparece sola. Desde que se cumplen esos 10 segundos,
la traza tarda como mucho 3 segundos en desaparecer de la pantalla.

Si el blanco vuelve a detectarse después, aparece como una traza nueva, que puede tener
otro número.

## 4 Borrar una traza

El operador puede borrar cualquier traza, por ejemplo una traza falsa causada por el
oleaje:

1. Seleccione la traza con el ratón.
2. Pulse la tecla SUPR.

La traza desaparece de la pantalla en menos de 2 segundos y el borrado queda anotado en el
registro de eventos.

## 5 Alarmas

Si una traza entra en una zona restringida, el sistema genera una alarma: la traza se
muestra en rojo y la alarma aparece en la lista de alarmas, con la hora y el número de la
traza. La alarma aparece en medio segundo como mucho desde que el sensor detecta al blanco
dentro de la zona.

La alarma permanece en la lista hasta que el operador la reconoce: selecciónela y pulse la
tecla F2. Reconocer una alarma no borra la traza.

## 6 Registro de eventos

El sistema anota en el registro de eventos cada traza borrada, ya sea por el operador o
porque dejó de detectarse, y cada alarma. El supervisor puede consultar el registro desde
el puesto de supervisión.

## 7 Preguntas frecuentes

**¿Cuántas trazas puede mostrar la pantalla?** Hasta 1000 a la vez.

**¿Qué pasa si se reinicia el sistema?** Tras un reinicio la pantalla aparece vacía y las
trazas se van creando de nuevo a medida que llegan las detecciones del sensor. En pocos
segundos la situación vuelve a estar completa.

**¿Se puede usar el sensor secundario?** No en esta versión.

**Una traza se ha quedado quieta en pantalla. ¿Es un fallo?** No: el sensor ha dejado de
detectar el blanco. La traza desaparecerá sola (ver la sección 3).
