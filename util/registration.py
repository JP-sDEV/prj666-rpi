import ubinascii
import urequests
import machine
import uasyncio as asyncio
from util.wifimanager import WiFiManager
from util.sdcard import SDCardManager

REGISTRATION_FILE = "registered.txt"


class PicoRegistration:
    def __init__(self, server_url):
        self.registered = False
        self.device_id = "123"
        self.server_url = server_url
        self.wifi_manager = WiFiManager()
        self.sd_card = SDCardManager()

    def is_registered(self):
        return self.registered

    async def start(self):
        """Start the registration process asynchronously."""
        print("Starting Pico Registration...")

        # Ensure WiFi connection
        self.wifi_manager.turn_on_wifi()
        
        # Wait asynchronously for WiFi to connect
        while not self.wifi_manager.connect_to_wifi():
            print("WiFi not connected. Retrying...")
            await asyncio.sleep(2)  # Non-blocking delay before retrying

        print("WiFi connected successfully!")
        await self.register_device()  # Call the async register function

    async def check_server_registration(self):
        """Check with the server asynchronously if the device is registered."""
        try:
            print(f"Checking registration with server at {self.server_url}...")
            response = urequests.get(f"{self.server_url}/api/device/status?device_id={self.device_id}")

            if response.status_code == 200:
                data = response.json()
                response.close()
                return data.get("registered", False)  # Expecting JSON like {"registered": true}
            
            print("Failed to check registration with the server.")
            response.close()
            return False

        except Exception as e:
            print(f"Error checking server registration: {e}")
            return False
        
    def check_local_registration(self):
        """Check if the device is registered locally."""
        try:
            file_content = self.sd_card.read_file(REGISTRATION_FILE)
            return file_content and file_content.strip() == "registered"
        except Exception as e:
            print("Error checking local registration:", e)
            return False  

    def persist_registration(self):
        """Save registration status to a file."""
        with open(REGISTRATION_FILE, "w") as file:
            file.write("registered")

    async def register_device(self):
        """Send device ID to the server for registration asynchronously."""
        try:
            print("Entering registration mode...")
            print("Checking registration status...")

            local_reg = self.check_local_registration()
            server_reg = await self.check_server_registration()  # Wait for server response

            # Check if already registered
            if local_reg and server_reg:
                print("Device is already registered both locally and on the server.")
                return

            # Sync local registration if needed
            if not local_reg and server_reg:
                print("Device registered on server but not locally. Updating local status...")
                self.persist_registration()
                self.registered = True
                return

            if local_reg and not server_reg:
                print("Device registered locally but not on the server. Attempting to register again...")

            # Register device with server
            payload = {"device_id": self.device_id, "mode": "device"}
            print(f"Sending registration payload: {payload}")

            response = urequests.post(f"{self.server_url}/api/device/register", json=payload)

            try:
                print(f"Server Response: {response.status_code}, {response.text}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.registered = True
                        print("Device successfully registered.")
                    else:
                        print("Registration timed out. User did not register the device.")
                else:
                    print("Registration failed.")
            finally:
                response.close()

        except Exception as e:
            print(f"Error during registration: {e}")

