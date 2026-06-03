from __future__ import annotations

import json
import os
import re
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage


def get_chat_model(tier: str = "gpt-4.1-mini") -> BaseChatModel | None:
    provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
    if provider in ("heuristic", "none", "disabled"):
        return None
    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None
        from langchain_openai import ChatOpenAI

        model = tier if tier.startswith("gpt") else "gpt-4.1-mini"
        return ChatOpenAI(model=model, temperature=0, max_retries=3)
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        model = "qwen2.5:7b" if "mini" in tier or "nano" in tier else "llama3.1:8b"
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(model=model, base_url=base_url, temperature=0)
    return None


async def invoke_json(prompt: str, tier: str = "gpt-4.1-mini") -> dict[str, Any]:
    llm = get_chat_model(tier)
    if llm is None:
        return {}
    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
    except Exception:
        return {}
    content = str(response.content)
    match = re.search(r"\{[\s\S]*\}", content)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return {"raw": content}
    return {"raw": content}
