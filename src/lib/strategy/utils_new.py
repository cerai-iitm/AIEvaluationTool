import os
from dotenv import load_dotenv
import json
import ast
from .logger import get_logger
from types import SimpleNamespace
from deepeval.metrics.g_eval.schema import Steps, ReasonScore
from ollama import Client, AsyncClient
from deepeval.models.base_model import DeepEvalBaseLLM

logger = get_logger("utils_new")

class FileLoader:
    """
    run_file_path : should be the __file__
    """
    @staticmethod
    def _load_env_vars(run_file_path:str):
        env_path = os.path.join(os.path.dirname(run_file_path), '.env')
        load_dotenv(env_path)
    

    ### need to change the function so that it works with strategy instead of the running file's name
    # @staticmethod
    # def _load_file_content(run_file_path:str, req_folder_path:str = '', file_name:str = ''):
    #     data_dir = os.path.join(os.path.dirname(run_file_path), req_folder_path) if req_folder_path != '' else os.path.dirname(run_file_path)
    #     try:
    #         file_names = os.listdir(data_dir)
    #     except:
    #         file_names = list()
    #         logger.error(f"The path {data_dir} does not exist. You might want to pass in data/{req_folder_path}.")
    #     running_file_name = run_file_path.split('/')[-1].removesuffix('.py') # .split("_")[-1] # the last split should be removed later after removing changed from filenames
    #     file_content = {}
    #     if file_name != "":
    #         file_content = FileLoader._fill_values(file_content, data_dir, file_name, multiple=False)
    #     else:
    #         for f in file_names:
    #             if running_file_name in f:
    #                 file_content = FileLoader._fill_values(file_content, data_dir, f)
    #     return file_content
    
    @staticmethod
    def _load_file_content(run_file_path:str, req_folder_path:str = "", file_name:str = "", **kwargs):
        data_dir = os.path.join(os.path.dirname(run_file_path), req_folder_path) if req_folder_path != '' else os.path.dirname(run_file_path)
        try:
            file_names = os.listdir(data_dir)
        except:
            file_names = list()
            logger.error(f"The path {data_dir} does not exist.")
        file_content = {}
        if file_name != "":
            file_content = FileLoader._fill_values(file_content, data_dir, file_name, multiple=False) # multiple false means only one file
            return file_content
        else:
            strat = kwargs.get("strategy_name")
            if not strat:
                logger.error("strategy_name was not inilialized.")
                return file_content
            else:
                prefixes = [os.path.commonprefix([strat, f]) for f in file_names]
                longest = max(prefixes, key=len, default=None)
                files = [f for f in file_names if f.startswith(longest)]
                if len(files) > 0:
                    for f in files:
                        file_content = FileLoader._fill_values(file_content, data_dir, f)
                else:
                    logger.error("None of the files in the directory match the strategy name.")
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
    
    @staticmethod
    def dot_dict(d):
        if isinstance(d, dict):
            return SimpleNamespace(**{k : FileLoader.dot_dict(v) for k,v in d.items()})
        else:
            return d


    @staticmethod
    def _to_dot_dict(run_file_path:str, dir_file_path:str, **kwargs):
        full_path = os.path.join(os.path.dirname(run_file_path), dir_file_path)
        if os.path.exists(full_path):
            with open(full_path, "r") as f:
                data = json.load(f)
            if kwargs.get("simple"):
                return json.loads(json.dumps(data[kwargs.get("strat_name")]), object_hook=lambda d: SimpleNamespace(**d))
            else:
                return FileLoader.dot_dict(data)
        else:
            logger.error(f"[ERROR] : could not find the path specified : {full_path}")
            return {}


class CustomOllamaModel(DeepEvalBaseLLM):
    def __init__(self, model_name : str, url : str, *args, **kwargs):
        self.model_name = model_name
        self.ollama_url = f"{url.rstrip()}"
        self.ollama_client = Client(host=self.ollama_url)
        self.score_reason = None
        self.steps = None
    
    def generate(self, input : str, *args, **kwargs) -> str:
        messages = [{"role": "user", "content": f'{input} /nothink'}] # nothink allows us to only get the final answer
        response = self.ollama_client.chat(
            model = self.model_name,
            messages=messages,
            format="json"
        )
        raw = json.loads(response.message.content)
        schema_ =  kwargs.get("schema")(**raw) # the deepeval library uses different schemas to serialize the JSON, so we return the schemas as required by the library
        if(kwargs.get("schema") is ReasonScore):
            self.score_reason = {"Score": schema_.score, "Reason": schema_.reason}
        if(kwargs.get("schema") is Steps):
            self.steps = schema_.steps
        return schema_ 
    
    def load_model(self, *args, **kwargs):
        return None
    
    async def a_generate(self, input:str, *args, **kwargs):
        client = AsyncClient(host=self.ollama_url)
        messages = [{"role": "user", "content": f'{input} /nothink'}]
        response = await client.chat(
            model=self.model_name,
            messages=messages,
            format="json"
        )
        raw = json.loads(response.message.content)
        schema_ =  kwargs.get("schema")(**raw)
        if(kwargs.get("schema") is ReasonScore):
            self.score_reason = {"Score": schema_.score, "Reason": schema_.reason}
        if(kwargs.get("schema") is Steps):
            self.steps = {"Steps" : schema_.steps}
        return schema_
    
    def get_model_name(self, *args, **kwargs):
         return self.model_name





        
