import machine
import utime
import struct
import time


class MoistureSensor:
    def __init__(self, pin=26):
        """Initialize the moisture sensor on the given GPIO pin."""
        self.adc = machine.ADC(pin)  # Initialize ADC on the provided pin
        self.DRY_VALUE = 54500  # ADC reading when the sensor is dry
        self.WET_VALUE = 22500  # ADC reading when the sensor is wet

    def read_moisture(self):
        """Read the moisture level and calculate moisture percentage."""
        retries = 5

        moisture_value = self.adc.read_u16()  # Read ADC value (0-65535)
        # Convert to voltage (optional for debugging)
        # voltage = moisture_value * 3.3 / 65535

        for _ in range(retries):
            try:
                # Convert ADC value to moisture percentage
                if moisture_value > self.DRY_VALUE:
                    moisture_percentage = 0
                elif moisture_value < self.WET_VALUE:
                    moisture_percentage = 100
                else:
                    moisture_percentage = 100 - ((moisture_value - self.WET_VALUE) /
                                                 (self.DRY_VALUE - self.WET_VALUE)
                                                 * 100)

                return moisture_value, moisture_percentage
            except Exception as e:
                print("Error reading DHT11:", str(e))
                time.sleep(1)  # Wait a second before retrying
        return None, None

    def display_moisture(self):
        """Display the moisture level, voltage, and moisture percentage."""
        moisture_value, moisture_percentage = self.read_moisture()

        if moisture_value is not None and moisture_percentage is not None:

            print(f"Moisture Level: {moisture_value}")

    def get_moisture_percentage_binary(self):
        """Return the moisture percentage as binary data."""
        _, moisture_percentage = self.read_moisture()
        if moisture_percentage is not None:
            # Pack the moisture percentage into binary (as a signed 16-bit integer)
            return struct.pack("h", int(moisture_percentage))
        return None


if __name__ == "__main__":
    # Initialize the sensor (using default pin 26)
    moisture_sensor = MoistureSensor(pin=26)

    try:
        while True:
            moisture_sensor.display_moisture()
            utime.sleep(1)  # Delay for the next reading
    except KeyboardInterrupt:
        print("\n*** Moisture Sensor Stopped ***")
