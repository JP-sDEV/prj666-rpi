async def get_sensor_data(request):
    # Simulated sensor data
    sensor_value = {"temperature": 22.5, "humidity": 60}
    return {"status": "success", "data": sensor_value}

async def update_sensor_data(request):
    data = request.json
    print("Received Sensor Data:", data)
    return {"status": "success", "message": "Sensor data updated"}
