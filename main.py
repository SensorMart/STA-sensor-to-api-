from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sensor_data.data_reader import SensorDataReader
import asyncio

app = FastAPI()
templates =  Jinja2Templates(directory= "templates")

#initialize the sensor data reader
sensor_data_reader = SensorDataReader(port='COM7', baud_rate='115200')

@app.get("/",response_class=HTMLResponse)
async def get_webpage(request: Request):
    return templates.TemplateResponse("index.html",{"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = sensor_data_reader.get_data()
        if data:
            await websocket.send_text(data)
        await asyncio.sleep(0.005)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host ="localhost",port = 8000)
