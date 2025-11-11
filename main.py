from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, os, trafilatura
from openai import OpenAI
from bs4 import BeautifulSoup

# ----------------------------------------------------------
# APP SETUP
# ----------------------------------------------------------
app = FastAPI()

# Allow connections from your iPhone Shortcut, Hoppscotch, etc.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# ----------------------------------------------------------
# MODELS
# ----------------------------------------------------------
class PageInput(BaseModel):
    url: str


# ----------------------------------------------------------
# ROUTES
# ----------------------------------------------------------
@app.get("/")
def root():
    return {"ok": True, "message": "Echo API is running 🚀"}


@app.post("/summarize")
def summarize(body: PageInput):
    # Step 1: Fetch HTML
    try:
        response = requests.get(body.url, timeout=15)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        return {"summary": f"Could not fetch the webpage: {str(e)}"}

    # Step 2: Try Trafilatura
    text = trafilatura.extract(html)

    # Step 3: Fallback to BeautifulSoup if needed
    if not text or len(text.strip()) < 200:
        soup = BeautifulSoup(html, "html.parser")
        paragraphs = [p.get_text() for p in soup.find_all("p")]
        text = " ".join(paragraphs)

    if not text.strip():
        return {"summary": "No readable text found on that webpage."}

    # Step 4: Build prompt
    prompt = f"""
    Summarize this webpage in 4–6 short sentences that sound natural when spoken aloud.
    Keep it concise and friendly. Then provide 2–3 quick key points at the end.
    TEXT:
    {text[:12000]}
    """

    # Step 5: Summarize with OpenAI
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",  # fast + affordable
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        summary = resp.choices[0].message.content.strip()
        return {"summary": summary}

    except Exception as e:
        return {"summary": f"Error during summarization: {str(e)}"}


# ----------------------------------------------------------
# ENTRY POINT FOR RENDER
# ----------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
