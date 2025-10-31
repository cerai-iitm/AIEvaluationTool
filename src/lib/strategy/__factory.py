from strategy import get_class, map_name_to_class

cls = get_class(map_name_to_class("indian_lang_fluency"))
if cls:
    obj = cls()
    print(obj.evaluate("This is a sentence."))
