from flask import Flask, request, jsonify
from agents import SecurityModel
from util.camera import process_image


app = Flask(__name__)


@app.route("/")
def home():
    return "Hello \t Welcome to the Drone Security System!"


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
    req_id = request.json.get("id")
    image_data = request.json.get("image")

    if not req_id or not image_data:
        return jsonify({"error": "Missing 'id' or 'image' in request body"}), 400

    return process_image(req_id, image_data)


@app.route("/camera_check", methods=["POST"])
def camera_info():
    camera_id = request.json.get("id")
    if not camera_id:
        return jsonify({"error": "Missing 'id' in request body"}), 400
    camera = model.cameras[camera_id]
    if not camera:
        return jsonify({"error": "Invalid camera ID"}, 400)
    camera.increase_alert_checks()  # Increase the alert checks
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
    guard_info = model.guard[0].give_info().json
    cameras_info = [camera.give_info().json for camera in model.cameras]
    drone_info = model.drone[0].give_info().json

    model.step()
    return {
        "channel": model.channel,
        "guard": guard_info,
        "cameras": cameras_info,
        "drone": drone_info,
    }


if __name__ == "__main__":
    parameters = {}  # Define any parameters needed for the model
    model = SecurityModel(parameters)
    model.setup()
    app.run(debug=True, host="0.0.0.0", port=8585)
