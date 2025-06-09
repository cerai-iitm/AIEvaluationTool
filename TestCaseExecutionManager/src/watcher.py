import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

class JsonFileHandler(FileSystemEventHandler):
    def __init__(self, folder_to_watch, script_to_run):
        super().__init__()
        self.folder_to_watch = folder_to_watch
        self.script_to_run = script_to_run

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            print(f"JSON file created: {event.src_path}")
            self.run_script()

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            print(f"JSON file modified: {event.src_path}")
            self.run_script()

    def run_script(self):
        # Run the other Python script
        print(f"Running script: {self.script_to_run}")
        subprocess.run(['python', self.script_to_run])

if __name__ == "__main__":
    folder_to_watch = "AIEvaluationTool\Data"
    script_to_run = "AIEvaluationTool\ResponseAnalyzer\src\ResponseAnalyzer.py"

    event_handler = JsonFileHandler(folder_to_watch, script_to_run)
    observer = Observer()
    observer.schedule(event_handler, folder_to_watch, recursive=False)
    observer.start()

    print(f"Waiting for Testing to complete : {folder_to_watch} for JSON file changes...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
