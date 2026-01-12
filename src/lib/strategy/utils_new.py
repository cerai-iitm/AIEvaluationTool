import os
from dotenv import load_dotenv
import json
import ast
import csv
from .logger import get_logger
from types import SimpleNamespace
import hashlib
from deepeval.metrics.g_eval.schema import Steps, ReasonScore
from ollama import Client, AsyncClient
from deepeval.models.base_model import DeepEvalBaseLLM
from typing import Optional, List

logger = get_logger("utils_new")

class FileLoader:
    """
    run_file_path : should be the __file__
    """
    @staticmethod
    def _load_env_vars(run_file_path:str):
        env_path = os.path.join(os.path.dirname(run_file_path), '.env')
        load_dotenv(env_path)
    
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
                logger.error("Strategy_name was not inilialized.")
                return file_content
            else:
                prefixes = [os.path.commonprefix([strat, f]) for f in file_names]
                longest = max(prefixes, key=len, default=None)
                files = [f for f in file_names if f.startswith(longest) and len(longest) >= len(strat.split("_")[0])] #the length of the prefix should be at least as long as the first word in the strategy name so that longest is not empty, if its empty it matches with all the names
                if len(files) > 0:
                    for f in files:
                        logger.info(f"Using file {f} to load the examples and evaluate the strategy.")
                        file_content = FileLoader._fill_values(file_content, data_dir, f)
                else:
                    logger.error("None of the files in the data/examples directory match the strategy name.")
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
    def _save_values(run_file_path:str, data:dict, data_dir:str, file_name:str):
        ext = file_name.split(".")[1]
        run_file_dir = os.path.dirname(run_file_path)
        with open(os.path.join(os.path.join(run_file_dir, data_dir), file_name), "w") as f:
            if ext == "json":
                json.dump(data, f)
            elif ext == "txt":
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
                def hook(obj):
                    if obj.get("__as_dict__") is True:
                        obj.pop("__as_dict__", None)
                        return obj
                    return SimpleNamespace(**obj)
                return json.loads(json.dumps(data[kwargs.get("strat_name")]), object_hook=hook)
            else:
                return FileLoader.dot_dict(data)
        else:
            logger.error(f"[ERROR] : could not find the path specified : {full_path}")
            return {}
    
    @staticmethod
    def _save_to_csv(run_file_path:str, df:dict, **kwargs):
        folder_path = os.path.join(os.path.dirname(run_file_path), os.path.join(kwargs.get("data_dir"), kwargs.get("save_dir")) )
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        file_path = os.path.join(folder_path, f"{kwargs.get('strat_name')}.csv")
        file_exists = os.path.isfile(file_path)
        hash = hashlib.sha256(df.get("id").encode('utf-8')).hexdigest()[:20]

        if file_exists:
            with open(file_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fields = reader.fieldnames     
                data = {row["id"] : row for row in reader}
            values = [hash, *df.get("score").values()]
            data.update({hash : {f : v for f, v in zip(fields, values)}}) 
        else:
            fields = ["id", *df.get("score").keys()]
            values = [hash, *df.get("score").values()]
            data = {hash : {f : v for f, v in zip(fields, values)}}

        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data.values())
        logger.info(f"Score and reason saved to : {file_path}")

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


class OllamaConnect:
    
    FileLoader._load_env_vars(__file__)
    ollama_url = os.getenv("OLLAMA_URL")
    dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="ollama_comms")

    @staticmethod
    def prompt_model(text:str, fields:List[str], model_names:List[str] = None, options:dict = None) -> List[dict]:
        ollama_client = Client(host=OllamaConnect.ollama_url)
        tries = OllamaConnect.dflt_vals.n_tries
        resp_in_format = []
        models = OllamaConnect.dflt_vals.model_names if model_names is None else model_names
        while(resp_in_format == [] and tries > 0):
            for model in models:
                try:
                    inputs = {
                        "model" : model,
                        "messages" : [
                            {
                                "role" : "user",
                                "content" : f"{text} /nothink",
                            }
                        ],
                        "format":"json",
                    }
                    if options is not None:
                        inputs.update({"options": options})
                    response = ollama_client.chat(**inputs)
                    try:
                        final = json.loads(response.message.content)
                    except:
                        final = {}
                except Exception as e:
                    logger.error(f"Did not receive any response from the model : {model}.")
                    final = {}
                if(OllamaConnect.has_correct_format(final, fields)):
                    resp_in_format.append(final)
            tries -= 1
        return resp_in_format
    
    @staticmethod
    def has_correct_format(obj : Optional[dict], fields: List[str]):
        correct = isinstance(obj, dict) 
        for fld in fields:
            correct = correct and fld in fields and isinstance(obj.get(fld), str) 
        return correct
    
    @staticmethod
    def get_reason(agent_response:str, strategy_name:str, score:float, **kwargs):
        prompt = OllamaConnect.dflt_vals.reason_prompt.format(input_sent=agent_response, metric=strategy_name, score=score, add_info=kwargs.get("add_info", ""))
        responses = OllamaConnect.prompt_model(prompt, OllamaConnect.dflt_vals.reqd_flds)
        final_rsn = ""
        if(len(responses) > 0):
            reasons = [r["reason"] for r in responses]
            if(len(reasons) == 1): return f"Reason : {r}" 
            for i, r in enumerate(reasons):
                if i == 0:
                    final_rsn += f"Reason {i+1} : {r}"
                else:
                    final_rsn += f"\n\n Reason {i+1} : {r}"
            return final_rsn
        else:
            return "Could not get a proper reasoning for the score."