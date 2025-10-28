import os
from dotenv import load_dotenv
import json
import ast

class FileLoader:
    """
    run_file_path : should be the __file__
    """
    @staticmethod
    def _load_env_vars(run_file_path:str):
        env_path = os.path.join(os.path.dirname(run_file_path), '.env')
        load_dotenv(env_path)
    
    @staticmethod
    def _load_file_content(run_file_path:str, req_folder_path:str = '', file_name:str = ''):
        data_dir = os.path.join(os.path.dirname(run_file_path), req_folder_path) if req_folder_path != '' else os.path.dirname(run_file_path)
        try:
            file_names = os.listdir(data_dir)
        except:
            file_names = list()
            print(f"[ERROR] : The path {data_dir} does not exist. You might want to pass in data/{req_folder_path}.")
        running_file_name = run_file_path.split('/')[-1].removesuffix('.py').split("_")[-1] # the last split should be removed later
        file_content = {}
        if file_name != "":
            file_content = FileLoader._fill_values(file_content, data_dir, file_name, multiple=False)
        else:
            for f in file_names:
                if running_file_name in f:
                    file_content = FileLoader._fill_values(file_content, data_dir, f)
        return file_content
    
    @staticmethod
    def _fill_values(file_content:dict, data_dir:str, f:str, multiple:bool = True):
        store_name = f.split(".")[0]
        if(f.split(".")[1] == "json"):
            with open(os.path.join(data_dir, f), "r") as file:
                content = json.load(file)
                if isinstance(content, dict) and not multiple:
                    file_content = content
                else:
                    file_content[store_name] = content
        elif(f.split(".")[1] == "txt"):
            with open(os.path.join(data_dir, f), "r") as file:
                file_content[store_name] = ast.literal_eval(file.read())
        return file_content


    @staticmethod
    def _check_if_present(run_file_path:str, folder_path:str, search_file_name:str):
        if (os.path.exists(os.path.join(os.path.join(os.path.dirname(run_file_path), folder_path), search_file_name))):
            return True
        else:
            return False
    
    @staticmethod
    def _save_values(data:dict, data_dir:str, file_name:str):
        ext = file_name.split(".")[1]
        if ext == "json":
            with open(os.path.join(data_dir, file_name), "w") as f:
                json.dump(data, f)
        elif ext == "txt":
            with open(os.path.join(data_dir, file_name), "w") as f:
                f.write(json.dumps(data))
            
    




        
