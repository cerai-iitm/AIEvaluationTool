from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

template = """Question: {question}

Answer: Let's think step by step."""

prompt = ChatPromptTemplate.from_template(template)
print("Sending a request to Ollama..")
model = OllamaLLM(model="llama3.1", base_url="http://10.21.186.219:11434")

chain = prompt | model

print(chain.invoke({"question": "What is LangChain?"}))
