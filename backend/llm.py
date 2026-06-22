import os, json, time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.environ.get("GROQ_API_KEY", ""),
                base_url="https://api.groq.com/openai/v1")

# Primary, then fallback if the primary is over capacity / rate limited.
MODELS = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile"]
TRANSIENT = ("503", "over capacity", "rate limit", "429", "timeout", "temporarily", "overloaded")

def chat(system: str, user: str, temperature: float = 0.3) -> str:
    last_err = None
    for model in MODELS:
        for attempt in range(3):
            try:
                resp = client.chat.completions.create(
                    model=model, temperature=temperature,
                    response_format={"type": "json_object"},
                    messages=[{"role": "system", "content": system},
                              {"role": "user", "content": user}],
                )
                return resp.choices[0].message.content
            except Exception as e:
                last_err = e
                if any(k in str(e).lower() for k in TRANSIENT):
                    time.sleep(2 ** attempt)   # 1s, 2s, 4s, then try next model
                    continue
                break  # non-transient: don't hammer, move to fallback model
    raise last_err

def parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    s, e = text.find("{"), text.rfind("}")
    if s != -1 and e != -1:
        text = text[s:e+1]
    return json.loads(text)