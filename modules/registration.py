async def check_status(request):
    return {"status": "Device registered"}

async def register_device(request):
    data = request.json
    print("Registering Device:", data)
    return {"status": "success", "message": "Device registered"}
