from flask import Flask, jsonify
import threading
import time
import sys

# Ensure UTF-8 output in terminal
sys.stdout.reconfigure(encoding='utf-8')

# Import the background task
try:
    from api.association.association_build import start_generate_association
except ImportError as e:
    print(f"[ERROR] Cannot import association module: {e}")
    sys.exit(1)

# Flask app initialization
app = Flask(__name__)

# Shared task state (thread-safe using a lock)
task_status = {
    "is_running": False,
    "last_message": "No association process has run yet.",
    "error": None
}
status_lock = threading.Lock()

# ---- ROUTES ----

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/home/<name>')
def hello(name):
    return f"Hello, {name}!"

@app.route('/api/association', methods=['GET', 'POST'])
def association_trigger():
    with status_lock:
        if task_status["is_running"]:
            return jsonify({
                'ok': False,
                'message': "Custom product generation is already in progress. Please wait."
            }), 409

        # Mark as running
        task_status["is_running"] = True
        task_status["last_message"] = "Starting custom product generation..."
        task_status["error"] = None

    # Start async task
    threading.Thread(target=process_association_task, daemon=True).start()

    return jsonify({
        'ok': True,
        'message': "Custom product generation started in background."
    })

def process_association_task():
    print("[INFO] Background task started.")
    try:
        time.sleep(5)  # Simulated processing
        start_generate_association()
        msg = "Custom product generation completed successfully."
        err = None
    except Exception as e:
        msg = f"Error: {e}"
        err = str(e)
        print(f"[ERROR] {e}")
    finally:
        with status_lock:
            task_status["is_running"] = False
            task_status["last_message"] = msg
            task_status["error"] = err
        print("[INFO] Background task ended.")

@app.route('/api/status', methods=['GET'])
def get_status():
    with status_lock:
        return jsonify({
            'status': 'Server is running',
            'custom_product_generation_in_progress': task_status["is_running"],
            'last_task_message': task_status["last_message"],
            'last_task_error': task_status["error"],
            'ok': True
        })

# ---- MAIN ----
if __name__ == '__main__':
    app.run(debug=True, port=5000)
