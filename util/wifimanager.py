import network
import socket
import time
from util.sdcard import SDCardManager


class WiFiManager:
    WIFI_CONFIG_PATH = "wifi_config.txt"
    AP_SSID = "Pico-Setup"
    AP_PASSWORD = "12345678"

    def __init__(self):
        self.ssid = None
        self.password = None
        self.sd_card = SDCardManager()
        self.wlan = network.WLAN(network.STA_IF)  # WiFi client mode
        self.ap = network.WLAN(network.AP_IF)  # Access Point mode

    def turn_on_wifi(self):
        self.wlan.active(True)


    def save_wifi_config(self, ssid, password):
        """Save WiFi credentials in plain text format."""
        try:
            self.ssid = ssid
            self.password = password
            creds = f"{ssid}\n{password}\n"

            with open(self.WIFI_CONFIG_PATH, "w") as f:
                f.write(creds)

            # self.sd_card.write_data(self.WIFI_CONFIG_FILE, creds)
            print("WiFi credentials saved.")

        except Exception as e:
            print(f"Error occured when saving WiFi credentials: {e}")

    def load_wifi_config(self):
        """Load WiFi credentials from internal storage."""
        try:
            with open(self.WIFI_CONFIG_PATH, "r") as f:
                lines = f.readlines()

            if len(lines) >= 2:
                self.ssid = lines[0].strip()
                self.password = lines[1].strip()
                print(f"Loaded WiFi SSID: {self.ssid}")
                return self.ssid, self.password

            print("WiFi config file is invalid.")
            return None, None

        except Exception as e:
            print(f"Error occurred while loading WiFi credentials: {e}")
            return None, None

    def connect_to_wifi(self):
        """Attempts to connect to WiFi using stored credentials."""
        try:
            print("WiFi active status:", self.wlan.active())
            ssid, password = self.load_wifi_config()
            if not ssid or not password:
                print("No WiFi credentials found. Starting setup mode...")
                # self.setup_page()
                return False

            if (not self.wlan.active()):
                self.wlan.active(False)
                time.sleep(2)
                print("Turning on WiFi...")
                self.wlan.active(True)

            print(f"Connecting to {ssid}...")

            for attempt in range(10):  # Wait for connection (10 attempts)
                self.wlan.connect(ssid, password)
                if self.wlan.isconnected():
                    print("Connected successfully!")
                    print("IP Address:", self.wlan.ifconfig()[0])
                    return True
                print(f"Waiting for connection... Attempt {attempt + 1}/10")
                time.sleep(2)

            print("Failed to connect to WiFi. Starting Starting setup mode...")
            # self.setup_page()
            return False

        except Exception as e:
            print(f"Failed to connect to WiFi. Starting setup mode...: {e}")
            # self.setup_page()
            return False

    def setup_page(self):
        """Starts WiFi Access Point and a simple HTTP server for setup."""
        print("Starting WiFi Setup Mode...")

        if (self.ap.active()):
            self.ap.active(False)  # Disable AP if active
            time.sleep(1)          # Allow time to shut down
        self.ap.active(True)   # Re-enable AP

        self.ap.config(essid=self.AP_SSID, password=self.AP_PASSWORD)

        print("AP Active:", self.ap.active())
        print("AP Config:", self.ap.ifconfig())

        print(f"Connect to {self.AP_SSID} and open http://192.168.4.1")

        # Start simple web server
        addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
        server = socket.socket()
        server.bind(addr)
        server.listen(1)

        html_page = """\n        <html>
        <head><title>WiFi Setup</title></head>
        <body>
        <h2>Enter WiFi Credentials</h2>
        <form action="/" method="POST" enctype="application/x-www-form-urlencoded">
            SSID: <input type="text" name="ssid"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Save">
        </form>
        </body></html>
        """

        while True:
            conn, addr = server.accept()
            print(f"Client connected from {addr}")
            request = conn.recv(1024).decode("utf-8")
            print("Received:", request)

            if "POST" in request:
                headers, body = request.split("\r\n\r\n", 1)

                # Extract Content-Length and ensure full body is read
                content_length = 0
                for line in headers.splitlines():
                    if line.startswith("Content-Length:"):
                        content_length = int(line.split(":")[1].strip())
                        break

                while len(body) < content_length:
                    body += conn.recv(1024).decode("utf-8")

                print(f"Full Body: {body}")

                # Manual form parsing
                def parse_form_data(body):
                    params = {}
                    for pair in body.split("&"):
                        if "=" in pair:
                            key, value = pair.split("=", 1)
                            key = key.replace("+", " ")  # Handle '+' as space
                            value = value.replace("+", " ")  # Handle '+' as space
                            params[key] = value
                    return params

                params = parse_form_data(body)
                ssid = params.get("ssid")
                password = params.get("password")

                print(f"Parsed SSID: {ssid}, Password: {password}")

                self.save_wifi_config(ssid, password)

                # Response after saving WiFi credentials
                success_page = """\n                <html>
                <head><title>Success</title></head>
                <body>
                <h2>WiFi Credentials Saved!</h2>
                <p>Your device will now attempt to connect.</p>
                <p>If it fails, restart the device and try again.</p>
                </body></html>
                """

                conn.send("HTTP/1.1 200 OK\nContent-Type: text/html\n\n" + success_page)
                conn.close()
                break  # Exit loop after saving credentials

            else:
                conn.send("HTTP/1.1 200 OK\nContent-Type: text/html\n\n" + html_page)
                conn.close()