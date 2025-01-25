import machine
import dht
import time

# GPIO 1 (i.e. pin 2)
dht_pin = machine.Pin(1)
dht_sensor = dht.DHT11(dht_pin)

while True:
    try:
        dht_sensor.measure()

        temperature_celsius = dht_sensor.temperature()
        humidity_percent = dht_sensor.humidity()

        print("Temperature: {:.2f} °C".format(temperature_celsius))
        print("Humidity: {:.2f} %".format(humidity_percent))

    except KeyboardInterrupt:
        break

    except Exception as e:
        print("Error reading DHT11:", str(e))

    time.sleep(1)

print("*** DHT11 Off ***")
