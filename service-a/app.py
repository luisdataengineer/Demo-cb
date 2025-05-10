from flask import Flask, jsonify
import requests
from circuitbreaker import CircuitBreaker, CircuitBreakerError # Asegúrate que esta es la importación correcta para la v1.4.0
import os

app = Flask(__name__)

# Configuración del Circuit Breaker
# Estas variables podrían venir de variables de entorno para mayor flexibilidad
# Usamos los nombres de parámetros correctos para la librería circuitbreaker v1.4.0:
# failure_threshold en lugar de fail_max
# recovery_timeout en lugar de reset_timeout
CIRCUIT_FAILURE_THRESHOLD = int(os.environ.get('CIRCUIT_FAILURE_THRESHOLD', 3))
CIRCUIT_RECOVERY_TIMEOUT = int(os.environ.get('CIRCUIT_RECOVERY_TIMEOUT', 20)) # Segundos

service_b_cb = CircuitBreaker(
    failure_threshold=CIRCUIT_FAILURE_THRESHOLD, # Nombre de parámetro corregido
    recovery_timeout=CIRCUIT_RECOVERY_TIMEOUT,   # Nombre de parámetro corregido
    name='ServiceB_CB' # Nombre opcional para el circuit breaker
)

@app.route('/')
def index():
    # Podrías mostrar el estado del circuit breaker aquí o un menú de opciones
    return f"""
    <h1>Service A - Circuit Breaker Demo</h1>
    <p>Circuit Breaker for Service B: FAILURE_THRESHOLD={CIRCUIT_FAILURE_THRESHOLD}, RECOVERY_TIMEOUT={CIRCUIT_RECOVERY_TIMEOUT}s</p>
    <ul>
        <li><a href="/call-service-b">Call Service B (via Circuit Breaker)</a></li>
    </ul>
    <hr>
    <h3>Control Service B (Open these in new tabs or use Postman/curl):</h3>
    <p>
        <button onclick="fetch('http://localhost:5001/induce-failure', {{method: 'POST'}})">Make Service B Fail</button>
        <button onclick="fetch('http://localhost:5001/remove-failure', {{method: 'POST'}})">Make Service B Healthy</button>
    </p>
    <p>
        <button onclick="fetch('http://localhost:5001/induce-latency', {{method: 'POST'}})">Make Service B Slow</button>
        <button onclick="fetch('http://localhost:5001/remove-latency', {{method: 'POST'}})">Make Service B Fast</button>
    </p>
    <script>
        // Pequeño script para que los botones POST funcionen sin cambiar de página
        // Opcional, pero mejora la experiencia de la demo
        document.querySelectorAll('button[onclick^="fetch"]').forEach(button => {{
            button.addEventListener('click', (event) => {{
                event.preventDefault();
                const url = button.getAttribute('onclick').match(/'([^']+)'/)[1];
                const method = button.getAttribute('onclick').match(/{{method: '([^']+)'}}/)[1];
                fetch(url, {{ method: method }})
                    .then(response => response.json())
                    .then(data => alert(data.message || JSON.stringify(data)))
                    .catch(error => alert('Error controlling Service B: ' + error));
            }});
        }});
    </script>
    """

@app.route('/health') # El healthcheck de service-a
def health_check():
    # Para el healthcheck de Docker Compose, es mejor que sea una llamada directa
    # y no dependa del circuit breaker principal para /data.
    # Este healthcheck solo verifica si service-a (esta app) está arriba.
    # La dependencia de service-b se maneja en el docker-compose.yml
    return jsonify({"status": "healthy", "service": "A"})


# Función que realmente llama a service-b y será envuelta por el Circuit Breaker
def _call_service_b_data_endpoint():
    print("Service A: Attempting to call Service B /data endpoint...")
    # Usamos service-b como hostname porque Docker Compose lo resolverá a la IP del contenedor service-b
    response = requests.get('http://service-b:5001/data', timeout=3) # Timeout para la petición individual
    response.raise_for_status()  # Lanza una excepción para códigos de error HTTP 4xx/5xx
    return response.json()

@app.route('/call-service-b')
def call_service_b_with_cb():
    try:
        # Usamos el método `call` del CircuitBreaker
        data_from_b = service_b_cb.call(_call_service_b_data_endpoint)
        
        print(f"Service A: Call to Service B successful. State: {service_b_cb.state}")
        return jsonify({
            "message": "Successfully fetched data from Service B.",
            "data": data_from_b,
            "circuit_state": str(service_b_cb.state)
        })
    except CircuitBreakerError as e:
        # El circuito está abierto o la llamada falló y contribuyó al conteo de fallos
        print(f"Service A: CircuitBreakerError: {e}. State: {service_b_cb.state}")
        return jsonify({
            "error": "Circuit Breaker is OPEN or call failed.",
            "details": str(e),
            "circuit_state": str(service_b_cb.state),
            "fallback_message": "Serving fallback data as Service B is unavailable."
        }), 503 # Service Unavailable
    except requests.exceptions.RequestException as e:
        # Otros errores de red/HTTP que no necesariamente abren el circuito inmediatamente
        # pero que el circuit breaker contará si es configurado para ello.
        print(f"Service A: RequestException: {e}. State: {service_b_cb.state}")
        return jsonify({
            "error": "Failed to connect to Service B.",
            "details": str(e),
            "circuit_state": str(service_b_cb.state) # Puede ser útil ver el estado aquí también
        }), 502 # Bad Gateway

@app.route('/circuit-status')
def circuit_status():
    # La librería circuitbreaker 1.4.0 tiene estos atributos:
    # state, failure_count, failure_threshold, recovery_timeout, last_failure_time
    return jsonify({
        "circuit_breaker_name": service_b_cb.name,
        "state": str(service_b_cb.state),
        "failure_count": service_b_cb.failure_count,
        "failure_threshold": service_b_cb.failure_threshold,
        "recovery_timeout": service_b_cb.recovery_timeout,
        "last_failure_time": str(service_b_cb.last_failure_time) if service_b_cb.last_failure_time else None
    })

if __name__ == '__main__':
    # Esta sección no se ejecuta cuando se usa Gunicorn.
    # Gunicorn se invoca desde el CMD del Dockerfile.
    # Dejarlo aquí no hace daño y permite ejecutar `python app.py` localmente para pruebas rápidas si se desea.
    app.run(host='0.0.0.0', port=5000, debug=True)
