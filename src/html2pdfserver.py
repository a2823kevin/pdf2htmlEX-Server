import os
from threading import Thread
from pathlib import Path
import logging
import string
import secrets
from fastapi import FastAPI, UploadFile, Response, HTTPException
import magic

TID_LENGTH = 5

app = FastAPI()
logger = logging.getLogger("uvicorn")
mime = magic.Magic(True)
tasks = {}

def convert_task(task_id):
    input_file_path = tasks[task_id]['inputfile']
    logger.info(f"converting {input_file_path} to html file...")
    os.system(f"docker run -it --rm -v ./pdf:/pdf -w /pdf pdf2htmlex/pdf2htmlex:0.18.8.rc2-master-20200820-ubuntu-20.04-x86_64 --process-outline 0 --font-size-multiplier 1 --zoom 1.35 '/{input_file_path}'")
    
    output_file_path = f"{Path(input_file_path).with_suffix('')}.html"
    if (Path(output_file_path).exists()):
        with open(output_file_path, "rb") as fin:
            content = fin.read()
        Path(output_file_path).unlink()
        with open(output_file_path, "wb") as fout:
            fout.write(content)
        tasks[task_id]["outputfile"] = output_file_path
        tasks[task_id]["state"] = "finished"
    else:
        tasks[task_id]["state"] = "failed"
        logger.error(f"conversion of {input_file_path} to html failed.")

def clean_up_files(task):
    Path(task["inputfile"]).unlink()
    Path(task["outputfile"]).unlink()

@app.post("/pdf")
async def convert_pdf_to_html(uploaded_file: UploadFile):
    response = {"status": "Rejected"}
    # check file availability
    content = uploaded_file.file.read()
    if (mime.from_buffer(content)=="application/pdf"):
        response["status"] = "Accepted"

        # save uploaded file
        output_file_path = f"pdf/{uploaded_file.filename}"
        with open(output_file_path, "wb") as fout:
            fout.write(content)

        # converting task
        # task id
        id = "".join([secrets.choice(string.ascii_letters+string.digits) for _ in range(TID_LENGTH)])
        response["task_id"] = id
        tasks[id] = {"state": "working", "inputfile": output_file_path}
        #conversion
        Thread(target=convert_task, args=(id,)).start()

    return response

@app.get("/task/{task_id}")
async def get_conversion_state(task_id):
    # check task id
    if (task_id in tasks.keys()):
        return {"state": tasks[task_id]["state"]}

    return {"state": "unknown"}

@app.get("/html/{task_id}")
async def get_html_file(task_id):
    # check if html is generated
    ok = False
    if (task_id in tasks.keys()):
        if (tasks[task_id]["state"]=="finished"):
            ok = True

        # deal conversion failed
        if (tasks[task_id]["state"]=="failed"):
            Path(tasks[task_id]["inputfile"]).unlink()
            tasks.pop(task_id)

    if (ok):
        # remove task & send html file
        task = tasks.pop(task_id)
        with open(task["outputfile"], "rb") as fin:
            content = fin.read()
            # clean up files
            Thread(target=clean_up_files, args=(task,)).start()

            # send html file
            return Response(
                headers={
                    "Content-Type": "text/html", 
                    "Content-Disposition": f"attachment; filename=\"{Path(task['outputfile']).name}\""
                }, 
                content=content
            )

    raise HTTPException(status_code=404)