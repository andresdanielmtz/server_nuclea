# simulation.py
from flask import Blueprint, request, jsonify
from agents import Guard, Camera, Drone


simulation = Blueprint("simulation", __name__)


# Route to handle simulation data
@simulation.route("/", methods=["GET"])
def main():
    pass
