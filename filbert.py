import sys
import time
import logging
import click
import textract
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import re
import os
import errno
import shutil
from ocrmypdf.api import ocr
from ocrmypdf.exceptions import PriorOcrFoundError


test_rule = {
    "regex": "Items\s*(\w*)\s(\d*),\s(\d*) -",
    "new_file": "~/Documents/chiro/(3)/(1)-(2)-(3).pdf"
}

class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        pass
        # print(f'event type: {event.event_type}  path : {event.src_path}')

    def on_created(self, event):
        process_file(event.src_path)

def process_file(file_path):
    if ".pdf" in file_path:
            rename_pdf_file(file_path)
    else:
        print("not a pdf, do nothing...for now")

            
def rename_pdf_file(file_path):

    temp_file = os.environ.get('TMPDIR', "./")+"tmp_pdf.pdf"

    try:    
        ocr(file_path, temp_file)
    except PriorOcrFoundError:
        temp_file = file_path

    text = textract.process(temp_file).decode()
    text = " ".join(text.split())
    
    print("text:", text)

    

    match = re.search(test_rule["regex"], text)

    
    new_file = test_rule["new_file"]
    new_file = new_file.replace("~", os.environ.get("HOME"))
    i = 1
    for term in match.groups():
        new_file = new_file.replace(f"({i})", term)
        i += 1


    print(new_file)
    os.makedirs(os.path.dirname(new_file), exist_ok=True)

    shutil.copy(file_path, new_file)

def run_as_service(directory_path, configfile):
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, directory_path, recursive=False)
    try:
        observer.start()
    except Exception as ex:
        print("error staring the scheduler")
        print(ex)
        return False
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print("running as service")

@click.command()
@click.argument('directory_path')
@click.option('--service', '-s', is_flag=True)
@click.option('--configfile', '-c')
def run(directory_path="", service=False, configfile=""):

    if service:
        run_as_service(directory_path, configfile)

    

    print("exiting")


if __name__ == "__main__":
    run()
   