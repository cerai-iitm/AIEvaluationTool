from strategy import get_class
import time

cls = get_class("IndianLanguageFluencyScorer")
if cls:
    obj = cls(name="indian_lang_fluency")
    print(obj.evaluate("This is a sentence."))
