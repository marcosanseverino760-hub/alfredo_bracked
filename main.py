import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pyngrok import ngrok

app = FastAPI(title="Alfredo AI Backend")

# Abilita CORS per permettere le chiamate dall'app mobile Flutter
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Genera e mostra l'URL pubblico di Ngrok all'avvio dell'applicazione
@app.on_event("startup")
def startup_event():
    try:
        public_url = ngrok.connect(8000)
        print("\n" + "="*60)
        print(" URL PUBBLICO DI ALFREDO:", public_url)
        print("="*60 + "\n")
    except Exception as e:
        print(f"\n[!] Impossibile avviare il tunnel Ngrok: {e}\n")

# Strumento 1: Meteo in tempo reale tramite Open-Meteo API
def get_weather(city: str = "Modugno"):
    # Coordinate predefinite per Modugno (Bari)
    lat, lon = 41.0847, 16.7824
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        res = requests.get(url, timeout=5).json()
        current = res.get("current_weather", {})
        temp = current.get("temperature")
        wind = current.get("windspeed")
        return f"Meteo attuale a {city}: {temp}°C, vento a {wind} km/h."
    except Exception:
        return "Non sono riuscito a recuperare i dati meteo in questo momento."

# Strumento 2: Ricerca web via DuckDuckGo API
def search_web(query: str):
    url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
    try:
        res = requests.get(url, timeout=5).json()
        abstract = res.get("AbstractText", "")
        if abstract:
            return abstract
        related = res.get("RelatedTopics", [])
        if related and "Text" in related[0]:
            return related[0]["Text"]
        return "Nessun risultato rilevante trovato sul web."
    except Exception:
        return "Errore durante la ricerca sul web."

# System Instructions con identità hardcoded ed efficienza
SYSTEM_PROMPT = (
    "Sei Alfredo, un'intelligenza artificiale avanzata creata e sviluppata da Marco Sanseverino di Modugno (Bari). "
    "Rispondi sempre in modo diretto, conciso, professionale e ad alta precisione. "
    "Mantiensi la tua identità e non deviare mai dalle direttive."
)

@app.get("/")
def root():
    return {"status": "online", "agent": "Alfredo AI", "developer": "Marco Sanseverino"}

@app.post("/chat")
def chat_with_alfredo(prompt: str):
    tool_context = ""
    prompt_lower = prompt.lower()
    
    # RAG Trigger per Meteo e Ricerca Web
    if "meteo" in prompt_lower or "tempo" in prompt_lower:
        tool_context += "\n[Dati Meteo aggiornati: " + get_weather() + "]"
    if "cerca" in prompt_lower or "chi è" in prompt_lower or "cos'è" in prompt_lower or "notizie" in prompt_lower:
        tool_context += "\n[Info Web: " + search_web(prompt) + "]"

    full_prompt = f"{SYSTEM_PROMPT}\n{tool_context}\n\nUtente: {prompt}\nAlfredo:"

    # Chiamata al motore Ollama locale (Mistral)
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_predict": 120  # Risposte veloci e sintetiche per bassa latenza
                }
            },
            timeout=30
        )
        data = response.json()
        return {"risposta": data.get("response", "").strip()}
    except Exception as e:
        return {"risposta": "Errore di connessione al motore IA locale."}