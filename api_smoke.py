"""
Minimal API smoke test for LLM settings in config.yaml.
"""

import os
import time
import yaml
from openai import OpenAI


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    config = load_config()
    model = config.get("model")
    base_url = config.get("base_url")
    api_key = config.get("api_key")

    missing = [k for k, v in [("model", model), ("base_url", base_url), ("api_key", api_key)] if not v]
    if missing:
        print(f"Missing required config fields: {', '.join(missing)}")
        raise SystemExit(1)

    print("Starting API smoke test...")
    print(f"model={model}")
    print(f"base_url={base_url}")
    print(f"api_key={'*' * 8}...{str(api_key)[-4:]}")

    client = OpenAI(api_key=api_key, base_url=base_url)
    prompt = "Reply with exactly: API OK"

    started = time.time()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            stream=False,
        )
    except Exception as e:
        elapsed = time.time() - started
        print(f"API test failed after {elapsed:.2f}s")
        print(f"Error: {e}")
        raise SystemExit(2)

    elapsed = time.time() - started
    content = (resp.choices[0].message.content or "").strip()
    print(f"API test succeeded in {elapsed:.2f}s")
    print(f"Response: {content}")


if __name__ == "__main__":
    main()
