from fastapi import FastAPI, WebSocket, Request ,HTTPException,WebSocketDisconnect
from fastapi.responses import HTMLResponse ,JSONResponse
from fastapi.templating import Jinja2Templates
from sensor_data.data_reader import SensorDataReader
import asyncio
import logging
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI()
templates =  Jinja2Templates(directory= "templates") #this is used to link html page in templates directory

#initialize the sensor data reader
sensor_data_reader = SensorDataReader(port='COM4', 
                                      baud_rate='115200',
                                      queue_size=1000,
                                      log_writer= "log.csv",
                                      csv_filename_prefix=" ",#this will come in the file saving prefix
                                      sr_no_limit=3000)#change here for the limit of the serial  number

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event: Start the data reading threads
    sensor_data_reader.read_thread.start()
    yield
    # Shutdown event: Ensure proper shutdown of threads and closing of CSV file
    sensor_data_reader.stop()
app.router.lifespan = lifespan




@app.get("/",response_class=HTMLResponse)
async def get_webpage(request: Request):
    return templates.TemplateResponse("index.html",{"request": request})

@app.websocket("/ws") 
async def websocket_endpoint(websocket: WebSocket):#function to make the websocket is initiated
    await websocket.accept()
    try:
        while True:
            data = sensor_data_reader.get_data() #takes the data directly from sensor reader      
            if data :
                await websocket.send_json(data) #sends the latest data points
            await asyncio.sleep(0.005)
    except WebSocketDisconnect:
        logger.info("websocket connection closed")
    except Exception as e:
        logger.error(f"websocket connection error:{e}")
    finally:
        if not websocket.client.closed:
            await websocket.close() 

    


@app.get("/data/")  #this is the route where the data points can beseen in json format 
async def get_data():
    try: 
        data = sensor_data_reader.get_data()
        if data:
            return JSONResponse(content={"data":data})
        else:
            raise HTTPException(status_code=404, detail="no data available")
    except Exception as e:
        logger.error(f"Error retriving data: {e}")
        raise HTTPException(status_code=500, detail="internal server error")
        
@app.post("/data/")    # This endpoint can be used to simulate updates or interact with data in other ways
async def update_sensor_data(request: Request):
    data = sensor_data_reader.get_data()
    if data:
        return JSONResponse(content={"data": data})
    else:
        raise HTTPException(status_code=404, detail="No data available")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host ="localhost",port = 8000)