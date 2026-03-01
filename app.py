import sqlite3
import os
from flask import Flask, Response, render_template_string, abort
from PIL import Image
import io

app = Flask(__name__)
DB_NAME = "world.mbtiles"

# Check if the database exists at startup
if not os.path.exists(DB_NAME):
    print(f"ERROR: Database file '{DB_NAME}' not found in the current directory.")
    exit(1)

# HTML Template with 3D Globe Projection
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Offline Map Viewer - 3D Globe</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
    <link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet" />
    <style> 
        body { margin: 0; padding: 0; background-color: #050505; color: white; } 
        #map { width: 100vw; height: 100vh; }
        #info {
            position: absolute; top: 10px; left: 10px;
            background: rgba(0,0,0,0.8); padding: 10px;
            border-radius: 5px; font-family: monospace;
            z-index: 999; pointer-events: none;
        }
        #toggle3d {
            position: absolute; bottom: 30px; right: 20px;
            background: rgba(0,0,0,0.8); color: white;
            border: 1px solid #666; border-radius: 5px;
            padding: 10px 20px; font-family: monospace;
            cursor: pointer; z-index: 1000;
        }
        #toggle3d:hover { background: #333; }
    </style>
</head>
<body>
    <div id="info">Status: Offline<br>Loading...</div>
    <div id="map"></div>
    <button id="toggle3d">Toggle 3D View</button>
    <script>
        const map = new maplibregl.Map({
            container: 'map',
            projection: 'globe',                 // 🌍 Enable 3D globe view
            center: [73.04, 33.68],              // Islamabad
            zoom: 13,
            pitch: 60,                            // Tilt for perspective
            bearing: 30,
            maxZoom: 22,
            style: {
                version: 8,
                sources: {
                    'offline-source': {
                        type: 'raster',
                        tiles: ['http://localhost:5000/tile/{z}/{x}/{y}.png'],
                        tileSize: 256,
                        minzoom: 0,
                        maxzoom: 19
                    }
                },
                layers: [
                    {
                        'id': 'background',
                        'type': 'background',
                        'paint': { 'background-color': '#050505' }
                    },
                    {
                        'id': 'satellite',
                        'type': 'raster',
                        'source': 'offline-source',
                        'paint': { 'raster-fade-duration': 0 }
                    }
                ]
            }
        });

        map.addControl(new maplibregl.NavigationControl());

        // Debug info with projection
        map.on('move', () => {
            document.getElementById('info').innerHTML = 
                'Center: ' + map.getCenter().lng.toFixed(4) + ', ' + map.getCenter().lat.toFixed(4) + '<br>' +
                'Zoom: ' + map.getZoom().toFixed(2) + '<br>' +
                'Pitch: ' + map.getPitch().toFixed(1) + '°<br>' +
                'Bearing: ' + map.getBearing().toFixed(1) + '°<br>' +
                'Projection: globe';
        });

        // 3D Toggle (changes tilt, keeps globe projection)
        document.getElementById('toggle3d').addEventListener('click', () => {
            if (map.getPitch() === 0) {
                // Switch to 3D
                map.easeTo({ pitch: 60, bearing: 30, duration: 1000 });
            } else {
                // Switch to 2D (top-down)
                map.easeTo({ pitch: 0, bearing: 0, duration: 1000 });
            }
        });

        // Optional: show when tiles are missing (for debugging)
        map.on('error', (e) => {
            if (e.error && e.error.status === 404) {
                console.log('Tile not found (expected if area not downloaded)');
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/tile/<int:z>/<int:x>/<int:y>.png')
def get_tile(z, x, y):
    # Convert XYZ to TMS (MBTiles format)
    tms_y = (1 << z) - 1 - y   # 2^z - 1 - y

    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?", (z, x, tms_y))
        tile = cursor.fetchone()
        if tile:
            return Response(tile[0], mimetype='image/png')
        else:
            # Return a transparent 1x1 PNG instead of 404 to keep map clean
            img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            return Response(buf.getvalue(), mimetype='image/png')
    except Exception as e:
        print(f"Error serving tile {z}/{x}/{y}: {e}")
        abort(404)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("Starting 3D Globe Map Server...")
    print(f"Using database: {DB_NAME}")
    print("Open your browser to: http://localhost:5000")
    app.run(port=5000, debug=False)