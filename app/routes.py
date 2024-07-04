import os
import flask
import googlemaps
import json
from datetime import datetime

ZOOM = 20
IMG_WIDTH = 640
IMG_HEIGHT = 640

# Define the data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

main = flask.Blueprint("main", __name__)
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_API_KEY"))


@main.route("/")
def index():
    return flask.render_template("index.html")


@main.route("/power_mix")
def power_mix():
    return flask.render_template("power_mix.html")


@main.route("/roof_calculator")
def roof_calculator():
    return flask.render_template(
        "roof_calculator.html", img_width=IMG_WIDTH, img_height=IMG_HEIGHT
    )


@main.route("/get_image", methods=["POST"])
def get_image():
    address = flask.request.form["address"]
    geocode_result = gmaps.geocode(address)
    if not geocode_result:
        return flask.jsonify({"error": "Place not found"})

    flask.session["place_id"] = geocode_result[0]["place_id"]

    location = geocode_result[0]["geometry"]["location"]
    image_url = generate_static_map_url(location["lat"], location["lng"])

    file_path = os.path.join(DATA_DIR, "{}.json".format(geocode_result[0]["place_id"]))
    polygons = []
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            polygons = json.load(f)

    return flask.jsonify(
        {
            "image_url": image_url,
            "width": IMG_WIDTH,
            "height": IMG_HEIGHT,
            "polygons": polygons,
        }
    )


@main.route("/save_polygons", methods=["POST"])
def save_polygons():
    data = flask.request.json
    polygons = data.get("polygons")
    if not flask.session.get("place_id") or not polygons:
        return flask.jsonify({"error": "Missing address or polygons data"}), 400

    file_path = os.path.join(DATA_DIR, "{}.json".format(flask.session["place_id"]))
    with open(file_path, "w") as f:
        json.dump(polygons, f, indent=2)

    return flask.jsonify({"success": True, "file_path": file_path})


@main.route("/calculate_power_mix", methods=["POST"])
def calculate_power_mix():
    data = flask.request.json
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")

    if not start_date_str or not end_date_str:
        return flask.jsonify({"error": "Invalid date range"}), 400

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError:
        return flask.jsonify({"error": "Invalid date format"}), 400

    with open(os.path.join(DATA_DIR, "simulation.json"), "r") as f:
        simulation_data = json.load(f)

    total_generation = 0
    total_consumption = 0

    for record in simulation_data["Data"]:
        record_date = datetime.strptime(record["date"], "%Y-%m-%d")
        if start_date <= record_date <= end_date:
            total_generation += record["generation_kWh"]
            total_consumption += record["consumption_kWh"]

    remaining_consumption = total_consumption - total_generation

    return flask.jsonify(
        {
            "total_generation": total_generation,
            "total_consumption": total_consumption,
            "remaining_consumption": remaining_consumption,
        }
    )


def generate_static_map_url(lat, lng):
    base_url = "https://maps.googleapis.com/maps/api/staticmap"
    params = {
        "center": "{},{}".format(lat, lng),
        "zoom": ZOOM,
        "size": "{}x{}".format(IMG_WIDTH, IMG_HEIGHT),
        "maptype": "satellite",
        "key": os.getenv("GOOGLE_API_KEY"),
    }
    url_params = "&".join(["{}={}".format(key, value) for key, value in params.items()])
    return "{}?{}".format(base_url, url_params)
