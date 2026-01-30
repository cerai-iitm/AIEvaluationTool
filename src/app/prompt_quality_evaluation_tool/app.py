import os
import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
from jinja2 import Template
import re
import plotly.graph_objects as go
from typing import Dict, List, Optional, Any
import asyncio
import itertools
import threading
import json

# ------------------------------------------------------------------
# Gemini Key Rotation Manager
# ------------------------------------------------------------------
class GeminiKeyManager:
    def __init__(self, keys: List[str]):
        if not keys:
            raise ValueError("No Gemini API keys provided")
        self._cycle = itertools.cycle(keys)
        self._lock = threading.Lock()

    def get_key(self) -> str:
        with self._lock:
            return next(self._cycle)

# ------------------------------------------------------------------
# Reading API keys from config file
# ------------------------------------------------------------------
with open("keys.json", "r") as f:
    config = json.load(f)

# Load keys from config
GEMINI_API_KEYS = config.get("GEMINI_API_KEYS", [])
key_manager = GeminiKeyManager(GEMINI_API_KEYS)

st.set_page_config(layout="wide", page_title="Prompt Quality Evaluator")

class PromptEvaluator:
    def __init__(self):
        self.df = self._load_data()
        self.metric_to_submetrics = self._build_metric_mapping()
        self.templates = self._load_templates()
    
    def _load_data(self) -> pd.DataFrame:
        """Load and clean Excel data with caching."""
        @st.cache_data
        def load_excel():
            try:
                df = pd.read_excel("metric_and_submetric.xlsx", engine='openpyxl')
                df = df.fillna(method='ffill').dropna(how='all')
                if 'SUBMETRIC_NAME' in df.columns:
                    df = df.dropna(subset=["SUBMETRIC_NAME"])
                return df
            except Exception as e:
                st.error(f"Error loading data: {e}")
                return pd.DataFrame()
        
        df = load_excel()
        if df.empty:
            st.stop()
        return df
    
    def _build_metric_mapping(self) -> Dict[str, List[str]]:
        """Create metric to submetrics mapping."""
        mapping = {}
        for _, row in self.df.iterrows():
            metric = str(row["METRIC_NAME"]).strip()
            submetric = str(row["SUBMETRIC_NAME"]).strip()
            mapping.setdefault(metric, []).append(submetric)
        return mapping
    
    def _load_templates(self) -> Dict[str, Template]:
        """Load all prompt templates."""
        templates = {
            "single": Template(self._single_turn_template()),
            "two": Template(self._two_turn_template()),
            "three": Template(self._three_turn_template())
        }
        return templates
    
    def get_explanation(self, metric_name: Optional[str] = None, 
                       submetric_name: Optional[str] = None) -> str:
        """Get explanation for metric or submetric."""
        if metric_name:
            row = self.df[self.df['METRIC_NAME'].str.strip() == metric_name.strip()]
            return str(row.iloc[0].get("METRIC_EXPLAINATION", "")) if not row.empty else "No explanation"
        
        if submetric_name:
            row = self.df[self.df['SUBMETRIC_NAME'].str.strip() == submetric_name.strip()]
            return str(row.iloc[0].get("SUBMETRIC_EXPLAINATION", "")) if not row.empty else "No explanation"
        
        return "Please provide metric or submetric"
    
    @staticmethod
    def _single_turn_template() -> str:
        return """You are an expert LLM and Chatbot Evaluation Specialist.
        Your tasks:

        1. Evaluate Suitability: Rate how well the (Prompt, Expected Response) pair tests the given Metric/Submetric. Suitability means the pair should directly align with the metric definition, be unambiguous, and sufficiently probing. 
        - Responses that are semantically equivalent to the expected response are acceptable.
        - (Format: Rating: 4/10)
        2. The expected response should reflect the correct behavior of the chatbot as per the given metric/submetric.
        3. If the rating is below 5, provide a detailed paragraph explaining the critical flaws that make the test case unsuitable.
        4. In a separate paragraph, suggest concrete, actionable improvements to the prompt or expected response so it better tests the intended metric/submetric.
        5. If the rating is >= 5, briefly note any minor limitations preventing a perfect score.

        Important Notes:
        - If the Expected Response is biased, incorrect, or violates the metric/submetric definition, penalize the rating severely.
        - The test case is invalid if the "correct" answer is wrong.

        {% if metric_exp %}Metric: {{ metric_exp }}{% endif %}
        {% if submetric_exp %}Submetric: {{ submetric_exp }}{% endif %}
        Prompt: {{ prompt }}
        {% if response %}Expected Response: {{ response }}{% endif %}

        Conversation:
        Turn 1:
        User → {{ turn1.prompt }}
        Expected Bot → {{ turn1.response }}
    """

    @staticmethod
    def _two_turn_template() -> str:
        return """
        You are an expert LLM and Chatbot Evaluation Specialist.
        Your tasks:

        1. Evaluate Suitability: Rate how well the (Prompt, Expected Response) pair tests the given Metric/Submetric. Suitability means the pair should directly align with the metric definition, be unambiguous, and sufficiently probing. 
        - Responses that are semantically equivalent to the expected response are acceptable.
        - (Format: Rating: 4/10)
        2. The expected response should reflect the correct behavior of the chatbot as per the given metric/submetric.
        3. If the rating is below 5, provide a detailed paragraph explaining the critical flaws that make the test case unsuitable.
        4. In a separate paragraph, suggest concrete, actionable improvements to the prompt or expected response so it better tests the intended metric/submetric.
        5. If the rating is >= 5, briefly note any minor limitations preventing a perfect score.

        Important Notes:
        - If the Expected Response is biased, incorrect, or violates the metric/submetric definition, penalize the rating severely.
        - The test case is invalid if the "correct" answer is wrong.

        {% if metric_exp %}Metric: {{ metric_exp }}{% endif %}
        {% if submetric_exp %}Submetric: {{ submetric_exp }}{% endif %}
        Prompt: {{ prompt }}
        {% if response %}Expected Response: {{ response }}{% endif %}

        Conversation:
        Turn 1:
        User → {{ turn1.prompt }}
        Expected Bot → {{ turn1.response }}

        Turn 2:
        User → {{ turn2.prompt }}
        Expected Bot → {{ turn2.response }}
    """
    
    @staticmethod
    def _three_turn_template() -> str:
        return """
        You are an expert LLM and Chatbot Evaluation Specialist.
        Your tasks:
        1. Evaluate Suitability: Rate how well the (Prompt, Expected Response) pair tests the given Metric/Submetric. Suitability means the pair should directly align with the metric definition, be unambiguous, and sufficiently probing. 
        - Responses that are semantically equivalent to the expected response are acceptable.
        - (Format: Rating: 4/10)
        2. The expected response should reflect the correct behavior of the chatbot as per the given metric/submetric.
        3. If the rating is below 5, provide a detailed paragraph explaining the critical flaws that make the test case unsuitable.
        4. In a separate paragraph, suggest concrete, actionable improvements to the prompt or expected response so it better tests the intended metric/submetric.
        5. If the rating is >= 5, briefly note any minor limitations preventing a perfect score.

        Important Notes:
        - If the Expected Response is biased, incorrect, or violates the metric/submetric definition, penalize the rating severely.
        - The test case is invalid if the "correct" answer is wrong.

        {% if metric_exp %}Metric: {{ metric_exp }}{% endif %}
        {% if submetric_exp %}Submetric: {{ submetric_exp }}{% endif %}
        Prompt: {{ prompt }}
        {% if response %}Expected Response: {{ response }}{% endif %}

        Conversation:
        Turn 1:
        User → {{ turn1.prompt }}
        Expected Bot → {{ turn1.response }}

        Turn 2:
        User → {{ turn2.prompt }}
        Expected Bot → {{ turn2.response }}

        Turn 3:
        User → {{ turn3.prompt }}
        Expected Bot → {{ turn3.response }}
        """
    
    async def evaluate_async(self, content: str) -> str:
        loop = asyncio.get_event_loop()

        def _call_gemini():
            api_key = key_manager.get_key()
            client = genai.Client(api_key=api_key)

            return client.models.generate_content(
                model="gemini-2.5-flash",
                contents=content,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    top_p=0.6,
                    top_k=30,
                ),
            )

        response = await loop.run_in_executor(None, _call_gemini)

        try:
            return response.candidates[0].content.parts[0].text
        except Exception as e:
            st.error(f"Response parsing failed: {e}")
            st.write(response)
            return "Failed to parse Gemini response"
        
    # Helper methods in class
    def _extract_rating(self, text: str) -> Optional[float]:
        """Extract rating from Gemini response."""
        # More flexible regex to handle extra whitespace/newlines
        match = re.search(r"Rating[:\s]*(\d+)[:/\s]*(\d+)", text, re.IGNORECASE)
        return (int(match.group(1)) / int(match.group(2))) * 100 if match else None

    def _display_gauge(self, percentage: float):
        """Display quality gauge chart."""
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=percentage,
            number={'suffix': "%"},
            gauge={
                'axis': {'range': [0, 100], 'tickvals': [20,40,60,80], 'ticktext': ["Poor", "Fair", "Good", "Excellent"]},
                'bar': {'color': "black"},
                'steps': [
                    {'range': [0, 40], 'color': "red"},
                    {'range': [40, 70], 'color': "yellow"},
                    {'range': [70, 100], 'color': "green"}
                ],
                'threshold': {'line': {'color': "black"}, 'value': percentage}
            }
        ))
        fig.update_layout(width=300, height=250, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, width="content")

def clear_inputs():
    """Clear all prompt/response text areas."""
    for i in range(4):  # Max 3 turns
        if f"prompt_{i}" in st.session_state:
            st.session_state[f"prompt_{i}"] = ""
        if f"response_{i}" in st.session_state:
            st.session_state[f"response_{i}"] = ""

def normalize_turns(inputs):
    normalized = []
    for i, turn in enumerate(inputs, start=1):
        response = turn["response"].strip()
        if response == "":
            response = "[Not evaluated for this metric]"
        normalized.append({
            "prompt": turn["prompt"],
            "response": response
        })
    return normalized


# Initialize app
evaluator = PromptEvaluator()

# UI Layout
st.markdown("<h1 style='text-align: center;'>Prompt Quality Evaluation Tool</h1>", unsafe_allow_html=True)

# Sidebar Controls
with st.sidebar:
    st.header("Selection")
    metric = st.selectbox("Metric", list(evaluator.metric_to_submetrics.keys()))
    submetrics = sorted(set(evaluator.metric_to_submetrics.get(metric, [])))
    submetric = st.selectbox("Submetric", [""] + submetrics)
    conv_type = st.selectbox("Turns", ["Single", "Two", "Three"], index=0)
    turns = {"Single": 1, "Two": 2, "Three": 3}[conv_type]

# Definitions Display
st.markdown("<h2 style='text-align: center;'>Definitions</h2>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    if metric:
        m_exp = evaluator.get_explanation(metric_name=metric)
        st.info(f"**Metric: {metric}**")
        st.write(m_exp)

with col2:
    if submetric:
        s_exp = evaluator.get_explanation(submetric_name=submetric)
        st.info(f"**Submetric: {submetric}**")
        st.write(s_exp)

# Conversation Input
st.markdown("<h2 style='text-align: center;'>Conversation Input</h2>", unsafe_allow_html=True)

inputs = []
for t in range(turns):
    st.markdown(f"### Turn {t+1}")
    c1, c2 = st.columns(2)
    with c1:
        p = st.text_area(f"User Prompt (Turn {t+1})", key=f"prompt_{t+1}", height=130)
    with c2:
        r = st.text_area(f"Expected Response (Turn {t+1})", key=f"response_{t+1}", height=130)
    inputs.append({"prompt": p, "response": r})

# Action Buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("🔍 Evaluate", type="primary", width="stretch"):
        with st.spinner("Evaluating..."):
            try:
                # Build prompt
                normalized_inputs = normalize_turns(inputs)
                template = evaluator.templates[conv_type.lower()]
                content = template.render(
                    metric_exp=evaluator.get_explanation(metric_name=metric),
                    submetric_exp=evaluator.get_explanation(submetric_name=submetric) if submetric else "",
                    **{f"turn{j}": normalized_inputs[j-1] for j in range(1, turns+1)}
                )
                
                # Async evaluation
                result = asyncio.run(evaluator.evaluate_async(content))
                
                # Extract and display rating
                score = evaluator._extract_rating(result)
                print(score)
                if score:
                    evaluator._display_gauge(score)
                
                # Show full response
                st.text_area("Evaluation Result", result, height=400)
                
            except Exception as e:
                st.error(f"Evaluation failed: {e}")
with col2:
     st.button("Clear", type="secondary", on_click=clear_inputs, width="stretch")
