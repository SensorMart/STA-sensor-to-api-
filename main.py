from fastapi import FastAPI, WebSocket, Request ,HTTPException,WebSocketDisconnect
from fastapi.responses import HTMLResponse ,JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sensor_data.data_reader import SensorDataReader
import asyncio
import logging
import pandas as pd
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI()
templates =  Jinja2Templates(directory= "templates")

# initialize the sensor data reader and CSV writer
sensor_data_reader = SensorDataReader(port='COM7', baud_rate='115200',queue_size=1000)

csv_save_path = "./data"
os.makedirs(csv_save_path, exist_ok = True)
max_rows = 1000
current_file_index = 1


@app.get("/",response_class=HTMLResponse)
async def get_webpage(request: Request):
    return templates.TemplateResponse("index.html",{"request": request})

@app.websocket("/ws") 
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = sensor_data_reader.get_data()       
            if data :
                await websocket.send_json(data) #sends the latest data points
            await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        logger.info("websocket connection closed")
    except Exception as e:
        logger.error(f"websocket connection error:{e}")
    finally:
        if  websocket.client != True:
            await websocket.close() 

@app.get("/data/")
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
        
# @app.post("/data/")
# async def update_sensor_data(request: Request):
#     # This endpoint can be used to simulate updates or interact with data in other ways
#     data = sensor_data_reader.get_data()
#     if data:
#         return JSONResponse(content={"data": data})
#     else:
#         raise HTTPException(status_code=404, detail="No data available")
    

# This endpoint can be used to simulate updates or interact with data in other ways        
@app.post("/data")
async def get_csv_data():
    global current_file_index    
    data = sensor_data_reader.get_data()
    if data: 
        df = pd.DataFrame(data, columns=["sr_no","X","Y","Z"])
        #check number of row in the current file
        current_file_path = os.path.join(csv_save_path, f"data_{current_file_index}.csv")
        if os.path.exists(current_file_path):
            existing_df =pd.read_csv(current_file_path)
            total_rows = len(existing_df) + len(df)
            if total_rows>max_rows:
                current_file_index += 1
                current_file_path = os.path.join(csv_save_path,f"data_{current_file_index}.csv")
        
        if os.path.exists(current_file_path):
            df.to_csv(current_file_path, mode='a',header=False,index=False)
        else:
            df.to_csv(current_file_path,mode='w',header=True,index=False)

        return JSONResponse(content={"messages": "data saved succesfully"})
    else:
        raise HTTPException(status_code=404, detail="no data available") 
    
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host ="localhost",port = 8000)