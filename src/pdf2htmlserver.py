import os
import dotenv
from threading import Thread
import subprocess
from pathlib import Path
import logging
import re
import string
import secrets
from fastapi import FastAPI, UploadFile, Response, HTTPException
# import magic

dotenv.load_dotenv()
TOKEN_LENGTH = int(os.getenv("TOKEN_LENGTH"))

app = FastAPI()
logger = logging.getLogger("uvicorn")
# mime = magic.Magic(True)
tasks = {}

def extract_progress(pdf2htmlex_output_ln):
    match = re.search("Working: *(\d+)\/(\d+)", pdf2htmlex_output_ln)
    if (match):
        result = (int(match.group(1))*100) // int(match.group(2)) 
        return str(result)
    return None
        

def convert_task(token):
    input_file_path = tasks[token]['inputfile'][2:]
    logger.info(f"converting {input_file_path} to html file...")
    convert_proc = subprocess.Popen(f"docker run -it --rm -v {os.getcwd()}/pdf:/pdf -w /pdf pdf2htmlex/pdf2htmlex:0.18.8.rc2-master-20200820-ubuntu-20.04-x86_64 --process-outline 0 --font-size-multiplier 1 --zoom 1.35 /{input_file_path}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    
    # convert
    while (convert_proc.poll() is None):
        ln = convert_proc.stdout.readline()[:-1]
        print(ln)
        progress = extract_progress(ln)
        if (progress is not None):
            tasks[token]["progress"] = progress

    # conversion complete
    convert_proc.wait()
    convert_proc.kill()

    output_file_path = f"{Path(input_file_path).with_suffix('')}.html"
    if (Path(output_file_path).exists()):
        with open(output_file_path, "rb") as fin:
            content = fin.read()
        Path(output_file_path).unlink()
        with open(output_file_path, "wb") as fout:
            fout.write(content)
        tasks[token]["outputfile"] = output_file_path
        tasks[token]["state"] = "finished"
    else:
        tasks[token]["state"] = "failed"
        Path(tasks[token]["inputfile"]).unlink()
        logger.error(f"conversion of {input_file_path} to html failed.")

def clean_up_files(task):
    Path(task["inputfile"]).unlink()
    Path(task["outputfile"]).unlink()

@app.post("/pdf")
async def convert_pdf_to_html(uploaded_file: UploadFile):
    response = {"status": "Rejected"}
    # check file availability
    content = uploaded_file.file.read()
    # if (mime.from_buffer(content)=="application/pdf"):
    if (os.path.splitext(uploaded_file.filename)[-1]==".pdf"):
        response["status"] = "Accepted"

        # save uploaded file
        output_file_path = f"./pdf/{uploaded_file.filename}"
        with open(output_file_path, "wb") as fout:
            fout.write(content)

        # converting task
        # task token
        token = "".join([secrets.choice(string.ascii_letters+string.digits) for _ in range(TOKEN_LENGTH)])
        response["token"] = token
        tasks[token] = {"state": "working", "progress": "0", "inputfile": output_file_path}
        #conversion
        Thread(target=convert_task, args=(token,)).start()

    return response

@app.get("/task/{token}")
async def get_conversion_state(token):
    # check token
    if (token in tasks.keys()):
        if (tasks[token]["state"]=="failed"):
            tasks.pop(token)
        return {"state": tasks[token]["state"], "progress": tasks[token]["progress"]}

    raise HTTPException(status_code=404)

@app.get("/html/{token}")
async def get_html_file(token):
    # check if html is generated
    ok = False
    if (token in tasks.keys()):
        if (tasks[token]["state"]=="finished"):
            ok = True

    if (ok):
        # remove task & send html file
        task = tasks.pop(token)
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