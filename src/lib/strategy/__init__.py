# import importlib
# import pkgutil
# import inspect
# import os
# import json
# import ast
from .utils import CustomOllamaModel
from .strategy_base import Strategy

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