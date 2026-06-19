import os, json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.environ.get("GROQ_API_KEY", ""),
                base_url="https://api.groq.com/openai/v1")
MODEL = "openai/gpt-oss-120b"

def chat(system: str, user: str, temperature: float = 0.3) -> str:
    resp = client.chat.completions.create(
        model=MODEL, temperature=temperature,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
    )
    return resp.choices[0].message.content

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