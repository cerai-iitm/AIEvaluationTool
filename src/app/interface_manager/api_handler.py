import time
from typing import Dict, Any, List

from context import APIRuntimeContext
from logger import get_logger

from openai import OpenAI
from google import genai

logger = get_logger("interface_manager")


def handle_api_chat(
    ctx: APIRuntimeContext,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Executes one API chat request and returns a normalized response.
    """

    # --------------------------------------------------
    # Driver lifecycle start
    # --------------------------------------------------
    logger.info("Driver is ready for API")

    start_ts = time.time()

    prompts: List[str] = payload.get("prompt_list", [])
    prompt = " ".join(prompts).strip()

    if not prompt:
        logger.error("Empty prompt_list received")
        raise ValueError("Empty prompt_list received")

    logger.info("Sending prompt to the bot: %s", prompt)

    logger.info(
        "API chat started | provider=%s model=%s",
        ctx.provider,
        ctx.agent_name,
    )

    try:
        # --------------------------------------------------
        # Dispatch by provider
        # --------------------------------------------------
        if ctx.is_openai():
            text = _run_openai(ctx, prompt)

        elif ctx.is_gemini():
            text = _run_gemini(ctx, prompt)

        elif ctx.is_local():
            text = _run_local(ctx, prompt)

        else:
            raise RuntimeError(f"Unsupported provider: {ctx.provider}")

        elapsed = int(time.time() - start_ts)

        logger.info(
            "(Waited:%d) Received response from API (%s): %s",
            elapsed,
            ctx.agent_name,
            text,
        )

        logger.info(
            "API chat completed | chars=%d time=%ss",
            len(text),
            round(time.time() - start_ts, 3),
        )

        return {
            "response": [
                {"response": text}
            ]
        }

    finally:
        # --------------------------------------------------
        # Driver lifecycle end (always runs)
        # --------------------------------------------------
        logger.info("Driver quit successfully")


# ------------------------------------------------------------------
# Provider implementations
# ------------------------------------------------------------------

def _run_openai(ctx: APIRuntimeContext, prompt: str) -> str:
    logger.info("Calling OpenAI API | model=%s", ctx.agent_name)

    client = OpenAI()

    response = client.chat.completions.create(
        model=ctx.agent_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=ctx.temperature,
        max_tokens=ctx.max_tokens,
        top_p=ctx.top_p,
    )

    return response.choices[0].message.content.strip()


def _run_gemini(ctx: APIRuntimeContext, prompt: str) -> str:
    logger.info("Calling Gemini API | model=%s", ctx.agent_name)

    client = genai.Client()

    response = client.models.generate_content(
        model=ctx.agent_name,
        contents=prompt,
    )

    return response.text.strip()


def _run_local(ctx: APIRuntimeContext, prompt: str) -> str:
    logger.info(
        "Calling LOCAL OpenAI-compatible API | model=%s base_url=%s",
        ctx.agent_name,
        ctx.base_url,
    )

    if not ctx.base_url:
        raise RuntimeError("LOCAL provider requires base_url")

    client = OpenAI(
        base_url=f"{ctx.base_url.rstrip('/')}/v1",
        api_key="local",   # required but unused
    )

    response = client.chat.completions.create(
        model=ctx.agent_name,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content.strip()
