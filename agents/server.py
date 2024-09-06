from flask import Flask, request, jsonify
from agents import SimulationModel
import threading
import queue

app = Flask(__name__)

sim = None
sim_thread = None
message_queue = queue.Queue()

def run_simulation():
    global sim
    parameters = {
        "message_queue": message_queue
    }
    sim = SimulationModel(parameters)
    sim.run()

@app.route("/", methods=["POST"])
def main():
    global sim, sim_thread, message_queue
    
    data = request.json
    camera_id = data.get('camera_id')
    intruder_detected = data.get('intruder_detected', False)
    
    if sim_thread is None or not sim_thread.is_alive():
        sim_thread = threading.Thread(target=run_simulation)
        sim_thread.start()
    
    message_queue.put((camera_id, intruder_detected))

    intruders_detected = sum(drone.intruders for drone in sim.drone) if sim else 0
    
    return jsonify({
        "status": "success",
        "message": f"Processed data for camera {camera_id}",
        "intruders_detected": intruders_detected
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8585)