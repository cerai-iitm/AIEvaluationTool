import warnings, os
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader
from ddgs import DDGS

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("hallucination")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="hallucination")

class HallucinationStrategy(Strategy):
    def __init__(self, name = "hallucination", **kwargs):
        super().__init__(name, **kwargs)
        pass

    def get_important(self):
        pass
    
    def find_relevant(self):
        pass

    def scrape_(self):
        pass

    def preprocess(self):
        pass

    def vector_store(self):
        pass

    def search_relevant_in_db(self):
        pass
    
    #generate an augmented output based on the prompt by following the previous methods, summarize if required 
    def aug_generate(self):
        pass
    
    # this is the only function that is not a util i think currently
    def compare_with_bot_op(self):
        pass

    def evaluate(self, testcase:TestCase, conversation:Conversation):
        pass


# from ddgs import DDGS
# import bs4
# from langchain_community.document_loaders import WebBaseLoader
# import re
# import requests
# import heapq

# def top_links(query, n=3):
#     with DDGS() as ddgs:
#         results = ddgs.text(query, max_results=n)
#         # print(results)
#         return [(r["title"], r["href"], r["body"]) for r in results if len(r["body"]) > 100]

# links = top_links("agriculture in india")

# # text_strainer = bs4.SoupStrainer(
# #     ["article", "section", "p"],
# #     class_=re.compile("content|article|main|body")
# # )
# headers = {
#     "User-Agent" : (
#         "MyTextFetcher/0.1"
#         "(Research Project; https://github.com/anukul; anukul@gmail.com)"
#     ),
#     "Accept-Encoding" : "gzip"
# }

# html_pages = [requests.get(links[i][1], timeout=10, headers=headers) for i in range(len(links))]
# text_strainer = bs4.SoupStrainer(["article", "section", "div", "main", "h1", "h2", "h3"])#, class_=[re.compile("content")])
# soup = bs4.BeautifulSoup(html_pages[2].text, features="lxml", parse_only=text_strainer)

# candidates = []

# def rank_text(text:str):
#     length_score = len(text)
#     sentence_score = text.count(".") * 20
#     paragraph_score = text.count("\n") * 5

#     digit_penalty = len(re.findall(r"\d", text)) * 15
#     symbol_penalty = len(re.findall(r"[|/\\=<>_{}<>@#$^*_+=~`[\]]", text)) * 20

#     short_word_pen = len(re.findall(r"\b\w{1,2}\b", text)) * 5

#     return length_score + sentence_score + paragraph_score - digit_penalty - symbol_penalty - short_word_pen

# def clean_text(text:str):
#     text = re.sub(r"\s+", " ", text)
#     text = re.sub(r"https://\S+", " ", text)
#     text = re.sub(r"\[[^\]]{1,4}\]", "", text)
#     text = re.sub(r"[|•·–—]{2,}", "", text)
#     text = re.sub(r"[<>@#$^*_+=~`]", "", text)
#     text = re.sub(r"\b[a-zA-Z]{30,}\b", "", text)

#     lines = []
#     for line in re.split(r"(?<=[.!?])\s+", text):
#         line = line.strip()
#         if len(line) < 25:
#             continue
#         if line.isupper():
#             continue
#         lines.append(line)
#     return ". ".join(lines)

# for tag in soup.find_all([re.compile("article|main|section|div")]):
#     text = tag.get_text(strip=True)

#     if len(text) < 500:
#         continue
#     score = rank_text(text)
#     text = clean_text(text)
    
#     heapq.heappush(candidates, (score, text))

# print(heapq.nlargest(2, candidates))
# # loader = WebBaseLoader(
# #     web_paths=(links[0][1],),
# #     bs_kwargs={"parse_only" : text_strainer},
# # )
# # docs = loader.load()

# # for l in links:
# #     print(l)

# # print(f"{docs[0].page_content}")