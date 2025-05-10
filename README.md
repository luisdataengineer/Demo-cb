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
/Demo-cb
|
|-- service-a/
|   |-- app.py             # Cliente Flask con Circuit Breaker
|   |-- requirements.txt   # Dependencias de Service A
|   -- Dockerfile # Dockerfile para Service A | |-- service-b/ | |-- app_b.py # Servicio Flask dependiente (simula fallos/latencia) | |-- requirements_b.txt # Dependencias de Service B |-- Dockerfile         # Dockerfile para Service B
|
|-- docker-compose.yml     # Orquesta los servicios
`-- README.md              # Este archivo

## Servicios

### `service-a` (Cliente con Circuit Breaker)

* **Expuesto en**: `http://localhost:5000`
* **Funcionalidad**:
    * Realiza llamadas al endpoint `/data` de `service-b`.
    * Implementa un Circuit Breaker para estas llamadas.
    * Proporciona una interfaz web simple para:
        * Iniciar una llamada a `service-b` (protegida por el Circuit Breaker).
        * Botones para controlar el comportamiento simulado de `service-b`.
    * (Opcional) Un endpoint `/circuit-status` (accesible directamente en `http://localhost:5000/circuit-status`) muestra el estado actual y las métricas del Circuit Breaker.
* **Configuración del Circuit Breaker** (a través de variables de entorno en `docker-compose.yml`, que se mapean a los parámetros de la librería `circuitbreaker`):
    * `CIRCUIT_FAIL_MAX` (usado como `failure_threshold` en el código): Número de fallos para abrir el circuito (por defecto: 3).
    * `CIRCUIT_RESET_TIMEOUT` (usado como `recovery_timeout` en el código): Segundos que el circuito permanece abierto antes de pasar a semi-abierto (por defecto: 20).

### `service-b` (Servicio Dependiente)

* **Expuesto en**: `http://localhost:5001` (principalmente para ser controlado por los botones en la UI de `service-a`).
* **Funcionalidad**:
    * Endpoint `/data`: Devuelve datos simulados o un error, según su estado actual.
    * Endpoint `/health`: Usado por Docker Compose para verificar la salud del servicio.
    * Endpoints de control (accesibles vía POST, por ejemplo, a través de los botones en `service-a`):
        * `/induce-failure`: Hace que el endpoint `/data` comience a devolver errores HTTP 500.
        * `/remove-failure`: Restaura el endpoint `/data` a su funcionamiento normal.
        * `/induce-latency`: Introduce una latencia aleatoria (2-5 segundos) en las respuestas de `/data`.
        * `/remove-latency`: Elimina la latencia adicional.

## Prerrequisitos

* [Docker](https://www.docker.com/get-started)
* [Docker Compose](https://docs.docker.com/compose/install/) (generalmente viene con Docker Desktop)

## Cómo Ejecutar la Demo

1.  **Clona el repositorio:**
    ```bash
    git clone [https://github.com/luisdataengineer/Demo-cb.git](https://github.com/luisdataengineer/Demo-cb.git)
    cd Demo-cb
    ```

2.  **Construye las imágenes y levanta los servicios:**
    Desde la raíz del proyecto (donde se encuentra el archivo `docker-compose.yml`), ejecuta:
    ```bash
    docker-compose up --build
    ```
    La opción `--build` es importante la primera vez o si realizas cambios en el código o los Dockerfiles. Para inicios subsecuentes, `docker-compose up` puede ser suficiente.

3.  **Accede a la Interfaz de la Demo:**
    Abre tu navegador web y ve a:
    `http://localhost:5000`

    Verás la página principal de `service-a`.

4.  **Experimenta con el Circuit Breaker:**
    * **Funcionamiento Normal**: Haz clic en el enlace "Call Service B (via Circuit Breaker)". Deberías ver una respuesta JSON exitosa de `service-b`, y el estado del circuito (mostrado en el JSON devuelto por `service-a`) será algo como `CircuitBreakerState.CLOSED` (o simplemente `closed` si la librería lo convierte a string así).
    * **Inducir Fallos**: Usa el botón "Make Service B Fail". Esto hará que `service-b` comience a devolver errores.
    * **Observar Apertura del Circuito**: Vuelve a hacer clic en "Call Service B (via Circuit Breaker)" varias veces (según el `FAILURE_THRESHOLD`, por defecto 3).
        * Las primeras llamadas fallidas serán registradas por el Circuit Breaker.
        * Una vez que se alcance el umbral, el circuito se abrirá. Las llamadas subsiguientes fallarán inmediatamente (devueltas por `service-a` sin contactar a `service-b`), y el estado del circuito será `CircuitBreakerState.OPEN`. Los logs en la terminal también reflejarán esto.
    * **Recuperación y Estado Semi-Abierto**: Haz clic en "Make Service B Healthy". Espera el `RECOVERY_TIMEOUT` (por defecto 20 segundos). Durante este tiempo, el circuito permanecerá abierto.
    * **Cierre del Circuito**: Después del timeout, el circuito pasará a `CircuitBreakerState.HALF_OPEN`. La *siguiente* llamada a "Call Service B (via Circuit Breaker)" será una llamada de prueba.
        * Si esta llamada de prueba tiene éxito (porque `service-b` ya está saludable), el circuito se cerrará (`CircuitBreakerState.CLOSED`).
        * Si la llamada de prueba falla, el circuito volverá a `CircuitBreakerState.OPEN`.
    * **Probar Latencia**: Puedes usar los botones "Make Service B Slow" y "Make Service B Fast" para ver cómo la latencia (si excede el timeout de la petición en `service-a`) también puede ser tratada como una falla por el Circuit Breaker.

5.  **Verificar Estado Detallado (Opcional):**
    Puedes acceder directamente a `http://localhost:5000/circuit-status` en tu navegador para ver un JSON con el estado actual y las métricas del Circuit Breaker en `service-a`.

6.  **Detener la Aplicación:**
    En la terminal donde ejecutaste `docker-compose up`, presiona `Ctrl + C`.
    Para detener y eliminar los contenedores, redes y volúmenes (si los hubiera), ejecuta:
    ```bash
    docker-compose down
    ```

## Archivos de Configuración Clave

* **`service-a/app.py`**: Lógica del cliente e implementación del Circuit Breaker.
* **`service-a/requirements.txt`**: Incluye `circuitbreaker==1.4.0`.
* **`service-b/app_b.py`**: Lógica del servicio dependiente simulado.
* **`docker-compose.yml`**: Orquestación de los servicios, definición de puertos, variables de entorno para el Circuit Breaker, y healthchecks.
