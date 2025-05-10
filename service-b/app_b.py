from flask import Flask, jsonify, request
import time
import random

app = Flask(__name__)

# Estado de salud de Service B
service_b_is_healthy = True
service_b_is_slow = False

@app.route('/health')
def health_check():
    if service_b_is_healthy:
        return jsonify({"status": "healthy", "service": "B"})
    else:
        return jsonify({"status": "unhealthy", "service": "B"}), 503

@app.route('/data')
def get_data():
    print(f"Service B /data called. Healthy: {service_b_is_healthy}, Slow: {service_b_is_slow}")
    if service_b_is_slow:
        sleep_duration = random.uniform(2, 5) # Simula latencia entre 2 y 5 segundos
        print(f"Service B simulating latency for {sleep_duration:.2f} seconds.")
        time.sleep(sleep_duration)

    if service_b_is_healthy:
        return jsonify({"message": "Hello from Service B!", "data": random.randint(1, 100)})
    else:
        return jsonify({"error": "Service B is intentionally failing."}), 500

@app.route('/induce-failure', methods=['POST'])
def induce_failure():
    global service_b_is_healthy
    service_b_is_healthy = False
    print("Service B set to UNHEALTHY state.")
    return jsonify({"message": "Service B will now return errors for /data."}), 200

@app.route('/remove-failure', methods=['POST'])
def remove_failure():
    global service_b_is_healthy
    service_b_is_healthy = True
    print("Service B set to HEALTHY state.")
    return jsonify({"message": "Service B will now work normally for /data."}), 200

@app.route('/induce-latency', methods=['POST'])
def induce_latency():
    global service_b_is_slow
    service_b_is_slow = True
    print("Service B set to SLOW state.")
    return jsonify({"message": "Service B will now have added latency for /data."}), 200

@app.route('/remove-latency', methods=['POST'])
def remove_latency():
    global service_b_is_slow
    service_b_is_slow = False
    print("Service B set to NORMAL SPEED state.")
    return jsonify({"message": "Service B will now respond quickly for /data."}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)