import os
import math
import requests
import shutil
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin
from flask import Flask, request, jsonify, send_from_directory, render_template, send_file
from threading import Thread
import time
from PIL import Image
import re

app = Flask(__name__)


TILE_SERVERS = {
    "OGF Carto": "https://tile.opengeofiction.net/ogf-carto/",
    "Arhet Carto": "https://tiles02.rent-a-planet.com/arhet-carto/",
    "OGF Topo": "https://tiles04.rent-a-planet.com/ogf-topo/",
    "CyclOGF": "https://tiles06.opengeofiction.net/cyclogf/",
    "ÖPNVKarte/Openbusmap": "https://tile.memomaps.de/tilegen/",
    "Humanitarian Layer": "https://a.tile.openstreetmap.fr/hot/",
    "OSM France": "https://a.tile.openstreetmap.fr/osmfr/"
}

tile_folder = "osm_tiles"
stitched_folder = "stitched_maps"
progress = {"total": 0, "downloaded": 0}

# Ensure folders exist
os.makedirs(tile_folder, exist_ok=True)
os.makedirs(stitched_folder, exist_ok=True)

def latlon_to_tile(lat, lon, zoom):
    """Convert latitude and longitude to tile coordinates."""
    lat_rad = math.radians(round(lat, 6))
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return xtile, ytile

def download_tile(tile_server, zoom, x, y):
    """Download a single tile."""
    global progress
    tile_url = urljoin(tile_server, f"{zoom}/{x}/{y}.png")
    tile_path = os.path.join(tile_folder, f"{zoom}_{x}_{y}.png")

    if os.path.exists(tile_path):
        progress["downloaded"] += 1
        return

    try:
        response = requests.get(tile_url, stream=True, timeout=20)
        if response.status_code == 200:
            with open(tile_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            progress["downloaded"] += 1
        else:
            print(f"Failed: {tile_url} (Status {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {tile_url}: {e}")

def download_tiles(tile_server, zoom, lat1, lon1, lat2, lon2, max_threads=12):
    """Download all tiles in the given coordinate range using multiple threads."""
    global progress
    x_min, y_min = latlon_to_tile(lat1, lon1, zoom)
    x_max, y_max = latlon_to_tile(lat2, lon2, zoom)

    tile_coords = [(zoom, x, y) for x in range(min(x_min, x_max), max(x_min, x_max) + 1)
                               for y in range(min(y_min, y_max), max(y_min, y_max) + 1)]

    progress["total"] = len(tile_coords)
    progress["downloaded"] = 0

    with ThreadPoolExecutor(max_threads) as executor:
        for zoom, x, y in tile_coords:
            executor.submit(download_tile, tile_server, zoom, x, y)


def count_tiles(zoom, lat1, lon1, lat2, lon2):
    x_min, y_min = latlon_to_tile(lat1, lon1, zoom)
    x_max, y_max = latlon_to_tile(lat2, lon2, zoom)

    total = (abs(x_max - x_min) + 1) * (abs(y_max - y_min) + 1)
    return total

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gallery/')
def gallery():
    return render_template('gallery.html')

@app.route('/start_download', methods=['POST'])
def start_download():
    data = request.json
    zoom = int(data['zoom'])
    lat1, lon1 = round(data['lat1'], 6), round(data['lon1'], 6)
    lat2, lon2 = round(data['lat2'], 6), round(data['lon2'], 6)
    tile_server = data.get('tile_server', list(TILE_SERVERS.values())[0])

    if tile_server not in TILE_SERVERS.values():
        return jsonify({"status": "Error", "message": "Invalid tile server"}), 400

    total_tiles = count_tiles(zoom, lat1, lon1, lat2, lon2)

    # 🚫 Reject if > 1000 tiles
    if total_tiles > 1000:
        return jsonify({
            "status": "Error",
            "message": "Too many tiles — please zoom in or select a smaller area.",
            "total_tiles": total_tiles
        }), 400

    Thread(target=download_tiles, args=(tile_server, zoom, lat1, lon1, lat2, lon2)).start()

    return jsonify({"status": "Download started", "total_tiles": total_tiles})

@app.route('/progress')
def get_progress():
    return jsonify(progress)

def get_tile_ranges(zoom):
    x_values = []
    y_values = []

    tile_dir = "osm_tiles"  # This is where tiles are saved
    if not os.path.exists(tile_dir):
        print(f"Error: Tile directory {tile_dir} does not exist!")
        return ([], [])

    for filename in os.listdir(tile_dir):
        match = re.match(rf'{zoom}_(\d+)_(\d+)\.png', filename)  # Match "15_31070_20596.png"
        if match:
            x_values.append(int(match.group(1)))  # Extract x value
            y_values.append(int(match.group(2)))  # Extract y value

    if not x_values or not y_values:
        print("Error: No valid tiles found for stitching!")
        return ([], [])

    return (min(x_values), max(x_values)), (min(y_values), max(y_values))

def stitch_tiles(zoom, tile_size=256):
    """Stitch OSM tiles into a large image."""
    x_range, y_range = get_tile_ranges(zoom)
    width, height = (x_range[1] - x_range[0] + 1) * tile_size, (y_range[1] - y_range[0] + 1) * tile_size
    stitched_image = Image.new("RGB", (width, height), (255, 255, 255))
    for x in range(x_range[0], x_range[1] + 1):
        for y in range(y_range[0], y_range[1] + 1):
            tile_path = os.path.join(tile_folder, f"{zoom}_{x}_{y}.png")
            x_offset, y_offset = (x - x_range[0]) * tile_size, (y - y_range[0]) * tile_size
            if os.path.exists(tile_path):
                with Image.open(tile_path) as tile:
                    stitched_image.paste(tile, (x_offset, y_offset))
    map_number = len(os.listdir(stitched_folder)) + 1
    output_file = os.path.join(stitched_folder, f"map_{map_number}.png")
    stitched_image.save(output_file, "PNG")
    shutil.rmtree(tile_folder)
    os.makedirs(tile_folder, exist_ok=True)
    return output_file

@app.route('/stitch_map', methods=['POST'])
def start_stitching():
    data = request.json
    zoom = int(data['zoom'])
    file_path = stitch_tiles(zoom)
    return jsonify({"status": "Success", "file": file_path})

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(stitched_folder, filename)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
