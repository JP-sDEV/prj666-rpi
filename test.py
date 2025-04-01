import socket
import ubinascii
import urandom
import os
import utime
from components.dht11 import DHTSensor
from components.moisture import MoistureSensor

dht_sensor = DHTSensor(pin=1)
moisture_sensor = MoistureSensor(pin=26)

temp_humidity_binary = dht_sensor.get_binary_data()
moisture_binary = moisture_sensor.get_moisture_percentage_binary()

class WebSocketClient:
    def __init__(self, server_ip, port):
        self.server_ip = server_ip
        self.port = port
        self.sock = None

    def generate_websocket_key(self):
        """Generates a base64-encoded 16-byte key for the WebSocket handshake."""
        random_bytes = bytearray()
        for _ in range(16):
            random_bytes.append(urandom.getrandbits(8))
        return ubinascii.b2a_base64(random_bytes).decode('utf-8').strip()

    def websocket_send(self, message):
        """Encodes and sends a WebSocket TEXT frame with masking (required for clients)."""
        msg_bytes = message.encode('utf-8')
        payload_len = len(msg_bytes)
        
        # Generate a random 4-byte masking key
        masking_key = bytearray([
            urandom.getrandbits(8),
            urandom.getrandbits(8),
            urandom.getrandbits(8),
            urandom.getrandbits(8)
        ])
        
        # Build the frame header
        header = bytearray()
        header.append(0b10000001)  # FIN + Text frame
        
        # Second byte: MASK (1, required for clients) + payload length
        if payload_len <= 125:
            header.append(0b10000000 | payload_len)  # Set MASK bit (0x80)
        elif payload_len <= 65535:
            header.append(0b10000000 | 126)  # MASK + len=126
            header.extend((payload_len >> 8) & 0xFF)
            header.extend(payload_len & 0xFF)
        else:
            raise ValueError("Message too long")
        
        # Add masking key to header
        header.extend(masking_key)
        
        # Mask the payload (XOR each byte with masking_key[i % 4])
        masked_payload = bytearray()
        for i in range(payload_len):
            masked_payload.append(msg_bytes[i] ^ masking_key[i % 4])
        
        # Combine and send
        frame = bytes(header) + masked_payload
        self.sock.send(frame)

    def websocket_send_ping(self):
        """Sends a WebSocket PING frame to the server with masking."""
        # WebSocket PING frame opcode is 0x89, with a payload length of 0
        payload_len = 0
        
        # Generate a random 4-byte masking key
        masking_key = bytearray([
            urandom.getrandbits(8),
            urandom.getrandbits(8),
            urandom.getrandbits(8),
            urandom.getrandbits(8)
        ])
        
        # Construct the WebSocket frame header
        frame_header = bytearray([0x89])  # PING opcode (0x89)
        
        # Add the payload length with the masking bit set (0x80)
        frame_header.append(0x80 | payload_len)
        
        # Add the masking key
        frame_header.extend(masking_key)
        
        # No payload for the ping frame, so we send an empty payload
        frame = bytes(frame_header)  # The full frame is just the header (masked)
        
        # Send the frame
        self.sock.send(frame)
        print("Ping frame sent with masking.")

    def websocket_handshake(self):
        """Perform WebSocket handshake with the server."""
        ws_key = self.generate_websocket_key()

        handshake_request = (
            "GET / HTTP/1.1\r\n"
            "Host: {ip}:{port}\r\n"
            "Connection: Upgrade\r\n"
            "Upgrade: websocket\r\n"
            "Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "Origin: http://{ip}\r\n"
            "\r\n"
        ).format(ip=self.server_ip, port=self.port, key=ws_key)
        
        print("Handshake:", handshake_request)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.server_ip, self.port))
            self.sock.send(handshake_request.encode())

            response = self.sock.recv(1024)
            print("Response:", response)

            if b"101 Switching Protocols" in response:
                print("WebSocket handshake successful!")
                i = 0 
                # Send a message after successful handshake
                self.websocket_send("{i}: Hello from Raspberry Pi Pico!".format(i = i))
                
                last_ping_time = utime.ticks_ms()  # Track last ping time
                while True:
                    i += 1
                    current_time = utime.ticks_ms()
                    
                    # Send a ping every 60 seconds
                    if utime.ticks_diff(current_time, last_ping_time) >= 5000:
                        self.websocket_send_ping()
                        print("Ping sent")
                        last_ping_time = current_time
                    
                    # Wait for a pong (if any) or handle timeouts
                    try:
                        reply = self.sock.recv(1024)
                        if reply:
                            print("Received:", reply)
                            # Check if it's a Pong message (0x8A)
                            if reply[0] == 0x8A:
                                print("Pong received")
                    except OSError:
                        print("Timeout waiting for pong")
                        # Optionally handle timeout (e.g., reconnect or close)
                    
                    utime.sleep(1)  # Avoid busy-waiting
            else:
                print("WebSocket handshake failed.")

        except Exception as e:
            print("Error:", e)


# Usage
ws_client = WebSocketClient("10.0.0.176", 3000)
ws_client.websocket_handshake()
