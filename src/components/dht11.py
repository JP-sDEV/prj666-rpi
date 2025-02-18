import machine
import dht
import time
import struct


class DHTSensor:
    def __init__(self, pin):
        """Initialize the DHT11 sensor on the given GPIO pin."""
        self.dht_pin = machine.Pin(pin)
        self.dht_sensor = dht.DHT11(self.dht_pin)

    def read_sensor(self):
        """Read temperature and humidity from the sensor."""
        retries = 5
        for _ in range(retries):
            try:
                self.dht_sensor.measure()
                temperature_celsius = self.dht_sensor.temperature()
                humidity_percent = self.dht_sensor.humidity()
                return temperature_celsius, humidity_percent
            except Exception as e:
                print("Error reading DHT11:", str(e))
                time.sleep(1)  # Wait a second before retrying
        return None, None

    def get_binary_data(self):
        """Get temperature and humidity packed into a binary format."""
        temp, humidity = self.read_sensor()
        if temp is not None and humidity is not None:
            return struct.pack("hh", temp, humidity)
        return None

    def display_data(self):
        """Prints sensor readings in both decimal and binary formats."""
        temp, humidity = self.read_sensor()
        if temp is not None and humidity is not None:
            binary_data = struct.pack("hh", temp, humidity)
            print(machine.unique_id().hex())
            print("Binary Data:", binary_data)
            print("Hex:", binary_data.hex())
            print(f"Temperature: {temp:.2f} °C")
            print(f"Humidity: {humidity:.2f} %")
        else:
            print("Failed to read sensor data.")


if __name__ == "__main__":
    sensor = DHTSensor(pin=1)

    try:
        while True:
            sensor.display_data()
            time.sleep(1)  # Delay for next reading
    except KeyboardInterrupt:
        print("\n*** DHT11 Sensor Stopped ***")
