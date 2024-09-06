from flask import Flask, request, jsonify
from simulation import simulation
from vision.vision import image_processing_bp
from agents import SecurityModel
import agentpy as ap
from util.camera import process_image


app = Flask(__name__)
app.register_blueprint(simulation, url_prefix="/sim")
app.register_blueprint(image_processing_bp, url_prefix="/image")


@app.route("/")
def home():
    return "Hello \t Welcome to the Drone Security System!"


@app.route("/vision", methods=["POST"])
def vision():
    req_id = request.json.get("id")
    image_data = request.json.get("image")
    
    if not req_id or not image_data:
        return jsonify({"error": "Missing 'id' or 'image' in request body"}), 400
    
    return process_image(req_id, image_data)

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
        "guard": guard_info,
        "cameras": cameras_info,
        "drone": drone_info,
    }


if __name__ == "__main__":
    parameters = {}  # Define any parameters needed for the model
    model = SecurityModel(parameters)
    model.setup()
    app.run(debug=True, host="0.0.0.0", port=8585)
