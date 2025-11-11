from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, os, trafilatura
from openai import OpenAI

app = FastAPI()

# ✅ Allow requests from anywhere (for Safari Shortcuts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class PageInput(BaseModel):
    url: str

@app.get("/")
def root():
    return {"ok": True, "message": "Echo API running"}

@app.post("/summarize")
def summarize(body: PageInput):
    try:
        html = requests.get(body.url, timeout=15).text
        text = trafilatura.extract(html) or ""
    except Exception:
        return {"summary": "Could not fetch or extract text from that page."}

    if not text:
        return {"summary": "No readable text found on that webpage."}

    prompt = f"""
    Summarize this webpage in 4–6 short sentences suitable to be read aloud.
    Keep it simple and natural:
    {text[:12000]}
    """

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        summary = resp.choices[0].message.content.strip()
        return {"summary": summary}
    except Exception as e:
        return {"summary": f"Error during summarization: {str(e)}"}


# ✅ Ensure Render runs on correct port
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

