import sqlite3
from flask import Flask, Response, render_template_string

app = Flask(__name__)
DB_NAME = "world.mbtiles"

# HTML Template with Black Background and Debugging
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Offline Map Viewer</title>
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
    </style>
</head>
<body>
    <div id="info">Status: Offline<br>Zooming...</div>
    <div id="map"></div>
    <script>
        const map = new maplibregl.Map({
            container: 'map',
            // CENTER THIS ON YOUR DOWNLOADED CITY (Islamabad)
            center: [73.04, 33.68],
            zoom: 13, 
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
                        'paint': { 'background-color': '#050505' } // Black Space Color
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

        // Debugging: Show current zoom level
        map.on('move', () => {
            document.getElementById('info').innerHTML = 
                'Center: ' + map.getCenter().lng.toFixed(4) + ', ' + map.getCenter().lat.toFixed(4) + '<br>' +
                'Zoom: ' + map.getZoom().toFixed(2);
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
    tms_y = (2**z) - 1 - y
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?", (z, x, tms_y))
    tile = cursor.fetchone()
    conn.close()
    
    if tile:
        return Response(tile[0], mimetype='image/png')
    else:
        # Return 404 so the map knows to show the black background
        return "Tile not found", 404

if __name__ == '__main__':
    print("Starting Map Server...")
    print("Open your browser to: http://localhost:5000")
    app.run(port=5000, debug=False)