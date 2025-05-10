# Demo del Patrón Circuit Breaker con Flask y Docker Compose

Este proyecto demuestra la implementación del patrón de diseño Circuit Breaker. Utiliza dos microservicios desarrollados con Flask y Python, orquestados mediante Docker Compose.

* **`service-a`**: Actúa como el cliente. Implementa el Circuit Breaker para proteger las llamadas que realiza a `service-b`.
* **`service-b`**: Actúa como el servicio dependiente, el cual puede ser configurado para simular fallos o latencia, permitiendo observar el comportamiento del Circuit Breaker.

La librería utilizada para el Circuit Breaker en `service-a` es `circuitbreaker==1.4.0`.

## ¿Qué es el Patrón Circuit Breaker?

El patrón Circuit Breaker es una técnica utilizada en el desarrollo de software para mejorar la estabilidad y resiliencia de sistemas que dependen de servicios remotos. Funciona de manera similar a un interruptor eléctrico:

1.  **Cerrado (Closed)**: En estado normal, las solicitudes fluyen del cliente al servicio dependiente. El Circuit Breaker monitorea las fallas.
2.  **Abierto (Open)**: Si el número de fallas excede un umbral predefinido, el circuito se "abre". Durante este estado, todas las solicitudes al servicio dependiente fallan inmediatamente, sin intentar la operación real. Esto evita sobrecargar un servicio que ya está fallando y permite que se recupere.
3.  **Semi-Abierto (Half-Open)**: Después de un período de tiempo (timeout), el circuito pasa a un estado "semi-abierto". En este estado, se permite que un número limitado de solicitudes de prueba lleguen al servicio dependiente.
    * Si estas pruebas tienen éxito, se considera que el servicio se ha recuperado, y el circuito vuelve al estado "cerrado".
    * Si las pruebas fallan, el circuito vuelve al estado "abierto", y el ciclo de espera comienza de nuevo.

Este patrón ayuda a prevenir fallas en cascada y a manejar los errores de forma más elegante.

## Estructura del Proyecto
