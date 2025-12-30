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


from ddgs import DDGS
import bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import re
import requests
import heapq
from typing import Optional
from pydantic import BaseModel
import itertools

counter = itertools.count()

class TextData(BaseModel):
    text : str
    title : Optional[str]
    href : Optional[str]

def top_links(query, n=3):
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=n)
        return [TextData(text=r["body"], href=r["href"], title=r["title"]) for r in results if len(r["body"]) > 100]

page_info = top_links("agriculture in india")

headers = {
    "User-Agent" : (
        "MyTextFetcher/0.1"
        "(Research Project; https://github.com/anukul; anukul@gmail.com)"
    ),
    "Accept-Encoding" : "gzip"
}

html_pages = [requests.get(l.href, timeout=10, headers=headers) for l in page_info]
text_strainer = bs4.SoupStrainer(["article", "section", "div", "main", "h1", "h2", "h3"])#, class_=[re.compile("content")])
soups = [(bs4.BeautifulSoup(page.text, features="lxml", parse_only=text_strainer), info.title, info.href) for page, info in zip(html_pages, page_info)]

candidates = []

def rank_text(text:str):
    length_score = len(text)
    sentence_score = text.count(".") * 20
    paragraph_score = text.count("\n") * 5
    digit_penalty = len(re.findall(r"\d", text)) * 15
    symbol_penalty = len(re.findall(r"[|/\\=<>_{}<>@#$^*_+=~`[\]]", text)) * 20
    short_word_pen = len(re.findall(r"\b\w{1,2}\b", text)) * 5

    return length_score + sentence_score + paragraph_score - digit_penalty - symbol_penalty - short_word_pen

def clean_text(text:str):
    text = re.sub(r"https?://[^\s]+", "", text) # URLs, keep line breaks also
    text = re.sub(r"\[[^\]]{1,4}\]", "", text) # remove texts like [1] [2]
    text = re.sub(r"[|•·–—]+", " ", text) # whitespace after separators
    text = re.sub(r"[<>@#$^*_+=~`]", " ", text) # whitespace after these symbols
    text = re.sub(r"\b[a-zA-Z]{30,}\b", " ", text) # remove the long words, generally meaningless
    text = re.sub(r"[ \t]+", " ", text)     # collapse spaces only
    text = re.sub(r"\n{3,}", "\n\n", text)  # keep paragraphs
    text = text.strip()

    lines = []
    for line in re.split(r"(?<=[.!?])\s+", text):
        line = line.strip()
        if len(line) < 25:
            continue
        if line.isupper():
            continue
        lines.append(line)
    return ". ".join(lines)

for soup in soups:
    for tag in soup[0].find_all([re.compile("article|main|section|div|h1|h2|h3")]):
        text = tag.get_text(strip=True)

        if len(text) < 500:
            continue
        text = clean_text(text)
        score = rank_text(text)
        
        heapq.heappush(candidates, (-1 * score, next(counter), TextData(text=text, title=soup[1], href=soup[2])))

# best_info_texts = [heapq.heappop(candidates)[1] for _ in range(len(soups))]
best_info_texts = []

sources = list(set([page_info[i].href for i in range(len(page_info))]))
while(len(sources) > 0 and len(candidates) > 0):
    popped_elem = heapq.heappop(candidates)[2]
    best_info_texts.append(popped_elem)
    if(popped_elem.href not in sources):
        continue
    sources.remove(popped_elem.href)

docs = []
for pages in best_info_texts:
    docs.append(
        Document(
            page_content=pages.text,
            metadata = {
                "source" : pages.href,
                "title" : pages.title
            }
        )
    )

print(docs[0].page_content)

splitter = RecursiveCharacterTextSplitter(chunk_size = 2000, chunk_overlap=400, add_start_index=True)
chunked_docs = splitter.split_documents(docs)


# loader = WebBaseLoader(
#     web_paths=(links[0][1],),
#     bs_kwargs={"parse_only" : text_strainer},
# )
# docs = loader.load()

# for l in links:
#     print(l)

# print(f"{docs[0].page_content}")

