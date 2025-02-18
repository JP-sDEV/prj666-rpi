import struct
import time
import urequests
from components.dht11 import DHTSensor
from components.moisture import MoistureSensor
from components.sdcard import SDCardManager
from util.scheduler import Scheduler
IP_ADDRESS = "0.0.0.0"
DATA_FILE = "sensor_data.bin"
SERVER_URL = "http://" + IP_ADDRESS + ":3000/api/raspberrypi/data"
RASPBERRY_PI_ID = 12345  # Example ID
READ_INTERVAL = 5
UPLOAD_INTERVAL = 10

# Initialize components
dht_sensor = DHTSensor(pin=1)
moisture_sensor = MoistureSensor(pin=26)
sd_card = SDCardManager()


def collect_and_store_data():
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


def upload_data():
    """Upload stored binary file to the server."""
    binary_data = sd_card.read_data(DATA_FILE)

    if binary_data:
        headers = {"Content-Type": "application/octet-stream"}
        response = urequests.post(SERVER_URL, data=binary_data, headers=headers)

        if response.status_code == 200:
            print("Upload successful, deleting file...")
            sd_card.delete_file(DATA_FILE)
        else:
            print("Upload failed:", response.status_code)

        response.close()
    else:
        print("No data to upload.")


# Create schedulers
sensor_scheduler = Scheduler(interval=READ_INTERVAL, task=collect_and_store_data,
                             run_on_start=True)
upload_scheduler = Scheduler(interval=UPLOAD_INTERVAL, task=upload_data)


def main_loop():
    """Main event loop."""
    try:
        while True:
            sensor_scheduler.run()
            upload_scheduler.run()
    except KeyboardInterrupt:
        print("\nStopping data collection...")
        sd_card.unmount()


# Run main loop
main_loop()
