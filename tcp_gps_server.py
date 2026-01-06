#!/usr/bin/env python3
"""
Simple TCP Server for GPS Trackers
No Django dependencies - standalone
"""
import socket
import threading
import logging
import time
from datetime import datetime
import json
import os

device_imei_map = {}  # Store IP -> IMEI mapping
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data storage (simple file-based for now)
DATA_FILE = '/home/neo_track/gps_data.json'

def save_gps_data(gps_data):
    """Save GPS data to JSON file safely."""
    try:
        data_list = []

        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    content = f.read().strip()
                    if content:
                        data_list = json.loads(content)
            except json.JSONDecodeError:
                logger.warning("?? gps_data.json corrupted or empty, recreating file")
                data_list = []

        data_list.append(gps_data)

        if len(data_list) > 1000:
            data_list = data_list[-1000:]

        with open(DATA_FILE, 'w') as f:
            json.dump(data_list, f, indent=2)

        logger.info(
            f"Saved: {gps_data.get('imei', 'Unknown')} - "
            f"{gps_data.get('lat', 0)}, {gps_data.get('lon', 0)}"
        )

    except Exception as e:
        logger.error(f"Save error: {e}")

def parse_gps_data(data_str):
    """
    Parse GPS tracker data.
    Supports multiple formats:
    1. G17H format: ##,imei:123456789012345,A,...
    2. Simple format: imei,lat,lon,speed,timestamp
    3. JSON format
    """
    try:
        data_str = data_str.strip()
        
        # Try JSON format
        if data_str.startswith('{'):
            data = json.loads(data_str)
            return data
        
        # G17H format
        elif data_str.startswith('##'):
            parts = data_str.split(',')
            if len(parts) < 8:
                return None
            
            # Extract IMEI
            imei_part = parts[1]
            if 'imei:' in imei_part:
                imei = imei_part.split(':')[1]
            else:
                imei = imei_part
            
            # Parse coordinates (simplified)
            try:
                lat = float(parts[5]) / 100 if parts[4] == 'N' else -float(parts[5]) / 100
                lon = float(parts[7]) / 100 if parts[6] == 'E' else -float(parts[7]) / 100
            except:
                # Try alternate position
                lat = float(parts[3]) if len(parts) > 3 else 0
                lon = float(parts[4]) if len(parts) > 4 else 0
            
            return {
                'imei': imei,
                'lat': lat,
                'lon': lon,
                'speed': float(parts[8]) if len(parts) > 8 else 0,
                'timestamp': datetime.now().isoformat(),
                'raw': data_str
            }
        
        # CSV format: imei,lat,lon,speed
        elif ',' in data_str:
            parts = data_str.split(',')
            return {
                'imei': parts[0] if len(parts) > 0 else 'unknown',
                'lat': float(parts[1]) if len(parts) > 1 else 0,
                'lon': float(parts[2]) if len(parts) > 2 else 0,
                'speed': float(parts[3]) if len(parts) > 3 else 0,
                'timestamp': datetime.now().isoformat(),
                'raw': data_str
            }
        
        # Unknown format
        else:
            return {
                'imei': 'unknown',
                'raw': data_str,
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Parse error: {e} - Data: {data_str}")
        return None

def handle_client(client_socket, address):
    logger.info(f"New connection from {address}")
    
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            
            logger.info(f"?? Received {len(data)} bytes from {address}")
            
            # Parse binary GPS data (GT06 protocol)
            gps_data = parse_binary_gps(data)
            
            if gps_data:
                # Store IMEI from login packet
                if gps_data.get('type') == 'login' and gps_data.get('imei'):
                    device_imei_map[address] = gps_data['imei']
                    logger.info(f"? Device registered: {address} -> IMEI: {gps_data['imei']}")
                
                # Add IMEI to location packets if we know it
                if gps_data.get('type') == 'location' and gps_data.get('imei') == 'unknown':
                    if address in device_imei_map:
                        gps_data['imei'] = device_imei_map[address]
                
                # Save to file
                save_gps_data(gps_data)
                
                # Send ACK
                client_socket.send(b'LOAD\n')
                logger.info(f"? Data saved: {gps_data.get('type', 'unknown')}")
            else:
                logger.warning(f"?? Could not parse data from {address}")
                client_socket.send(b'LOAD\n')
                
    except Exception as e:
        logger.error(f"Client error {address}: {e}")
    finally:
        # Clean up when device disconnects
        if address in device_imei_map:
            del device_imei_map[address]
        client_socket.close()
        logger.info(f"Connection closed: {address}")

def parse_gt06_login(data):
    """Parse GT06 login packet."""
    try:
        # Login packet: 78 78 0D 01 <IMEI 8 bytes> <00 00 00 00> <CRC> 0D 0A
        if len(data) < 18:
            return None
            
        # Extract IMEI (8 bytes = 16 hex chars = 15 digits, first digit is 0)
        imei_bytes = data[4:12]
        
        # Convert BCD to decimal IMEI
        imei_hex = imei_bytes.hex()
        imei = imei_hex.lstrip('0')  # Remove leading zero
        
        logger.info(f"?? Device login IMEI: {imei}")
        
        return {
            "imei": imei,
            "type": "login",
            "protocol": "gt06",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Login parse error: {e}")
        return None

def parse_binary_gps(data_bytes):
    """Parse GT06/GT02 protocol binary GPS data."""
    try:
        hex_str = data_bytes.hex()
        
        # Check if it's GT06 protocol (starts with 0x78 0x78 or 0x79 0x79)
        if len(data_bytes) >= 10 and (data_bytes[0:2] == b'\x78\x78' or data_bytes[0:2] == b'\x79\x79'):
            return parse_gt06_protocol(data_bytes)
        
        return None
        
    except Exception as e:
        logger.error(f"Binary parse error: {e}")
        return None

def parse_gt06_location(data):
    """Parse GT06 GPS location packet - CORRECTED VERSION."""
    try:
        if len(data) < 40:
            return None
        
        # DEBUG: Print raw bytes
        print(f"\n?? RAW PACKET ANALYSIS (length: {len(data)}):")
        for i in range(min(30, len(data))):
            print(f"  Byte {i:2d}: 0x{data[i]:02x} ({data[i]:3d})")
        
        # Parse date/time (6 bytes: YY MM DD HH MM SS) - CORRECT
        year = data[4] + 2000
        month = data[5]
        day = data[6]
        hour = data[7]
        minute = data[8]
        second = data[9]
        print(f"  Time: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}")
        
        # GPS info is byte 10 - but check what's actually there
        gps_byte = data[10]
        print(f"  Byte 10 (GPS info): 0x{gps_byte:02x} = {gps_byte:08b}")
        
        # Some devices have different format. Let's check multiple possibilities:
        
        # POSSIBILITY 1: Standard GT06 format
        if gps_byte & 0x80:  # Bit 7 set = GPS fix
            gps_fix = True
            satellites = gps_byte & 0x0F
            lat_start = 11
            lon_start = 15
            speed_pos = 19
            course_pos = 20
            print(f"  Format: Standard GT06")
        else:
            # POSSIBILITY 2: Alternate format
            print(f"  Checking alternate format...")
            # Try to find where actual coordinates start
            for offset in [8, 9, 10, 11, 12]:
                if len(data) > offset + 20:
                    test_lat = int.from_bytes(data[offset:offset+4], 'big')
                    test_lon = int.from_bytes(data[offset+4:offset+8], 'big')
                    if -90000000 < test_lat < 90000000 and -180000000 < test_lon < 180000000:
                        print(f"  Found coordinates at offset {offset}")
                        lat_start = offset
                        lon_start = offset + 4
                        speed_pos = offset + 8
                        course_pos = offset + 9
                        gps_fix = True
                        satellites = 0  # Unknown in this format
                        break
        
        # Parse coordinates
        lat_raw = int.from_bytes(data[lat_start:lat_start+4], 'big')
        lon_raw = int.from_bytes(data[lon_start:lon_start+4], 'big')
        
        print(f"  Raw lat: {lat_raw} (bytes {lat_start}:{lat_start+4})")
        print(f"  Raw lon: {lon_raw} (bytes {lon_start}:{lon_start+4})")
        
        # Try different divisors
        divisors = [1800000.0, 3600000.0, 30000.0, 100000.0, 1000000.0, 10000.0]
        valid_coords = []
        
        for divisor in divisors:
            lat = lat_raw / divisor
            lon = lon_raw / divisor
            
            # Check if coordinates are valid
            if -90 <= lat <= 90 and -180 <= lon <= 180 and (abs(lat) > 0.0001 or abs(lon) > 0.0001):
                valid_coords.append((divisor, lat, lon))
                print(f"  Divisor {divisor:10.1f}: {lat:.6f}, {lon:.6f}")
        
        if valid_coords:
            # Use the most likely divisor (usually 1800000)
            divisor, latitude, longitude = valid_coords[0]
            print(f"  Using divisor: {divisor}")
        else:
            print(f"  ?? No valid coordinates found")
            latitude = 0.0
            longitude = 0.0
        
        # Parse speed
        if len(data) > speed_pos:
            speed = data[speed_pos]
            print(f"  Speed byte {speed_pos}: {speed} km/h")
        else:
            speed = 0
        
        # Parse course
        if len(data) > course_pos + 1:
            course_raw = int.from_bytes(data[course_pos:course_pos+2], 'big')
            course = course_raw / 10.0
            print(f"  Course bytes {course_pos}:{course_pos+2}: {course}°")
        else:
            course = 0.0
        
        timestamp = f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}"
        
        return {
            "imei": "unknown",
            "lat": latitude,
            "lon": longitude,
            "speed": speed,
            "course": course,
            "gps_fix": gps_fix,
            "satellites": satellites,
            "timestamp": timestamp,
            "type": "location",
            "protocol": "gt06",
            "raw_lat": lat_raw,
            "raw_lon": lon_raw
        }
        
    except Exception as e:
        print(f"? Parse error: {e}")
        return None

def parse_gt06_heartbeat(data):
    """Parse GT06 heartbeat packet."""
    logger.info("?? Heartbeat packet received")
    return {
        "imei": "unknown",
        "type": "heartbeat",
        "timestamp": datetime.now().isoformat(),
        "protocol": "gt06"
    }
def start_server(host='0.0.0.0', port=6789):
    """Start TCP server."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((host, port))
        server.listen(5)
        logger.info(f"? TCP Server started on {host}:{port}")
        logger.info(f"?? Data file: {DATA_FILE}")
        
        while True:
            client_socket, address = server.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, address)
            )
            client_thread.daemon = True
            client_thread.start()
            
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()