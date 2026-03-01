import os
import requests
import mercantile
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CONFIGURATION ---

# 1. GLOBAL BASE MAP (Zoom 0 to 9)
# This covers the whole planet at a decent "Atlas" quality.
# Size: Approx 5-10 GB.
GLOBAL_MAX_ZOOM = 9

# 2. HIGH-RES CITIES (Zoom 10 to 19)
# Add as many cities as you want here!
# Format: "City Name": [West, South, East, North]
CITIES = {
    "Islamabad": [72.7, 33.4, 73.3, 33.8],
    "New York": [-74.25, 40.5, -73.7, 40.9],
    "London": [-0.5, 51.3, 0.3, 51.7],
    # You can add more cities here...
}
CITY_MAX_ZOOM = 19

# 3. Output folder
OUTPUT_DIR = "output_satellite_tiles"
TILE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

def download_tile(tile):
    z, x, y = tile.z, tile.x, tile.y
    folder_path = f"{OUTPUT_DIR}/{z}/{x}"
    os.makedirs(folder_path, exist_ok=True)
    file_path = f"{folder_path}/{y}.png"
    
    if os.path.exists(file_path):
        return None 

    url = TILE_URL.format(z=z, y=y, x=x)
    headers = {"User-Agent": "OfflineMapBuilder/1.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(response.content)
            return True
        return False
    except:
        return False

def main():
    print("--- STARTING SMART WORLD DOWNLOAD ---")
    
    all_tiles = []

    # PHASE 1: The Whole World (Low Res)
    print(f"Calculating Global Base Map (Zoom 0-{GLOBAL_MAX_ZOOM})...")
    for z in range(0, GLOBAL_MAX_ZOOM + 1):
        tiles = list(mercantile.tiles(-180, -85, 180, 85, z))
        all_tiles.extend(tiles)
        print(f"Zoom {z}: {len(tiles)} tiles (Global)")

    # PHASE 2: Specific Cities (High Res)
    print(f"\nCalculating High-Res Cities (Zoom {GLOBAL_MAX_ZOOM+1}-{CITY_MAX_ZOOM})...")
    for city_name, bbox in CITIES.items():
        print(f"Processing {city_name}...")
        for z in range(GLOBAL_MAX_ZOOM + 1, CITY_MAX_ZOOM + 1):
            tiles = list(mercantile.tiles(bbox[0], bbox[1], bbox[2], bbox[3], z))
            all_tiles.extend(tiles)
            print(f"  Zoom {z}: {len(tiles)} tiles")

    total = len(all_tiles)
    print(f"\nTotal tiles to download: {total}")
    print("Starting high-speed download... (This will take hours/days depending on your list)")

    count = 0
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(download_tile, t): t for t in all_tiles}
        
        for future in as_completed(futures):
            count += 1
            if count % 1000 == 0:
                print(f"Progress: {count} / {total} tiles ({round(count/total*100, 2)}%)")

    print("\nDownload Complete!")

if __name__ == "__main__":
    main()