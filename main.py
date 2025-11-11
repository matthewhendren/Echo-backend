from fastapi import FastAPI
from pydantic import BaseModel
import trafilatura, requests, os
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class Body(BaseModel):
    url: str

@app.get("/")
def root():
    return {"ok": True}

@app.post("/summarize")
def summarize(body: Body):
    # 1) fetch web page
    html = requests.get(body.url, timeout=15).text

    # 2) extract readable article text
    text = trafilatura.extract(html) or ""
    if not text.strip():
        text = f"URL only: {body.url}"

    # 3) summarize (short, listenable)
    prompt = f"""
Summarize this web page for listening.
Keep it 4–6 short sentences, plain English.
Then add 3 bullet key points.
Text:
{text[:12000]}
"""
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )
    summary = resp.choices[0].message.content.strip()
    return {"summary": summary}
