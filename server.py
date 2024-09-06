from flask import Flask, Response, request, jsonify
from agents import SecurityModel
from util.camera import process_image

app = Flask(__name__)


@app.route("/")
def home():
    return "Hello \t Welcome to the Drone Security System!"

@app.route("/move_system")
def move_system():
    model.step()
    return jsonify({"message": "System moved"})

@app.route("/set_channel", methods=["POST"])
def set_channel():
    subject = request.json.get("subject")
    if not isinstance(subject, list):
        return jsonify({"error": "Invalid 'subject' type, expected a list"}), 400

    content = request.json.get("content")
    if not subject or not content:
        return jsonify({"error": "Missing 'subject' or 'content' in request body"}), 400
    model.channel = {"subject": subject, "content": content}

    return jsonify(model.channel)


@app.route("/clean_channel", methods=["GET"])
def clean_channel():
    model.channel = {}
    return jsonify(model.channel)


@app.route("/vision", methods=["POST"])
def vision():
    image_data = request.json.get("image")

    if not image_data:
        return jsonify({"error": "Missing 'image' in request body"}), 400

    # Call process_image and handle the returned dictionary
    result = process_image(image_data)
    
    if "error" in result:
        return jsonify(result), 500
    
    message = result.get("message")
    if not message:
        return jsonify({"error": "No result from vision processing"}), 500
    if message == "YES":
        model.channel = {"subject": ["vision"], "content": "intruder"}
    
    return jsonify({"message": "Vision processing successful", "result": message})

@app.route("/visionFinal", methods=["POST"])
def visionFinal():
    image_data = request.json.get("image")

    if not image_data:
        return jsonify({"error": "Missing 'image' in request body"}), 400

    # Call process_image and handle the returned dictionary
    result = process_image(image_data)
    
    if "error" in result:
        return jsonify(result), 500
    
    message = result.get("message")
    if not message:
        return jsonify({"error": "No result from vision processing"}), 500
    if message == "YES":
        model.channel = {"subject": ["Drone"], "content": "intruder"}
    
    return jsonify({"message": "Vision processing successful", "result": message})


@app.route("/vision_result", methods=["POST"])
def vision_result():
    agent_type = request.json.get("agent_type")
    agent_id = request.json.get("id")
    result = request.json.get("result")

    if not agent_type or not result:
        return (
            jsonify({"error": "Missing 'agent_type' or 'result' in request body"}),
            400,
        )

    if agent_type == "drone":
        model.drone[0].update_vision_result(result)
        subject = "drone"
    elif agent_type == "camera":
        if not agent_id:
            return jsonify({"error": "Missing 'id' for camera agent"}), 400
        model.cameras[agent_id].update_vision_result(result)
        subject = "camera"
    else:
        return jsonify({"error": "Invalid agent_type"}), 400

    model.channel = {"subject": subject, "content": result}
    return jsonify(
        {"message": "Vision result updated successfully", "channel": model.channel}
    )


@app.route("/camera_check", methods=["POST"])
def camera_info():
    camera_id = request.json.get("id")
    if not camera_id:
        return jsonify({"error": "Missing 'id' in request body"}), 400
    camera = model.cameras[camera_id]
    if not camera:
        return jsonify({"error": "Invalid camera ID"}, 400)
    camera.increase_alert_checks()
    return jsonify(camera.give_info().json)


@app.route("/test")  # Testing route
def test():

    model.guard[0].panoramic_analysis()
    return model.guard[0].give_info()


@app.route("/channel")
def channel():
    return model.channel


@app.route("/agents_info")
def agents_info():
    guard_info = model.guard[0].give_info()
    cameras_info = [camera.give_info() for camera in model.cameras]
    drone_info = model.drone[0].give_info()
    model.step()

    return jsonify(
        {
            "channel": model.channel,
            "guard": (
                guard_info.get_json()
                if isinstance(guard_info, Response)
                else guard_info
            ),
            "cameras": [
                cam.get_json() if isinstance(cam, Response) else cam
                for cam in cameras_info
            ],
            "drone": (
                drone_info.get_json()
                if isinstance(drone_info, Response)
                else drone_info
            ),
        }
    )


@app.route("/drone_info", methods=["GET"])
def get_drone_info():
    drone = model.drone[0]
    return jsonify(
        {
            "current_position": drone.pos,
            "detection": drone.detection,
            "panoramic": drone.panoramic,
            "time_counter": drone.time_counter,
            "drone_override": model.guard[0].drone_override,
        }
    )


@app.route("/guard_info", methods=["GET"])
def get_guard_info():
    guard = model.guard[0]
    return jsonify(
        {
            "drone_override": guard.drone_override,
            "initialize_panoramic_view": guard.initialize_panoramic_view,
            "drone_override_timer": guard.drone_override_timer,
        }
    )


@app.route("/trigger_panoramic", methods=["GET"])
def trigger_panoramic():
    guard = model.guard[0]
    guard.panoramic_analysis()
    return jsonify({"message": "Panoramic analysis triggered"})


@app.route("/simulate_steps", methods=["POST"])
def simulate_steps():
    steps = request.json.get("steps", 1)
    for _ in range(steps):
        model.step()
    return jsonify({"message": f"Simulated {steps} steps"})


@app.route("/reset_simulation", methods=["GET"])
def reset_simulation():
    global model
    model = SecurityModel()
    return jsonify({"message": "Simulation reset"})


if __name__ == "__main__":
    parameters = {}  # Define any parameters needed for the model
    model = SecurityModel(parameters)
    model.setup()
    app.run(debug=True, host="0.0.0.0", port=8585)
