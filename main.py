import uos
import network
import time
import struct
import urequests
from microdot.microdot import Microdot, asyncio
from modules.registration import check_status, register_device
from modules.usersocket import start_socket
from components.dht11 import DHTSensor
from components.moisture import MoistureSensor
from util.scheduler import AsyncScheduler
from util.wifimanager import WiFiManager
from util.registration import PicoRegistration
from util.sdcard import SDCardManager

IP_ADDRESS = "10.0.0.176"
RASPBERRY_PI_ID = 123  # Example ID
SERVER_URL = f"http://{IP_ADDRESS}:3000"
REGISTRATION_FILE = "registered.txt"
DATA_FILE = "sensor_data.bin"

wifi_manager = WiFiManager()
pico_registration = PicoRegistration(SERVER_URL)
sd_card = SDCardManager()

dht_sensor = DHTSensor(pin=1)
moisture_sensor = MoistureSensor(pin=26)


# Create Microdot app
app = Microdot()

# Register routes manually
app.get('/api/registration/status')(check_status)
app.post('/api/registration/register')(register_device)


# Route for opening WebSocket connection
@app.route('/api/device/socket', methods=["POST"])
async def open_socket(request):
    await start_socket(request)

# # Route for closing WebSocket connection
# @app.route('/api/device/close_socket', methods=["POST"])
# async def close_socket_route(request):
#     return await close_socket(request)

async def wait_for_wifi_connection():
    """Async function to wait for Wi-Fi connection."""
    print("On Boot Process...")
    wifi_manager.turn_on_wifi()

    while not wifi_manager.connect_to_wifi():
        print("Wi-Fi connection failed. Starting setup mode...")
        wifi_manager.setup_page()
        await asyncio.sleep(2) 
        print("Retrying Wi-Fi connection...")

    print("Wi-Fi connected successfully!")

async def wait_for_device_registration():
    """Checks registration and exits early when registered."""
    for _ in range(10):  # Retry up to 10 times
        try:
            if not file_exists(REGISTRATION_FILE):  # Check file existence in MicroPython
                print(f"{REGISTRATION_FILE} does not exist. Assuming unregistered.")
                await pico_registration.start()
            else:
                registration_status = pico_registration.sd_card.read_file(REGISTRATION_FILE)
                if registration_status and registration_status.strip() == "registered":
                    print("Device is registered. Proceeding to data collection...")
                    return  # Exit function early

                print("Device not registered. Entering registration mode...")
                await pico_registration.start()

        except Exception as e:
            print(f"Error reading registration file: {e}")
            await pico_registration.start()

        await asyncio.sleep(30)  # Check registration every 30s
    
    print("Max retries reached. Proceeding without registration.")

async def collect_and_store_data():
    """Read sensors, format binary data, and save to SD card."""
    temp_humidity_binary = dht_sensor.get_binary_data()
    moisture_binary = moisture_sensor.get_moisture_percentage_binary()

    if temp_humidity_binary is None or moisture_binary is None:
        print("Sensor read failed.")
        return

    timestamp = int(time.time())
    print("Timestamp: " + str(timestamp))

    # Unpack temperature and humidity from binary (assuming signed 16-bit int format)
    temperature, humidity = struct.unpack("hh", temp_humidity_binary)

    # Unpack moisture as a signed 16-bit integer
    (moisture,) = struct.unpack("h", moisture_binary)

    # Ensure moisture is an integer and within valid range for 'B' (0-255)
    if not (0 <= moisture <= 255):
        print(f"Invalid moisture value: {moisture}")
        return

    # Now repack everything into the final binary format
    binary_data = struct.pack("<IffBI", RASPBERRY_PI_ID, float(temperature),
                              float(humidity), moisture, timestamp)

    sd_card.write_data(DATA_FILE, binary_data)
    print("Data saved to SD card.")

    
async def upload_data():
    """Upload stored binary file to the server."""
    binary_data = sd_card.read_data(DATA_FILE)

    if binary_data:
        headers = {"Content-Type": "application/octet-stream"}
        response = urequests.post(f"{SERVER_URL}/api/device/data/{RASPBERRY_PI_ID}", data=binary_data, headers=headers)

        if response.status_code == 201:
            print("Upload successful, deleting file...")
            sd_card.delete_file(DATA_FILE)
        else:
            print("Upload failed:", response.status_code)

        response.close()
    else:
        print("No data to upload.")


def file_exists(filepath):
    """Check if a file exists in MicroPython using uos."""
    try:
        uos.stat(filepath)  # This will raise an error if the file doesn't exist
        return True
    except OSError:
        return False


# Create schedulers
scheduler1 = AsyncScheduler(5, collect_and_store_data)
scheduler2 = AsyncScheduler(10, upload_data)

async def onboot():
    """Async boot function to ensure Wi-Fi is connected before starting the server."""
    # First, ensure Wi-Fi is connected and device is registered
    await wait_for_wifi_connection()
    await wait_for_device_registration()

    # Now, schedule sensor readings and uploads without blocking the Microdot server
    # asyncio.create_task(scheduler1.run())  # Collect data every 5 seconds
    # asyncio.create_task(scheduler2.run())  # Upload data every 10 seconds

    # Run Microdot server concurrently
    await app.run(port=80)  # Runs Microdot server

# Run the onboot function asynchronously
asyncio.run(onboot())
