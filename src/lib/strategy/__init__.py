import importlib
# import pkgutil
# import inspect
import os
import json
import ast


CACHE_PATH = os.path.join(os.path.dirname(__file__), ".strategy_registery_cache.json")
REGISTERY = {}
MAPP = {}

def create_mapp():
    package = __name__
    package_path = os.path.dirname(__file__)
    for filename in os.listdir(package_path):
        # write the name of the files that we dont want to include in the registery
        if filename.startswith("__") or not filename.endswith(".py"):
            continue
        full_path = os.path.join(package_path, filename)
        mod_name = f"{package}.{filename.removesuffix('.py')}"

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=filename)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        for base_cls in node.bases:
                            if isinstance(base_cls, ast.Name) and base_cls.id == "Strategy":
                                MAPP[node.name] = mod_name
                                break
        except Exception as e:
            print(f"Failed to scan the file {filename}, Error : {e}")
        
    save_cache()

def get_class(name:str):
    global REGISTERY
    cls = REGISTERY.get(name)
    if cls:    
        return cls
    
    load_cache()

    mod_name = MAPP.get(name)
    if not mod_name:
        create_mapp()
        mod_name = MAPP.get(name)
        if not mod_name:
            raise ValueError(f"Class {mod_name} not found in the package.")
    
    mod =  importlib.import_module(mod_name)
    cls = getattr(mod, name)
    REGISTERY[name] = cls
    return cls

def update_mapp():
    package_path = os.path.dirname(__file__)
    package_name = __name__
    new_paths = set(f"{package_name}.{name.removesuffix('.py')}" for name in os.listdir(package_path) if name.endswith('.py') and not name.startswith('__'))
    prev_paths = set(v for v in MAPP.values())
    if new_paths != prev_paths:
        print("Rebuilding cache...")
        create_mapp()

def save_cache():
    with open(CACHE_PATH, "w") as f:
        json.dump(MAPP, f)
        print(f"Saved strategy class registery to {CACHE_PATH}")

def load_cache():
    global MAPP
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r") as f:
            MAPP = json.load(f)

if __name__ == "__main__":
    load_cache()

# def load_strategies():
#     start = time.time()
#     cache = load_cache()
#     print(f"time taken to load : {time.time() - start}")
#     print(cache)
#     package = __name__
#     print(package)
#     package_path = os.path.dirname(__file__)
#     REGISTERY.clear()

#     for _, mod_name, _ in pkgutil.iter_modules([package_path]):
#         # write the name of the files that we dont want to include in the registery
#         if mod_name in ["__init__", "factory"]:
#             continue

#         file_path = os.path.join(package_path, f"{mod_name}.py")
#         file_m_time = os.path.getmtime(file_path)

#         # we try to find if this module's file has been changed by returning one item from that module
#         def get_val(cache:dict):
#             for _ , v in cache.items():
#                 if v.get("mtime") == file_m_time and v.get("filepath") == file_path:
#                     return v
#             return None
#         # if we get even one item, then the file was not modified and we update all the classes in that file into the registery
#         if get_val(cache):
#             REGISTERY.update({k : v for k, v in cache.items() if v.get("filepath") == file_path})
#             continue

#         name = f"{package}.{mod_name}"
#         print(f"Loading module : {name}")
#         if name in sys.modules:
#             print(f"Reloading the modified module : {name}")
#             mod = importlib.reload(sys.modules[name])
#         else:
#             mod = importlib.import_module(name)
#             print(f"Imported the new class : {mod.__name__} successfully.")

#         for name, obj in inspect.getmembers(mod, inspect.isclass):
#             if obj.__module__ == mod.__name__ and issubclass(obj, Strategy):
#                 REGISTERY[name] = {
#                     "filepath" : file_path,
#                     "file_m_time" : file_m_time,
#                     "class" : obj
#                 }
#                 print(f"Registered class : {name}")
        
#     save_cache(REGISTERY)