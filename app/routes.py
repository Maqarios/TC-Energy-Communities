import os
import flask
import googlemaps
import json
from datetime import datetime
import shapely
import math

ZOOM = 20
IMG_WIDTH = 640
IMG_HEIGHT = 640

# Define the data directory
DATA_DIR = os.path.join("/tmp")

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
    data = flask.request.get_json()
    address = data.get("address")
    geocode_result = gmaps.geocode(address)
    if not geocode_result:
        return flask.jsonify({"error": "Place not found"})

    location = geocode_result[0]["geometry"]["location"]
    image_url = generate_static_map_url(location["lat"], location["lng"])

    file_path = os.path.join(DATA_DIR, "{}.json".format(geocode_result[0]["place_id"]))
    roofs = []
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            roofs = json.load(f)

    flask.session["place_id"] = geocode_result[0]["place_id"]
    flask.session["address"] = address
    flask.session["sqm_per_pixel"] = (
        156543033.92 * math.cos(location["lat"] * math.pi / 180) / math.pow(2, ZOOM)
    )

    return flask.jsonify(
        {
            "image_url": image_url,
            "width": IMG_WIDTH,
            "height": IMG_HEIGHT,
            "roofs": roofs,
        }
    )


@main.route("/calculate", methods=["POST"])
def calculate():
    data = flask.request.json
    roofs = data.get("roofs")
    obstacles = data.get("obstacles", [])
    sqm_per_pixel = flask.session.get("sqm_per_pixel")

    if not flask.session.get("place_id"):
        return (
            flask.jsonify({"error": "Missing address"}),
            400,
        )

    if not roofs:
        return (
            flask.jsonify({"error": "Missing roofs data"}),
            400,
        )

    file_path = os.path.join(DATA_DIR, "{}.json".format(flask.session["place_id"]))
    estimated_rectangles = []

    for roof in roofs:
        polygon_coords = roof["coordinates"]
        shapely_polygon = shapely.geometry.Polygon(polygon_coords)
        area_sqm = shapely_polygon.area / sqm_per_pixel
        roof["area_sqm"] = area_sqm

        obstacle_polygons = [
            shapely.geometry.Polygon(obstacle["coordinates"]) for obstacle in obstacles
        ]

        rect_width = 1 * math.sqrt(sqm_per_pixel)  # Define the width of the rectangles
        rect_height = 1.6 * math.sqrt(
            sqm_per_pixel
        )  # Define the height of the rectangles

        best_rectangles = fill_polygon_with_rectangles(
            shapely_polygon, obstacle_polygons, rect_width, rect_height
        )

        roof_kWp = 0.33 * len(best_rectangles)
        roof["roof_kWp"] = roof_kWp

        estimated_rectangles.extend(
            {
                "coordinates": list(rectangle.exterior.coords),
                "roof_polygon_id": roof["id"],
            }
            for rectangle in best_rectangles
        )

    with open(file_path, "w") as f:
        json.dump(roofs + obstacles, f, indent=2)

    return flask.jsonify({"estimated_rectangles": estimated_rectangles, "roofs": roofs})


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

    with open(
        os.path.join(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"),
            "simulation.json",
        ),
        "r",
    ) as f:
        simulation_data = json.load(f)

    total_generation = 0
    total_consumption = 0

    for record in simulation_data["Data"]:
        record_date = datetime.strptime(record["date"], "%Y-%m-%d")
        if start_date <= record_date <= end_date:
            total_generation += record["generation_kWh"]
            total_consumption += record["consumption_kWh"]

    remaining_consumption = total_consumption - total_generation

    # Calculate total cost and profit
    government_price_per_kWh = 0.4
    generation_cost = total_generation * government_price_per_kWh
    consumption_cost = total_consumption * government_price_per_kWh

    initial_investment = simulation_data["PV System Cost"]["Total Cost"]

    profit_earned = total_generation * government_price_per_kWh

    return flask.jsonify(
        {
            "total_generation": round(total_generation),
            "total_consumption": round(total_consumption),
            "remaining_consumption": round(remaining_consumption),
            "generation_cost": round(generation_cost),
            "consumption_cost": round(consumption_cost),
            "initial_investment": round(initial_investment),
            "profit_earned": round(profit_earned),
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


def fill_polygon_with_rectangles(polygon, obstacles, rect_width, rect_height):
    def create_rectangle(x, y, rect_width, rect_height, angle=0):
        rectangle = shapely.geometry.box(x, y, x + rect_width, y + rect_height)
        return shapely.affinity.rotate(rectangle, angle, origin="centroid")

    def rotate_to_edge_angle(polygon):
        edges = []
        coords = list(polygon.exterior.coords)
        for i in range(len(coords) - 1):
            p1, p2 = coords[i], coords[i + 1]
            angle = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
            edges.append((p1, p2, angle))
        return edges

    best_rectangles = []
    max_rectangle_count = 0

    polygon_edges = rotate_to_edge_angle(polygon)

    for edge in polygon_edges:
        p1, p2, angle = edge
        aligned_rectangles = []
        placed_rectangles = []

        minx, miny, maxx, maxy = polygon.bounds
        y = miny
        while y < maxy:
            x = minx
            while x < maxx:
                rectangle = create_rectangle(x, y, rect_width, rect_height, angle)
                if (
                    polygon.contains(rectangle)
                    and not any(
                        rectangle.intersects(obstacle) for obstacle in obstacles
                    )
                    and not any(
                        rectangle.intersects(placed) for placed in placed_rectangles
                    )
                ):
                    aligned_rectangles.append(rectangle)
                    placed_rectangles.append(rectangle)
                x += rect_width
            y += rect_height

        if len(aligned_rectangles) > max_rectangle_count:
            best_rectangles = aligned_rectangles
            max_rectangle_count = len(aligned_rectangles)

    return best_rectangles
