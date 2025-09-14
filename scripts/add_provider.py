#!/usr/bin/env python3
"""
Enhanced interactive script to add a new news provider (one-shot):
  * Prompts for core metadata (name, url, topics, enabled)
  * Updates config/providers.json
  * Generates provider module with fetch_articles() (compatible with runner)
  * Optional: LLM-assisted provider code generation (OpenAI or local) via --use-llm flag

Run examples:
  uv run python scripts/add_provider.py
  uv run python scripts/add_provider.py --use-llm --llm-provider openai --model gpt-4o-mini
  uv run python scripts/add_provider.py --non-interactive \
      --name foxnews --url https://moxie.foxnews.com/google-publisher/latest.xml \
      --topics general,politics,world
"""

import json, os, sys, argparse, textwrap
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config" / "providers.json"
PROVIDERS_DIR = ROOT / "providers"

# Default minimal template (no LLM)
BASIC_TEMPLATE = '''"""Provider for {name}"""
import logging
import feedparser
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

PRIMARY_TOPIC = "sport"

def fetch_articles() -> List[Dict[str, Any]]:
    """Fetch articles for provider '{name}'."""
    url = "{url}"
    logger.info("Fetching {name} RSS from %s", url)
    d = feedparser.parse(url)
    entries = d.entries or []
    articles: List[Dict[str, Any]] = []
    for entry in entries{limit_slice}:
        try:
            articles.append({{
                "title": (entry.get("title") or "").strip(),
                "url": entry.get("link"),
                "content": entry.get("summary") or entry.get("description") or "",
                "published_at": entry.get("published") or entry.get("updated") or "",
                "topic": PRIMARY_TOPIC,
            }})
        except Exception as e:  # defensive
            logger.warning("Error parsing entry: %s", e)
            continue
    logger.info("Successfully fetched %d articles from {name}", len(articles))
    return articles
'''

# Prompt helpers

def prompt(msg, default=None, required=True):
    if default:
        full = f"{msg} [{default}]: "
    else:
        full = f"{msg}: "
    while True:
        val = input(full).strip()
        if not val and default is not None:
            return default
        if val or not required:
            return val
        print("Value required.")

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
        f.write("\n")

def write_provider_file(name: str, code: str):
    PROVIDERS_DIR.mkdir(exist_ok=True)
    path = PROVIDERS_DIR / f"{name}.py"
    if path.exists():
        print("Provider module already exists, overwriting (backup manually if needed)...")
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"Created/Updated {path.relative_to(ROOT)}")

# LLM support

def generate_with_llm(name: str, url: str, topics: List[str], model: str, provider: str):
    prompt_text = textwrap.dedent(f"""
    You are an assistant that generates a Python provider module for a news aggregation system.
    Requirements:
    - Provide a function fetch_articles() -> List[Dict[str, Any]] with no arguments.
    - Use feedparser to parse the RSS feed: {url}
    - Include logging.
    - Set 'topic' for each article. Primary topic: {topics[0] if topics else 'general'}
    - Keep code concise and robust; catch per-entry errors.
    - No external network calls beyond feedparser.parse(url).
    - Do NOT add execution code under if __name__ == '__main__'.
    Provider internal name: {name}
    """).strip()

    def _call_openai():
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You write clean Python modules."},
                {"role": "user", "content": prompt_text},
            ],
            temperature=0.4,
        )
        return resp.choices[0].message.content.strip()

    def _call_mistral():
        # Assumes Ollama / compatible local endpoint returning {'response': '...'} or OpenAI-like.
        import requests, json
        endpoint = os.getenv("MISTRAL_ENDPOINT", "http://localhost:11434/api/generate")
        mistral_model = os.getenv("MISTRAL_MODEL", "mistral")
        payload = {
            "model": mistral_model,
            "prompt": prompt_text,
            "stream": False,
            "options": {"temperature": 0.4}
        }
        r = requests.post(endpoint, json=payload, timeout=90)
        r.raise_for_status()
        data = r.json()
        # Ollama format uses 'response'; adjust if different.
        return (data.get("response") or data.get("text") or "").strip()

    # Provider modes:
    #   openai   -> only OpenAI
    #   mistral  -> only local mistral
    #   auto     -> try OpenAI then mistral
    provider = (provider or "openai").lower()
    if provider == "openai":
        try:
            return _call_openai()
        except Exception as e:
            print(f"[LLM WARNING] OpenAI generation failed: {e}; falling back to basic template.")
            return None
    elif provider == "mistral":
        try:
            return _call_mistral()
        except Exception as e:
            print(f"[LLM WARNING] Mistral generation failed: {e}; falling back to basic template.")
            return None
    elif provider == "auto":
        # Try OpenAI first, then Mistral
        try:
            return _call_openai()
        except Exception as e:
            print(f"[LLM INFO] OpenAI failed ({e}); trying Mistral...")
            try:
                return _call_mistral()
            except Exception as e2:
                print(f"[LLM WARNING] Mistral also failed ({e2}); using basic template.")
                return None
    else:
        print(f"[LLM WARNING] Unknown LLM provider '{provider}'; using basic template.")
        return None


def build_basic_code(name: str, url: str, topics: List[str], limit: int | None):
    primary_topic = topics[0] if topics else "general"
    limit_slice = f"[:{limit}]" if limit else ""
    return BASIC_TEMPLATE.format(
        name=name, url=url, primary_topic=primary_topic, limit_slice=limit_slice
    )


def parse_args():
    p = argparse.ArgumentParser(description="Add a news provider (one-shot)")
    p.add_argument("--use-llm", action="store_true", help="Use LLM to generate provider code")
    p.add_argument("--llm-provider", default="auto",
                   choices=["auto", "openai", "mistral", "local"],
                   help="LLM backend selection order / type")
    p.add_argument("--model", default="gpt-4o-mini", help="LLM model name (OpenAI). Mistral uses MISTRAL_MODEL env.")
    p.add_argument("--non-interactive", action="store_true", help="Use flags instead of prompts")
    p.add_argument("--name", help="Provider internal name (lowercase)")
    p.add_argument("--url", help="Feed URL")
    p.add_argument("--topics", help="Comma separated topics list")
    p.add_argument("--limit", type=int, help="Optional internal limit (applied inside provider file)")
    p.add_argument("--disable", action="store_true", help="Create as disabled")
    return p.parse_args()


def interactive_collect():
    print("=== Add New Provider ===")
    name = prompt("Internal provider name (lowercase, no spaces)")
    url = prompt("Feed/API URL")
    topics_raw = prompt("Topics (comma separated)", default="general", required=False)
    topics = [t.strip() for t in topics_raw.split(',') if t.strip()] or ["general"]
    limit_str = prompt("Default internal limit (blank for none)", default="", required=False)
    limit = int(limit_str) if limit_str.isdigit() else None
    enabled = prompt("Enable now? (y/n)", default="y").lower().startswith("y")
    use_llm = prompt("Generate code with LLM? (y/n)", default="n").lower().startswith("y")
    return {
        "name": name,
        "url": url,
        "topics": topics,
        "limit": limit,
        "enabled": enabled,
        "use_llm": use_llm,
    }


def non_interactive_collect(args):
    missing = [k for k in ["name", "url"] if not getattr(args, k)]
    if missing:
        print(f"Missing required flags for non-interactive mode: {', '.join(missing)}")
        sys.exit(1)
    topics = []
    if args.topics:
        topics = [t.strip() for t in args.topics.split(',') if t.strip()]
    if not topics:
        topics = ["general"]
    return {
        "name": args.name,
        "url": args.url,
        "topics": topics,
        "limit": args.limit,
        "enabled": not args.disable,
        "use_llm": args.use_llm,
    }


def clean_llm_code(raw: str, name: str, url: str, primary_topic: str) -> str:
    """Strip markdown fences and fallback if no fetch_articles found."""
    if not raw:
        return ""
    lines = raw.strip().splitlines()
    code_lines = []
    in_block = False
    for ln in lines:
        t = ln.strip()
        if t.startswith("```"):
            if in_block:
                in_block = False
            else:
                if "python" in t.lower() or t == "```":
                    in_block = True
            continue
        if in_block:
            code_lines.append(ln)
    candidate = "\n".join(code_lines).strip() if code_lines else "\n".join(
        [l for l in lines if not l.lower().startswith("here")])
    if "def fetch_articles" not in candidate:
        candidate += f"""

import logging, feedparser
from typing import List, Dict, Any
logger = logging.getLogger(__name__)
FEED_URL = "{url}"
PRIMARY_TOPIC = "{primary_topic}"

def fetch_articles() -> List[Dict[str, Any]]:
    logger.info("Fetching {name} RSS from %s", FEED_URL)
    d = feedparser.parse(FEED_URL)
    articles: List[Dict[str, Any]] = []
    for entry in d.entries or []:
        articles.append({{
            "title": (entry.get("title") or "").strip(),
            "url": entry.get("link"),
            "content": entry.get("summary") or entry.get("description") or "",
            "published_at": entry.get("published") or entry.get("updated") or "",
            "topic": PRIMARY_TOPIC,
        }})
    return articles
"""
    return candidate.strip()


def main():
    args = parse_args()
    data = non_interactive_collect(args) if args.non_interactive else interactive_collect()

    name = data["name"].lower()
    url = data["url"].strip()
    topics = data["topics"]
    limit = data["limit"]
    enabled = data["enabled"]
    use_llm = data["use_llm"] or args.use_llm

    cfg = load_config()
    if name in cfg:
        print("Provider already defined in config/providers.json")
        return

    # Update config object
    cfg[name] = {
        "module": name,
        "type": "rss",
        "url": url,
        "enabled": enabled,
        "topics": topics,
    }
    if limit:
        cfg[name]["limit"] = limit

    # Generate code
    code = None
    if use_llm:
        raw = generate_with_llm(name, url, topics, args.model, args.llm_provider)
        if raw:
            code = clean_llm_code(raw, name, url, topics[0] if topics else "general")
    if not code:
        code = build_basic_code(name, url, topics, limit)

    # Persist
    save_config(cfg)
    write_provider_file(name, code)

    print("\nSummary:")
    print(f"  Name     : {name}")
    print(f"  URL      : {url}")
    print(f"  Topics   : {', '.join(topics)}")
    print(f"  Enabled  : {enabled}")
    if limit:
        print(f"  Limit    : {limit}")
    print("  LLM Code : " + ("yes" if use_llm and code else "no (basic template)"))

    print("\nTest with (fetch only, no send):")
    print(f"uv run python main.py --providers {name} --limit 3 --title-only --send-telegram --dry-run")

if __name__ == "__main__":
    main()
