from fastapi import FastAPI, WebSocket, Request ,HTTPException
from fastapi.responses import HTMLResponse ,JSONResponse
from fastapi.templating import Jinja2Templates
from sensor_data.data_reader import SensorDataReader
import asyncio
import json
import requests

app = FastAPI()
templates =  Jinja2Templates(directory= "templates")

#initialize the sensor data reader
sensor_data_reader = SensorDataReader(port='COM5', baud_rate='115200',queue_size=1000)

@app.get("/",response_class=HTMLResponse)
async def get_webpage(request: Request):
    return templates.TemplateResponse("index.html",{"request": request})

@app.websocket("/ws") 
async def websocket_endpoint(websocket: WebSocket):
   
    await websocket.accept()
    while True:
        data = sensor_data_reader.get_data()
        
        if data :
            # print (f"{data})
            await websocket.send_text(json.dumps(data)) #sends the latest data points
        await asyncio.sleep(1)   

@app.get("/data/")
async def get_data():
    data = sensor_data_reader.get_data()
    if data:
        return JSONResponse(content={"data":data})
    else:
        raise HTTPException(status_code=404, detail="no data")
    
@app.post("/data/")
async def update_sensor_data(request: Request):
    # This endpoint can be used to simulate updates or interact with data in other ways
    data = sensor_data_reader.get_data()
    if data:
        return JSONResponse(content={"data": data})
    else:
        raise HTTPException(status_code=404, detail="No data available")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host ="localhost",port = 8000)