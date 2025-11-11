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

# Allow your Shortcut, browser, or Hoppscotch to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow from anywhere
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ----------------------------------------------------------
# DATA MODEL
# ----------------------------------------------------------
class PageInput(BaseModel):
    url: str


# ----------------------------------------------------------
# ROUTES
# ----------------------------------------------------------
@app.get("/")
def root():
    return {"ok": True, "message": "Echo API is live 🚀"}


@app.post("/summarize")
def summarize(body: PageInput):
    # Step 1: Fetch the webpage HTML with browser-style headers
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(body.url, headers=headers, timeout=15)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        return {"summary": f"Could not fetch the webpage: {str(e)}"}

    # Step 2: Try to extract readable text
    text = trafilatura.extract(html)

    # Step 3: Fallback to BeautifulSoup if Trafilatura fails or text too short
    if not text or len(text.strip()) < 200:
        soup = BeautifulSoup(html, "html.parser")
        paragraphs = [p.get_text() for p in soup.find_all("p")]
        text = " ".join(paragraphs)

    if not text.strip():
        return {"summary": "No readable text found on that webpage."}

    # Step 4: Build summarization prompt
    prompt = f"""
    You are Echo, an AI assistant that quickly reads webpages and explains their main point in a few clear sentences. Your job is to save the user time by giving only the essential information — what the page is about, its key facts or takeaway, and nothing extra. Write in plain English, limit your answer to 1–3 sentences max, and do not add commentary, filler, or introductions.
    TEXT:
    {text[:12000]}
    """

    # Step 5: Generate summary with OpenAI
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",   # fast + affordable model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        summary = resp.choices[0].message.content.strip()
        return {"summary": summary}

    except Exception as e:
        return {"summary": f"Error during summarization: {str(e)}"}


# ----------------------------------------------------------
# ENTRY POINT (REQUIRED FOR RENDER)
# ----------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
