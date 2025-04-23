import os
import dotenv
from threading import Thread
import time
import datetime
import subprocess
from pathlib import Path
from typing import Any
import logging
import re
import uuid
from fastapi import FastAPI, UploadFile, Response
from pydantic import BaseModel

class ApiResponse(BaseModel):
    status: str
    message: str | None = None
    data: Any = None
    
    @staticmethod
    def success(msg, data):
        return ApiResponse(status="ok", message=msg, data=data)
    
    @staticmethod
    def error(msg):
        return ApiResponse(status="error", message=msg)

dotenv.load_dotenv()
app = FastAPI()
logger = logging.getLogger("uvicorn")
tasks = {}

def extract_progress(pdf2htmlex_output_ln):
    match = re.search("Working: *(\d+)\/(\d+)", pdf2htmlex_output_ln)
    if (match):
        result = (int(match.group(1))*100) // int(match.group(2)) 
        return str(result)
    return None

def cleanup(id):
    if (id in tasks.keys()):
        for f in ["inputfile", "outputfile"]:
            if (f in tasks[id].keys()):
                try:
                    Path(tasks[id][f]).unlink()
                except:
                    pass
        tasks.pop(id)

def auto_cleanup(id):
    start_time = datetime.datetime.now()
    while True:
        current_time = datetime.datetime.now()
        if (current_time>=start_time+datetime.timedelta(minutes=30)):
            break
        time.sleep(60)
    cleanup(id)

def convert_task(id):
    input_file_path = tasks[id]['inputfile']
    logger.info(f"converting {input_file_path} to html file...")
    convert_proc = subprocess.Popen(["pdf2htmlEX", "--debug", "1", "--process-outline", "0", "--font-size-multiplier", "1", "--no-drm", "1", "--bg-format", "none", input_file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # convert
    while True:
        ln = convert_proc.stdout.readline()
        if not ln:
            break
        print(ln, end='')
        progress = extract_progress(ln)
        if (progress is not None):
            tasks[id]["progress"] = progress

    output_file_path = f"./{Path(input_file_path[6:]).with_suffix('')}.html"
    if (Path(output_file_path).exists()):
        with open(output_file_path, "rb") as fin:
            content = fin.read()
        with open(output_file_path, "wb") as fout:
            fout.write(content)
        tasks[id]["outputfile"] = output_file_path
        tasks[id]["state"] = "finished"
    else:
        tasks[id]["state"] = "failed"
        logger.error(f"conversion of {input_file_path} to html failed.")

@app.post("/pdf")
async def convert_pdf_to_html(file: UploadFile):
    # check file availability
    content = file.file.read()
    if (os.path.splitext(file.filename)[-1]==".pdf"):
        # save uploaded file
        output_file_path = f"./pdf/{file.filename}"
        with open(output_file_path, "wb") as fout:
            fout.write(content)

        # converting task
        # task id
        id = str(uuid.uuid4())
        
        tasks[id] = {"state": "working", "progress": "0", "inputfile": output_file_path}
        
        #conversion
        Thread(target=convert_task, args=(id,)).start()
        Thread(target=auto_cleanup, args=(id,)).start()

        return ApiResponse.success(
            f"{file.filename} is in conversion.", 
            {
                "taskId": id
            }
        )
    return ApiResponse.error("Invalid pdf file.")

@app.get("/task/{id}")
async def get_conversion_state(id):
    # check id
    if (id in tasks.keys()):
        task = tasks[id]
        if (task["state"]=="failed"):
            cleanup(id)
            return ApiResponse.success(
                "Conversion failed.", 
                {
                    "state": task["state"], 
                    "progress": task["progress"]
                }
            )

        else:
            return ApiResponse.success(
                f"Conversion progress: {task['progress']}%", 
                {
                    "state": task["state"], 
                    "progress": task["progress"]
                }
            )

    return ApiResponse.error("Task not found.")

@app.get("/html/{id}")
async def get_html_file(id):
    # check if html is generated
    ok = False
    if (id in tasks.keys()):
        if (tasks[id]["state"]=="finished"):
            ok = True

    if (ok):
        # remove task & send html file
        task = tasks[id]
        with open(task["outputfile"], "rb") as fin:
            content = fin.read()
            # clean up files
            Thread(target=cleanup, args=(id,)).start()

            # send html file
            return Response(
                headers={
                    "Content-Type": "text/html"
                }, 
                content=content
            )

    return ApiResponse.error("Task not found.")