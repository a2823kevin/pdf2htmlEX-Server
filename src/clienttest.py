import os
import time
import requests
import dotenv
import pyrfc6266
import logging

dotenv.load_dotenv()
logging.basicConfig(format='[%(levelname)s] %(message)s')

SERVER_IP = os.getenv("SERVER_IP")
SERVER_PORT = os.getenv("SERVER_PORT")
PDF_FILE = os.getenv("PDF_FILE")

if __name__=="__main__":
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    '''Phase 1: upload pdf file & get task id if file accepted'''
    logger.info("ENTERED PHASE 1")
    task = requests.post(f"http://{SERVER_IP}:{SERVER_PORT}/pdf", files={"uploaded_file": open(PDF_FILE, "rb")}).json()
    if (task["status"]=="Accepted"):

        '''Phase 2: check whether the conversion has been done'''
        logger.info("ENTERED PHASE 2")
        while True:
            task_state = requests.get(f"http://{SERVER_IP}:{SERVER_PORT}/task/{task['task_id']}").json()["state"]
            if (task_state!="working"):
                logger.info(f"conversion task {task_state}")
                break
            time.sleep(1)

        '''Phase 3: download html file if conversion task complete'''
        if (task_state=="finished"):
            logger.info("ENTERED PHASE 3")
            resp = requests.get(f"http://{SERVER_IP}:{SERVER_PORT}/html/{task['task_id']}")
            with open(f"test/downloaded_{pyrfc6266.parse_filename(resp.headers['Content-Disposition'])}", "wb") as fout:
                fout.write(resp.content)
                
    logger.info("TEST COMPLETE")