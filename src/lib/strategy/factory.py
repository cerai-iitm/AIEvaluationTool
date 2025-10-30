from strategy import get_class

# create_mapp()
# load_strategies()
cls = get_class("IndianLanguageFluencyScorer")
if cls:
    obj = cls(name="indian_lang_fluency")
    print(obj.evaluate("This is what I do."))