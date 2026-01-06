#!/usr/bin/env python3
"""
COMPLETE WORKING GT06 GPS Server for Bangladesh
Coordinates verified with SMS: Lat:N23.867976,Lon:E90.390219
"""
import socket
import threading
import json
import os
from datetime import datetime
import logging
    

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

# Configure Django when running this script standalone so models can be imported
import sys
import django

# Ensure project root is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neo_track.settings')
django.setup()

from vehicles.models import Vehicle, VehicleLocation

# Storage
device_imei = {}  # ip -> imei mapping
DATA_FILE = '/home/neo_track/gps_data.json'

def save_gps_data(data):
    """Save GPS data to JSON file."""
    try:
        all_data = []
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    if os.path.getsize(DATA_FILE) > 0:
                        all_data = json.load(f)
            except:
                all_data = []
        
        all_data.append(data)
        if len(all_data) > 1000:
            all_data = all_data[-1000:]
        
        with open(DATA_FILE, 'w') as f:
            json.dump(all_data, f, indent=2)
        
        if data.get('type') == 'location':
            lat = data.get('lat', 0)
            lon = data.get('lon', 0)
            imei = data.get('imei', 'unknown')
            speed = data.get('speed', 0)
            satellites = data.get('satellites', 0)
            timestamp = data.get('time', datetime.now().isoformat())
            
            log.info(f"? SAVED LOCATION: {lat:.6f}, {lon:.6f}")
            
            # Save to Django database
            save_to_database(imei, lat, lon, speed, satellites, timestamp)
        else:
            log.info(f"?? SAVED: {data.get('type', 'data')}")
        
        return True
    except Exception as e:
        log.error(f"Save error: {e}")
        return False

def save_to_database(imei, lat, lon, speed, satellites, timestamp_str):
    """Save GPS location to Django database."""
    try:
        # Try to find the vehicle by IMEI
        vehicle = Vehicle.objects.filter(imei=imei).first()
        
        if not vehicle:
            # If not found, try with "unknown" IMEI (your existing logic)
            vehicle = Vehicle.objects.filter(imei="unknown").first()
        
        if vehicle:
            # Parse timestamp string to datetime object
            try:
                if 'T' in timestamp_str:
                    time_obj = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")
                else:
                    # Try other formats if needed
                    time_obj = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                time_obj = datetime.now()
            
            # Create VehicleLocation record
            VehicleLocation.objects.create(
                vehicle=vehicle,
                lat=lat,
                lon=lon,
                speed=speed,
                sat=satellites,
                time=time_obj
            )
            
            log.info(f"? Database: Location saved for vehicle: {vehicle.reg_no} (IMEI: {imei})")
            return True
        else:
            log.warning(f"? Database: No vehicle found with IMEI: {imei}")
            return False
            
    except Exception as e:
        log.error(f"Database save error: {e}")
        return False

def parse_gt06_packet(data):
    """Parse GT06 protocol packet."""
    try:
        if len(data) < 10:
            return None
        
        # Check start bytes
        if data[0:2] not in [b'\x78\x78', b'\x79\x79']:
            return None
        
        length = data[2]
        protocol = data[3]
        
        log.info(f"?? Packet: Protocol=0x{protocol:02x}, Length={length}")
        
        # Parse based on protocol
        if protocol == 0x01:  # Login
            return parse_login_packet(data)
        elif protocol in [0x12, 0x22, 0x26]:  # GPS location only
            return parse_location_packet(data, protocol)
        elif protocol == 0x20:  # LBS packet — DO NOT SAVE
            log.info("📡 LBS packet ignored (0x20)")
            return None
        elif protocol == 0x13:  # Heartbeat
            return {"type": "heartbeat", "time": datetime.now().isoformat()}
        elif protocol == 0x16:  # Alarm
            return parse_alarm_packet(data)
        elif protocol == 0x24:  # Status
            return {"type": "status", "protocol": "0x24", "time": datetime.now().isoformat()}
        elif protocol == 0x20:  # Additional data or LBS location
            return parse_protocol_20_packet(data)
        else:
            log.warning(f"?? Unknown protocol: 0x{protocol:02x}")
            return None
            
    except Exception as e:
        log.error(f"Parse error: {e}")
        return None

def parse_login_packet(data):
    """Parse login packet (protocol 0x01)."""
    try:
        if len(data) < 18:
            return None
        
        # IMEI is bytes 4-11 (8 bytes BCD)
        imei_bytes = data[4:12]
        
        # Convert BCD to string
        imei = ""
        for b in imei_bytes:
            imei += f"{b:02d}"
        
        imei = imei.lstrip('0')
        
        log.info(f"?? LOGIN - IMEI: {imei}")
        
        return {
            "imei": imei,
            "type": "login",
            "time": datetime.now().isoformat(),
            "protocol": "0x01"
        }
        
    except Exception as e:
        log.error(f"Login parse error: {e}")
        return None

def parse_location_packet(data, protocol):
    """Parse GPS location packet - VERIFIED with SMS coordinates."""
    try:
        # Protocol 0x22 has offset 4, others might differ
        # if protocol == 0x22:
        #     offset = 4
        #     if len(data) < offset + 25:
        #         return None
        # else:
        #     offset = 0
        #     if len(data) < 40:
        #         return None

        offset = 4
        if len(data) < offset + 20:
            return None
        
        # Parse date/time (YY MM DD HH MM SS)
        year = 2000 + data[offset]
        month = data[offset + 1]
        day = data[offset + 2]
        hour = data[offset + 3]
        minute = data[offset + 4]
        second = data[offset + 5]
        
        # GPS info
        gps_byte = data[offset + 6]
        gps_fix = (gps_byte & 0x80) != 0
        satellites = gps_byte & 0x0F
        if not gps_fix:
            log.warning("📡 No GPS fix — packet ignored")
            return None
        
        # Coordinates
        lat_raw = int.from_bytes(data[offset + 7:offset + 11], 'big')
        lon_raw = int.from_bytes(data[offset + 11:offset + 15], 'big')
        
        # Speed and course
        speed = int.from_bytes(data[offset + 15:offset + 17], 'big')
        course_raw = int.from_bytes(data[offset + 17:offset + 19], 'big')
        course = course_raw / 10.0
        
        # ? CORRECT COORDINATE CALCULATION
        # Verified with SMS: Lat:N23.867976 = lat_raw/1800000
        DIVISOR = 1800000.0
        
        latitude = lat_raw / DIVISOR
        longitude = lon_raw / DIVISOR
        
        timestamp = f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}"
        
        # Validate for Bangladesh
        if 20 < latitude < 27 and 88 < longitude < 93:
            log.info(f"?? GPS Bangladesh: {latitude:.6f}N, {longitude:.6f}E")
        else:
            log.warning(f"?? Unexpected coordinates: {latitude:.6f}, {longitude:.6f}")
        return {
            "imei": "unknown",
            "lat": latitude,
            "lon": longitude,
            "speed": speed,
            "course": course,
            "satellites": satellites,
            "gps_fix": gps_fix,
            "time": timestamp,
            "type": "location",
            "protocol": f"0x{protocol:02x}",
            "verified": True
        }
        
    except Exception as e:
        log.error(f"Location parse error: {e}")
        return None
    
def parse_protocol_20_packet(data):
    """Parse protocol 0x20 packet (often LBS location or additional data)."""
    try:
        if len(data) < 10:
            return None
        
        log.info(f"?? Protocol 0x20 packet received, length: {len(data)}")
        
        # Protocol 0x20 often contains LBS (cell tower) location data
        # You can parse it or just acknowledge it
        return {
            "type": "protocol_20",
            "time": datetime.now().isoformat(),
            "protocol": "0x20",
            "raw_length": len(data)
        }
        
    except Exception as e:
        log.error(f"Protocol 0x20 parse error: {e}")
        return None
    
def parse_alarm_packet(data):
    """Parse alarm packet (protocol 0x16)."""
    try:
        alarm_type = data[4] if len(data) > 4 else 0
        log.info(f"?? ALARM: Type=0x{alarm_type:02x}")
        
        return {
            "type": "alarm",
            "alarm_code": alarm_type,
            "time": datetime.now().isoformat(),
            "protocol": "0x16"
        }
        
    except Exception as e:
        log.error(f"Alarm parse error: {e}")
        return None

def send_acknowledgment(sock, protocol):
    """Send appropriate ACK."""
    try:
        if protocol in [0x01, 0x12, 0x13, 0x16, 0x20, 0x22, 0x24, 0x26]:
            ack = b'\x78\x78\x05\x01\x00\x00\x00\x00\x0D\x0A'
        else:
            ack = b'OK\n'
        
        sock.send(ack)
        log.info(f"?? ACK sent for protocol 0x{protocol:02x}")
        
    except Exception as e:
        log.error(f"ACK error: {e}")

def handle_client_connection(sock, addr):
    """Handle device connection."""
    ip, port = addr
    log.info(f"?? CONNECTED: {ip}:{port}")
    
    try:
        while True:
            data = sock.recv(1024)
            if not data:
                break
            
            # Parse packet
            packet = parse_gt06_packet(data)
            
            if packet:
                # Store IMEI from login
                if packet.get('type') == 'login' and packet.get('imei'):
                    device_imei[ip] = packet['imei']
                    log.info(f"? Registered: {ip} -> {packet['imei']}")
                
                # Add IMEI to location packets
                if packet.get('type') == 'location' and ip in device_imei:
                    packet['imei'] = device_imei[ip]
                
                # Save data
                save_gps_data(packet)
                
                # Send ACK
                protocol = data[3] if len(data) > 3 else 0
                send_acknowledgment(sock, protocol)
                
            else:
                # Unknown data
                log.warning(f"? Unknown data from {ip}")
                sock.send(b'OK\n')
                
    except ConnectionResetError:
        log.info(f"?? Connection reset by {ip}")
    except Exception as e:
        log.error(f"? Error: {e}")
    finally:
        if ip in device_imei:
            del device_imei[ip]
        sock.close()
        log.info(f"?? DISCONNECTED: {ip}")

def start_gps_server(host='0.0.0.0', port=6789):
    """Start GPS server."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((host, port))
        server.listen(5)
        log.info(f"?? GPS Server started on {host}:{port}")
        log.info(f"?? Data file: {DATA_FILE}")
        log.info("?? Coordinates verified with SMS: Lat:N23.867976,Lon:E90.390219")
        log.info("?? Waiting for device connections...")
        
        while True:
            client_sock, client_addr = server.accept()
            client_thread = threading.Thread(
                target=handle_client_connection,
                args=(client_sock, client_addr)
            )
            client_thread.daemon = True
            client_thread.start()
            
    except KeyboardInterrupt:
        log.info("?? Server stopping...")
    except Exception as e:
        log.error(f"? Server error: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("GT06 GPS SERVER - BANGLADESH")
    print("Coordinates verified with SMS data")
    print(f"Port: 6789 | Data: {DATA_FILE}")
    print("="*60 + "\n")
    
    start_gps_server()