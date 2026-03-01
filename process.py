import sqlite3
import os

# --- CONFIGURATION ---
SOURCE_DIR = "output_satellite_tiles"
DB_NAME = "world.mbtiles"

def init_db():
    # Delete old DB if you want to start fresh, or keep it to append
    if os.path.exists(DB_NAME):
        print(f"Found existing {DB_NAME}. Appending new tiles...")
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Create MBTiles tables
    c.execute('CREATE TABLE IF NOT EXISTS tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob)')
    c.execute('CREATE UNIQUE INDEX IF NOT EXISTS tile_index on tiles (zoom_level, tile_column, tile_row)')
    c.execute('CREATE TABLE IF NOT EXISTS metadata (name text, value text)')
    
    # Standard Metadata
    c.execute('INSERT OR REPLACE INTO metadata (name, value) VALUES ("name", "My Offline World")')
    c.execute('INSERT OR REPLACE INTO metadata (name, value) VALUES ("format", "png")')
    conn.commit()
    conn.close()

def pack_tiles():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    print(f"Scanning {SOURCE_DIR} for images...")
    
    tiles_found = 0
    # Walk through the /z/x/y.png structure
    for z in os.listdir(SOURCE_DIR):
        z_path = os.path.join(SOURCE_DIR, z)
        if not os.path.isdir(z_path): continue
        
        for x in os.listdir(z_path):
            x_path = os.path.join(z_path, x)
            if not os.path.isdir(x_path): continue
            
            for y_file in os.listdir(x_path):
                if not y_file.endswith(".png"): continue
                
                y = y_file.replace(".png", "")
                
                # Convert to integers
                iz, ix, iy = int(z), int(x), int(y)
                
                # IMPORTANT: MBTiles uses TMS (flipped Y). 
                # We must flip the Y coordinate for the database.
                tms_y = (2**iz) - 1 - iy
                
                file_path = os.path.join(x_path, y_file)
                
                with open(file_path, "rb") as f:
                    tile_data = f.read()
                
                try:
                    c.execute('INSERT OR IGNORE INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)', 
                              (iz, ix, tms_y, tile_data))
                    tiles_found += 1
                except Exception as e:
                    print(f"Error at {iz}/{ix}/{iy}: {e}")

        print(f"Finished Zoom Level {z}...")
        conn.commit() # Save after every zoom level

    conn.close()
    print(f"\nSuccess! Packed {tiles_found} tiles into {DB_NAME}")

if __name__ == "__main__":
    init_db()
    pack_tiles()