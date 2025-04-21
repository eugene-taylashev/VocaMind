
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

#import uvicorn

import tasks

#-- FastAPI
app = FastAPI()

#-----------------------------------------------------------------------------------
#-- Output HTML page for the client
#-----------------------------------------------------------------------------------
@app.get("/")
async def root():
    content = tasks.out_index_page()
    return HTMLResponse(content=content)

#-- images and Javascript files
app.mount("/images", StaticFiles(directory="./images"), name="images")


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
@app.get("/calls/{call_id}")
async def get_call_details(call_id: int):
    """
    Get call details
    """
    events = []
    #-- get the call details from the DB
    call, events = tasks.get_call_details(call_id)
    if not call:
        return {"response": [{"status":"error","msg":"No call found"}] }
    return {"response": [{"status":"ok","msg":"Call found","call":call}] }

#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
#curl -X POST -F "file=@/path/to/file.wav" 'http://localhost:8000/calls/upload'
@app.post("/calls/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file:
        return {"response": [{"status":"error","msg":"No upload file sent"}] }
    #-- process the file
    events = await tasks.upload_call_file(file)
    return {"response": events}


#if __name__ == "__main__":
#    uvicorn.run(app, host="0.0.0.0", port=8000)
