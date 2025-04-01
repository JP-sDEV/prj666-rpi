import socket
import ubinascii
import urandom
import ujson
import uasyncio as asyncio
from microdot.microdot import Microdot, Response


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

    async def websocket_send_ping(self):
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
        
    async def ping_every_10_seconds(self):
        """Send a WebSocket ping every 10 seconds."""
        while self.sock:
            await self.websocket_send_ping()  # Send ping frame
            await asyncio.sleep(10)  # Wait for 10 seconds


    async def websocket_handshake(self):
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

        if self.sock is not None:
            raise Exception("Socket already open.")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.sock.connect((self.server_ip, self.port))
            self.sock.send(handshake_request.encode())

            response = await self.non_blocking_recv(1024)

            if response:
                print("Response:", response)

                if b"101 Switching Protocols" in response:
                    print("WebSocket handshake successful!")
                    
                    asyncio.create_task(self.ping_every_10_seconds())
                else:
                    print("Failed WebSocket handshake response:", response)
            else:
                print("No response received.")

        except Exception as e:
            print("Error:", e)

    async def non_blocking_recv(self, bufsize):
        """Non-blocking receive with error handling and handling pong."""
        try:
            if self.sock:
                data = self.sock.recv(bufsize)
                if data:
                    if data[0] == 0x8A:  # PONG frame (opcode 0x8A)
                        print("Pong received from server")
                    return data
                else:
                    print("No data received.")
                    return None
            else:
                print("Socket is not initialized.")
                return None
        except Exception as e:
            print("Error receiving data:", e)
            return None


# Initialize the WebSocket client
ws_manager = WebSocketClient("10.0.0.176", 3000)


async def start_socket(request):
    try:
        data = ujson.loads(request.body)
        ws_url = data.get('websocket_url')
        if not ws_url:
            return Response(ujson.dumps({"error": "WebSocket URL not provided"}))
        asyncio.create_task(ws_manager.websocket_handshake())
        return Response(ujson.dumps({"message": "Connecting to " + ws_url}))
    except Exception as e:
        return Response(ujson.dumps({"error": str(e)}))
