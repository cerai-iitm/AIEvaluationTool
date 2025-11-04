# from strategy import get_class, map_name_to_class

# cls = get_class(map_name_to_class("indian_lang_fluency"))
# if cls:
#     obj = cls()
#     print(obj.evaluate("This is a sentence."))

import os
import json
import ast
import importlib
from lib.data import TestCase, Conversation
from .logger import get_logger


logger = get_logger("lazy_loader")

class LazyLoader:

    def __init__(self):
        self.CACHE_PATH = os.path.join(os.path.dirname(__file__), ".strategy_registery_cache.json")
        self.REGISTERY = dict()
        self.CLASS_NAME_TO_MOD_NAME = dict()
        self.STRAT_NAME_TO_CLASS_NAME = dict()
        self.package = __package__ # full name e.g. mypackage.utils.helper (who am i ?) but __package__ would be mypackage.utils (where do i live?)
        self.package_path = os.path.dirname(__file__)
        # if the cache file is there just load it
        self.load_cache()
        
    def create_mapp(self):
        for filename in os.listdir(self.package_path):
            # remove the last condition later
            if filename.startswith("__") or not filename.endswith(".py") or not filename.startswith("changed"):
                continue
            full_path = os.path.join(self.package_path, filename)
            mod_name = f"{self.package}.{filename.removesuffix('.py')}"

            try:
                with open(full_path, "r") as f:
                    tree = ast.parse(f.read(), filename=filename)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            for base_cls in node.bases:
                                if isinstance(base_cls, ast.Name) and base_cls.id == "Strategy":
                                    self.CLASS_NAME_TO_MOD_NAME[node.name] = mod_name

                                    for body in node.body:
                                        if isinstance(body, ast.FunctionDef) and body.name == "__init__":
                                            for (arg, val) in zip(body.args.args[-len(body.args.defaults):], body.args.defaults):
                                                if arg.arg == "name":
                                                    if isinstance(val, ast.Constant):
                                                        self.STRAT_NAME_TO_CLASS_NAME[val.value] = node.name
                                                        break
                                    break
                assert(len(self.CLASS_NAME_TO_MOD_NAME) == len(self.STRAT_NAME_TO_CLASS_NAME))
            except Exception as e:
                print(f"Failed to scan the file {filename}, Error : {e}")
        self.save_cache()
    
    def get_class(self, class_name:str):
        if class_name in self.REGISTERY:
            return self.REGISTERY.get(class_name)
        # search for the value in the loaded cache
        mod_name = self.CLASS_NAME_TO_MOD_NAME.get(class_name)
        # if the class name is not present in the previous cache, the files might have been updated or the cache might not have been loaded
        if not mod_name:
            # So, create new cache and save it
            self.create_mapp()
            # if the class name is still not present, then there is an error in the name
            mod_name = self.CLASS_NAME_TO_MOD_NAME.get(class_name)
            if not mod_name:
                raise ValueError(f"Class {mod_name} not found in the package.")
        
        mod = importlib.import_module(mod_name)
        cls = getattr(mod, class_name)
        self.REGISTERY[class_name] = cls
        return cls
    
    def map_name_to_class(self, name:str):
        # if there is no cache loaded prior, then create the cache and save it
        if not self.STRAT_NAME_TO_CLASS_NAME or not self.STRAT_NAME_TO_CLASS_NAME.get(name):
            self.create_mapp()
        try:
            return self.STRAT_NAME_TO_CLASS_NAME.get(name)
        except Exception as e:
            logger.error(f"Could not load the cache because it is empty. : {e}")
            return None

    def save_cache(self):
        with open(self.CACHE_PATH , "w") as f:
            data = [self.CLASS_NAME_TO_MOD_NAME, self.STRAT_NAME_TO_CLASS_NAME]
            json.dump(data, f)
            # print(f"Saved strategy class registery to {self.CACHE_PATH}.")
    
    def load_cache(self):
        if os.path.exists(self.CACHE_PATH):
            with open(self.CACHE_PATH, "r") as f:
                data = json.load(f)
                self.CLASS_NAME_TO_MOD_NAME = data[0]
                self.STRAT_NAME_TO_CLASS_NAME = data[1]

# ll = LazyLoader()
# try:
#     cls = ll.get_class(ll.map_name_to_class("indian_lang_fluency"))
# except Exception as e:
#     print(f"[ERROR]: Could not load the class specified. {e}")
# if cls:
#     obj = cls()
#     print(obj.evaluate("This my is the bad bad. I am the lovely of son my fathers. I come to India for study and I learn many thing and travel many places."))
#     print(obj.evaluate("This is a sentence. There is a house nearby. I like to walk my dog and eat my sandwich. My wife is lovely and I love my parents."))
