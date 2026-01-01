from ddgs import DDGS
import bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import re
import os
import requests
import heapq
from typing import Optional
from pydantic import BaseModel
import itertools
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
import math
from collections import Counter
import hashlib
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
import time

counter = itertools.count()

class TextData(BaseModel):
    text : str
    title : Optional[str]
    href : Optional[str]

class InfoRetrieve:
    def __init__(self):
        pass

    def top_links(self, query:str, n=3):
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=n)
            return [TextData(text=r["body"], href=r["href"], title=r["title"]) for r in results if len(r["body"]) > 100]
    
    def create_header(self):
        return {
            "User-Agent" : (
                "MyTextFetcher/0.1"
                "(Research Project; https://github.com/anukul; anukul@gmail.com)"
            ),
            "Accept-Encoding" : "gzip"
        }
    
    def rank_text(self, text:str):
        length_score = math.log(len(text) + 1) * 200
        sentence_score = text.count(".") * 20
        paragraph_score = text.count("\n") * 5
        digit_penalty = len(re.findall(r"\d", text)) * 15
        symbol_penalty = len(re.findall(r"[|/\\=<>_{}<>@#$^*_+=~`[\]]", text)) * 20
        short_word_pen = len(re.findall(r"\b\w{1,2}\b", text)) * 5

        entropy = self.word_entropy(text)
        entropy_pen = 0 if entropy > 2.5 else (2.5 - entropy) * 300

        return length_score + sentence_score + paragraph_score - digit_penalty - symbol_penalty - short_word_pen - entropy_pen
    
    def clean_text(self, text:str):
        text = re.sub(r"https?://[^\s]+", "", text) # URLs, keep line breaks also
        text = re.sub(r"[.!?]{2,}", ".", text) # remove the trailing .s
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
        return " ".join(line.rstrip(".!?") + "." for line in lines)
    
    def word_entropy(self, text:str):
        words = text.lower().split()
        if len(words) < 10:
            return 0
        counts = Counter(words)
        total = len(words)
        return -1 * sum((c / total) * math.log2(c / total) for c in counts.values())
    
    def normalized_hash(self, text:str):
        t = text.lower()
        t = re.sub(r"\s+", " ", t)
        t = re.sub(r"[^\w\s]", "", t)
        return hashlib.sha1(t.encode()).hexdigest()
    
    def identify_code_css(self, text:str):
        css_tokens = re.findall(r"[.#][a-zA-Z_-]+", text)
        css_ratio = len(css_tokens) / max(len(text.split()), 1)
        symb_ratio = len(re.findall(r"[{};:]", text)) / max(len(text), 1)
        id_ratio = len(re.findall(r"\b[a-z]+(?:-[a-z]+)+\b|\b[a-z]+(?:_[a-z]+)+\b", text)) / max(len(text.split()), 1)
        return css_ratio > 0.15 or symb_ratio > 0.02 or id_ratio > 0.2

    def evaluate(self):
        page_info = self.top_links("agriculture in tamil nadu")
        html_pages = [requests.get(l.href, timeout=10, headers=self.create_header()) for l in page_info]
        text_strainer = bs4.SoupStrainer(["article", "section", "div", "main", "h1", "h2", "h3"])#, class_=[re.compile("content")])
        
        soups = []
        for page, info in zip(html_pages, page_info):
            soup = bs4.BeautifulSoup(page.text, features="lxml", parse_only=text_strainer)

            for bad in soup.find_all(["style", "script", "noscript"]):
                bad.decompose()
            soups.append((soup, info.title, info.href))

        splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap=80, add_start_index=True)

        hash_counter = Counter()
        chunks = []

        for soup in soups:
            for tag in soup[0].find_all(True):
                cleaned_text = self.clean_text(tag.get_text(" ", strip=True))
                if len(cleaned_text) < 400:
                    continue
                raw_chunks = splitter.split_text(cleaned_text)
                for c in raw_chunks:
                    if(self.identify_code_css(c)):
                        continue
                    h = self.normalized_hash(c)
                    hash_counter[h] += 1
                    chunks.append(TextData(text=c, title=soup[1], href=soup[2]))
        
        candidates = []
        for chunk in chunks:
            h = self.normalized_hash(chunk.text)
            if hash_counter.get(h, 0) > 3:
                continue
            score = self.rank_text(chunk.text)
            heapq.heappush(candidates, (-1 * score, next(counter), chunk))

        docs = []
        src_chunk_nums = 20
        sources_cnt = {i.href : src_chunk_nums for i in page_info}
        # print(sources_cnt)
        seen = set()
        # print(len(candidates))

        while len(candidates):
            popped_elem = heapq.heappop(candidates)[2]
            if sources_cnt.get(popped_elem.href) is not None:
                if sources_cnt.get(popped_elem.href) >= 0:
                    key = (popped_elem.href, self.normalized_hash(popped_elem.text))
                    if key in seen:
                        continue
                    seen.add(key)
                    sources_cnt[popped_elem.href] -= 1
                    docs.append(
                        Document(
                            page_content=popped_elem.text,
                            metadata={
                                "source" : popped_elem.href,
                                "title" : popped_elem.title
                            }
                        )
                    )

        embeddings = OllamaEmbeddings(
            model = "all-minilm",
            base_url=os.getenv("OLLAMA_URL")
        )

        vector_store = Chroma(
            collection_name="example_collection",
            embedding_function=embeddings,
            persist_directory="chroma_langchain_db"
        )

        document_ids = vector_store.add_documents(documents=docs)
        # print(document_ids[:3])

        @tool(response_format="content_and_artifact")
        def retrieve_context(query:str):
            """Retrieve information to help answer a query."""
            retrieved_docs = vector_store.similarity_search(query, k=2)
            serealized = "\n\n".join(
                (f"Source : {doc.metadata} \n Content:{doc.page_content}")
                for doc in retrieved_docs
            )
            return serealized, retrieved_docs
        
        tools = [retrieve_context]
        prompt = (
            "You have access to a tool that retrieves context from the internet."
            "Use the tool to help answer queries."
        )

        chat_model = ChatOllama(
            model=os.getenv("LLM_AS_JUDGE_MODEL"),
            base_url=os.getenv("OLLAMA_URL"),
            disable_streaming=False
        )

        agent = create_agent(chat_model, tools=tools, system_prompt=prompt)

        query = (
            "Give me recent information about agriculture in Rajasthan."
            "Once you get the answer, lookup some more information on rainwater harvesting in india."
        )

        for event in agent.stream(
            {"messages" : [{"role" : "user", "content": query}]},
            stream_mode="values",
        ):
            event["messages"][-1].pretty_print()


clean = InfoRetrieve()
clean.evaluate()