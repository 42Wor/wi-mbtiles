#
import os
import requests
import mercantile
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CONFIGURATION ---
# 1. Your Region (West, South, East, North)
# Currently set to the Islamabad neighborhood you used before.
BBOX = [73.03, 33.67, 73.05, 33.69] 

# 2. DOWNLOAD EVERYTHING (From World View to Street View)
MIN_ZOOM = 0
MAX_ZOOM = 19

# 3. Output folder
OUTPUT_DIR = "output_satellite_tiles"

# Esri World Imagery (Best free high-res satellite data)
TILE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

def download_tile(tile):
    z, x, y = tile.z, tile.x, tile.y
    folder_path = f"{OUTPUT_DIR}/{z}/{x}"
    os.makedirs(folder_path, exist_ok=True)
    file_path = f"{folder_path}/{y}.png"
    
    # Skip if already exists
    if os.path.exists(file_path):
        return None # Silent skip to keep terminal clean

    url = TILE_URL.format(z=z, y=y, x=x)
    headers = {"User-Agent": "OfflineMapBuilder/1.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(response.content)
            return f"Downloaded Zoom {z}: {x}/{y}"
        else:
            return f"Failed {z}/{x}/{y} (Status {response.status_code})"
    except Exception as e:
        return f"Error {z}/{x}/{y}"

def main():
    print(f"--- PREPARING DOWNLOAD ---")
    print(f"Region: {BBOX}")
    print(f"Zoom Levels: {MIN_ZOOM} to {MAX_ZOOM}")
    
    all_tiles = []
    for z in range(MIN_ZOOM, MAX_ZOOM + 1):
        tiles = list(mercantile.tiles(BBOX[0], BBOX[1], BBOX[2], BBOX[3], z))
        all_tiles.extend(tiles)
        print(f"Zoom {z}: Found {len(tiles)} tiles")

    total = len(all_tiles)
    print(f"\nTotal tiles to download: {total}")
    print("Starting high-speed download... (Press Ctrl+C to stop)\n")

    count = 0
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(download_tile, t): t for t in all_tiles}
        
        for future in as_completed(futures):
            result = future.result()
            count += 1
            if result: # Only print if we actually downloaded something
                print(f"[{count}/{total}] {result}")
            elif count % 100 == 0:
                print(f"[{count}/{total}] ... skipping existing files ...")

    print("\nDownload Complete! You can now see every house and street.")

if __name__ == "__main__":
    main()