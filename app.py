import os
import flask
import googlemaps
import json
import shapely

ZOOM = 20
IMG_WIDTH = 640
IMG_HEIGHT = 640

app = flask.Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_API_KEY"))


@app.route("/")
def index():
    return flask.render_template("roof_calculator.html")


@app.route("/get_image", methods=["POST"])
def get_image():
    address = flask.request.form["address"]
    geocode_result = gmaps.geocode(address)
    if not geocode_result:
        return flask.jsonify({"error": "Place not found"})

    flask.session["place_id"] = geocode_result[0]["place_id"]

    location = geocode_result[0]["geometry"]["location"]
    image_url = generate_static_map_url(location["lat"], location["lng"])

    file_path = os.path.join("data", "{}.json".format(geocode_result[0]["place_id"]))
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


@app.route("/save_polygons", methods=["POST"])
def save_polygons():
    data = flask.request.json
    polygons = data.get("polygons")
    if not flask.session["place_id"] or not polygons:
        return flask.jsonify({"error": "Missing address or polygons data"}), 400

    file_path = os.path.join("data", "{}.json".format(flask.session["place_id"]))
    with open(file_path, "w") as f:
        json.dump(polygons, f, indent=2)

    # TODO: remove
    # for polygon in polygons:
    #     print(polygon["name"], polygon_area(polygon["coordinates"]) / 100)
    #     print(
    #         len(
    #             fill_polygon_with_rectangles(
    #                 shapely.geometry.Polygon(polygon["coordinates"]), 14, 22.62
    #             )
    #         )
    #     )

    return flask.jsonify({"success": True, "file_path": file_path})


def generate_static_map_url(lat, lng):
    base_url = "https://maps.googleapis.com/maps/api/staticmap"
    params = {
        "center": "{},{}".format(lat, lng),
        "zoom": ZOOM,  # Adjust zoom level as needed
        "size": "{}x{}".format(IMG_WIDTH, IMG_HEIGHT),
        "maptype": "satellite",
        "key": os.getenv("GOOGLE_API_KEY"),
    }
    url_params = "&".join(["{}={}".format(key, value) for key, value in params.items()])
    return "{}?{}".format(base_url, url_params)


def polygon_area(coordinates):
    n = len(coordinates)  # Number of vertices
    area = 0.0

    for i in range(n):
        x1, y1 = coordinates[i]
        x2, y2 = coordinates[(i + 1) % n]  # Wraps around to the first vertex
        area += x1 * y2 - y1 * x2

    return abs(area) / 2.0


def fill_polygon_with_rectangles(polygon, rect_width, rect_height):
    minx, miny, maxx, maxy = polygon.bounds

    # Create a list to hold rectangles
    rectangles = []

    # Iterate over the bounding box with the given rectangle dimensions
    y = miny
    while y < maxy:
        x = minx
        while x < maxx:
            # Create a rectangle
            rect = shapely.geometry.box(x, y, x + rect_width, y + rect_height)
            # Check if it intersects with the polygon
            if rect.intersects(polygon):
                rectangles.append(rect.intersection(polygon))
            x += rect_width
        y += rect_height

    return rectangles


if __name__ == "__main__":
    app.run(debug=True)
