import os
import dotenv
from threading import Thread
import subprocess
from pathlib import Path
import logging
import re
import uuid
from fastapi import FastAPI, UploadFile, Response, HTTPException

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
        

def convert_task(id):
    input_file_path = tasks[id]['inputfile']
    logger.info(f"converting {input_file_path} to html file...")
    convert_proc = subprocess.Popen(["pdf2htmlEX", "--process-outline", "0", "--font-size-multiplier", "1", "--zoom", "1.35", input_file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
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
        Path(output_file_path).unlink()
        with open(output_file_path, "wb") as fout:
            fout.write(content)
        tasks[id]["outputfile"] = output_file_path
        tasks[id]["state"] = "finished"
    else:
        tasks[id]["state"] = "failed"
        # Path(tasks[id]["inputfile"]).unlink()
        logger.error(f"conversion of {input_file_path} to html failed.")

def clean_up_files(task):
    Path(task["inputfile"]).unlink()
    Path(task["outputfile"]).unlink()

@app.post("/pdf")
async def convert_pdf_to_html(file: UploadFile):
    response = {"status": "Rejected"}
    # check file availability
    content = file.file.read()
    if (os.path.splitext(file.filename)[-1]==".pdf"):
        response["status"] = "Accepted"

        # save uploaded file
        output_file_path = f"./pdf/{file.filename}"
        with open(output_file_path, "wb") as fout:
            fout.write(content)

        # converting task
        # task id
        id = str(uuid.uuid4())
        response["taskId"] = id
        response["message"] = f"{file.filename} is in conversion."
        
        tasks[id] = {"state": "working", "progress": "0", "inputfile": output_file_path}
        #conversion
        Thread(target=convert_task, args=(id,)).start()

    return response

@app.get("/task/{id}")
async def get_conversion_state(id):
    # check id
    if (id in tasks.keys()):
        if (tasks[id]["state"]=="failed"):
            tasks.pop(id)
        return {
            "status": tasks[id]["state"], 
            "progress": tasks[id]["progress"], 
            "message": f"Conversion progress: {tasks[id]['progress']}%"
        }

    raise HTTPException(status_code=404)

@app.get("/html/{id}")
async def get_html_file(id):
    # check if html is generated
    ok = False
    if (id in tasks.keys()):
        if (tasks[id]["state"]=="finished"):
            ok = True

    if (ok):
        # remove task & send html file
        task = tasks.pop(id)
        with open(task["outputfile"], "rb") as fin:
            content = fin.read()
            # clean up files
            Thread(target=clean_up_files, args=(task,)).start()

            # send html file
            return Response(
                headers={
                    "Content-Type": "text/html"
                }, 
                content=content
            )

    raise HTTPException(status_code=404)