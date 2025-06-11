from DB import DB
import sys

# setup the relative import path for data module.
sys.path.append(os.path.dirname(__file__) + '/..')

from data.prompt import Prompt

# __len__ __getitem__ __setitem__ __delitem__ __iter__ __contains__
# __enter__ __exit__  contextual management methods for the DB class
# __iter__ __next__ methods for iterating over languages (raise StopIteration when done)

db = DB()


print("\n".join([repr(_) for _ in db.languages]))
print(db.get_language_name(2))
lang_english = db.get_language_id('english')

newPrompt = Prompt(system_prompt="Answer in one sentence.", prompt_string="What is AI?", lang_id=lang_english)
db.add_prompt(newPrompt)

