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
import json
from ocrmypdf.api import ocr
from ocrmypdf.exceptions import PriorOcrFoundError


class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        pass
        # print(f'event type: {event.event_type}  path : {event.src_path}')

    def on_created(self, event):
        process_file(event.src_path)

def process_file(file_path, config_data):


    for rule in config_data["rules"]:
        if re.match(rule["files"], file_path):
            if file_contains(file_path, rule.get("contains", ".*")):
                if(rule["action"] == "rename"):
                    rename_file(file_path, rule)
                return
    else:
        print("not a pdf, do nothing...for now")

def file_contains(file_path, needle):
    
    if re.match(".*pdf", file_path):

        temp_file = file_path

        try:    
            ocr(file_path, temp_file)
        except PriorOcrFoundError:
            temp_file = file_path

        
        text = textract.process(temp_file).decode()
        text = " ".join(text.split())
        print(needle)
        if re.match(needle, text):
            print(f"found a match for {needle} in this")
            print(text)
        
        return re.match(needle, text)

            
def rename_file(file_path, rule):

    new_file = rule["new_file"]
    new_file = new_file.replace("~", os.environ.get("HOME"))

    if rule.get("contains", False):
        if re.match(".*pdf", file_path):

            temp_file = os.environ.get('TMPDIR', "./")+"tmp_pdf.pdf"

            try:    
                ocr(file_path, temp_file)
            except PriorOcrFoundError:
                temp_file = file_path

            text = textract.process(temp_file).decode()
            text = " ".join(text.split())    

            match = re.search(rule["contains"], text)
            i = 1
            for term in match.groups():
                new_file = new_file.replace(f"({i})", term)
                i += 1

    os.makedirs(os.path.dirname(new_file), exist_ok=True)

    print(f"copying {file_path} to {new_file}")
    shutil.copy(file_path, new_file)

def run_as_service(directory_path, config_data):
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

def process_directory(directory_path, config_data):
    for filename in os.listdir(directory_path):
        if os.path.isfile(f"{directory_path}/{filename}"):
            file_path = f"{directory_path}/{filename}"
            print(file_path)
            process_file(file_path, config_data)

    

@click.command()
@click.argument('directory_path')
@click.option('--service', '-s', is_flag=True)
@click.option('--configfile', '-c')
def run(directory_path="", service=False, configfile=""):

    if not configfile:
        configfile = "./default_config.json"

    with open(configfile) as json_data:
        config_data = json.load(json_data)
        json_data.close()

    if service:
        run_as_service(directory_path, config_data)
    
    process_directory(directory_path, config_data)
    

if __name__ == "__main__": run()
   