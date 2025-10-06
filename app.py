from flask import Flask, render_template, request, session
from ibm_watson import AssistantV2, NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, KeywordsOptions
import requests
from deep_translator import GoogleTranslator

# Try to use langdetect if available (optional but more reliable)
try:
    from langdetect import detect as lang_detect
except Exception:
    lang_detect = None

# ✅ Import hospitals blueprint
from hospitals_api import hospitals_bp

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.register_blueprint(hospitals_bp)

# ---------------- Watson Credentials ----------------
ASSISTANT_APIKEY = '0C7T92wwncphsAHYdLQDHEJbkQT10SrTBILISsdITcIG'
ASSISTANT_URL = 'https://api.au-syd.assistant.watson.cloud.ibm.com'
ASSISTANT_ID = 'ac225b4e-9d7a-4007-a5f5-7ceeba8c7517'
ENVIRONMENT_ID = 'draft'

NLU_APIKEY = 'TVfAEgyyxp2RAv1N8M4j3gtpsZv20ECcYoqA3lnyrPQ5'
NLU_URL = 'https://api.au-syd.natural-language-understanding.watson.cloud.ibm.com/instances/feacb2c5-90ed-45bf-85ff-8a30a8cffd61'

GOOGLE_API_KEY = 'AIzaSyAMrmlM6_qS-4hjQUXeZTbq79Me5xQB3RE'
SEARCH_ENGINE_ID = '479345b95c2b541cb'

# ---------------- Initialize Watson ----------------
assistant_authenticator = IAMAuthenticator(ASSISTANT_APIKEY)
assistant = AssistantV2(version='2021-06-14', authenticator=assistant_authenticator)
assistant.set_service_url(ASSISTANT_URL)

nlu_authenticator = IAMAuthenticator(NLU_APIKEY)
nlu = NaturalLanguageUnderstandingV1(version='2022-04-07', authenticator=nlu_authenticator)
nlu.set_service_url(NLU_URL)

# ---------------- Localized headers ----------------
HEADERS_REC = {
    "es": "✅ Recomendaciones:\n",
    "de": "✅ Empfehlungen:\n",
    "fr": "✅ Recommandations:\n",
    "hi": "✅ सिफारिशें:\n",
    "or": "✅ ସୁପାରିଶ:\n",   # ← added Odia
}
HEADERS_RES = {
    "es": "🔗 Recursos:\n",
    "de": "🔗 Ressourcen:\n",
    "fr": "🔗 Ressources:\n",
    "hi": "🔗 संसाधन:\n",
    "or": "🔗 ସମ୍ପଦ:\n",     # ← added Odia
}

# ---------------- Helpers ----------------
def detect_language_strict(text: str) -> str:
    """
    Try multiple ways to detect language (no external API keys):
    1) langdetect (if installed)
    2) Deep Translator's GoogleTranslator(source='auto') reflection
    3) Simple keyword heuristics
    Default to 'en' as last resort.
    """
    # 1) langdetect
    if lang_detect:
        try:
            code = lang_detect(text)
            if code:
                return code
        except Exception:
            pass

    # 2) Deep Translator reflection
    try:
        t = GoogleTranslator(source='auto', target='en')
        _ = t.translate(text)  # forces detection
        code = getattr(t, "_source", None) or getattr(t, "source", None)
        if code and code != "auto":
            return code
    except Exception:
        pass

    # 3) Heuristics (very simple, common words)
    lowered = text.lower()
    de_hits = any(w in lowered for w in ["ich", "habe", "und", "mit", "brustschmerzen", "fieber"])
    es_hits = any(w in lowered for w in ["tengo", "dolor", "fiebre", "cabeza", "pecho"])
    fr_hits = any(w in lowered for w in ["j'ai", "fièvre", "tête", "douleur", "poitrine"])
    hi_hits = any(w in lowered for w in ["मुझे", "खांसी", "बुखार", "सीने", "दर्द"])
    # Odia (Oriya) – check in native script
    or_hits = any(w in text for w in ["ମୁଁ", "ଜ୍ୱର", "ବେଦନା", "ଛାତି", "ମୁଣ୍ଡବଥା"])

    if de_hits: return "de"
    if es_hits: return "es"
    if fr_hits: return "fr"
    if hi_hits: return "hi"
    if or_hits: return "or"   # ← added Odia

    return "en"

def google_search(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"q": query, "key": GOOGLE_API_KEY, "cx": SEARCH_ENGINE_ID}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        items = r.json().get('items', [])[:2]
        return [f"{it['title']} - {it['link']}" for it in items]
    except Exception:
        return []

# ---------------- Chatbot Route ----------------
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'history' not in session:
        session['history'] = []

    watson_reply = ""
    recommendation_block = ""

    if request.method == 'POST':
        user_input = (request.form.get('message') or '').strip()
        if not user_input:
            return render_template('index.html',
                                   history=session['history'],
                                   recommendation=recommendation_block,
                                   watson_reply="(empty message)")

        # 🔥 Strict language detection
        detected_lang = detect_language_strict(user_input)

        # Always translate input to English for Watson
        try:
            translated_input = GoogleTranslator(source=detected_lang, target='en').translate(user_input) \
                if detected_lang != 'en' else user_input
        except Exception:
            translated_input = user_input
            detected_lang = "en" if not detected_lang else detected_lang

        session['history'].append({'sender': 'user', 'text': user_input})

        try:
            # Watson Assistant
            session_data = assistant.create_session(assistant_id=ASSISTANT_ID).get_result()
            session_id = session_data['session_id']

            response = assistant.message(
                assistant_id=ASSISTANT_ID,
                session_id=session_id,
                environment_id=ENVIRONMENT_ID,
                input={'message_type': 'text', 'text': translated_input}
            ).get_result()

            # ---------------- Handle Watson reply ----------------
            generic_output = response.get('output', {}).get('generic', [])
            if generic_output:
                text_chunks = [g.get('text') for g in generic_output if g.get('response_type') == 'text' and g.get('text')]
                bot_text_en = "\n".join(text_chunks) if text_chunks else "I couldn't find an answer."
            else:
                bot_text_en = "No response from Watson Assistant."

            # Always translate Watson reply back into detected language
            try:
                watson_reply = GoogleTranslator(source='en', target=detected_lang).translate(bot_text_en) \
                                if detected_lang != 'en' else bot_text_en
            except Exception:
                watson_reply = bot_text_en

            session['history'].append({'sender': 'bot', 'text': watson_reply})

            # ---------------- Build Recommendations (English base) ----------------
            rec_lines = []
            lower_in = translated_input.lower()
            if 'fever' in lower_in:
                rec_lines.append("🌡 Stay hydrated, rest, and monitor your temperature.")
            if 'chest pain' in lower_in:
                rec_lines.append("❤️ Chest pain may be serious. Consult a physician immediately.")
            if 'cough' in lower_in:
                rec_lines.append("💨 Use warm fluids and a humidifier.")
            if 'headache' in lower_in:
                rec_lines.append("🧠 Rest in a dark room, avoid screens, drink water.")

            # Translate each recommendation line to detected_lang
            if rec_lines and detected_lang != "en":
                new_lines = []
                for line in rec_lines:
                    try:
                        new_lines.append(GoogleTranslator(source='en', target=detected_lang).translate(line))
                    except Exception:
                        new_lines.append(line)
                rec_lines = new_lines

            # ---------------- Build Resources (translate titles only) ----------------
            google_results = google_search(translated_input)
            res_lines = []
            if google_results:
                for res in google_results:
                    if " - " in res:
                        title, link = res.split(" - ", 1)
                    else:
                        title, link = res, ""
                    if detected_lang != "en":
                        try:
                            title = GoogleTranslator(source='en', target=detected_lang).translate(title)
                        except Exception:
                            pass
                    res_lines.append(f"{title} - {link}")

            # ---------------- Format Final Block with localized headers ----------------
            final_block = ""
            if rec_lines:
                final_block += HEADERS_REC.get(detected_lang, "✅ Recommendations:\n")
                for line in rec_lines:
                    final_block += f"{line}\n"
                final_block += "\n"

            if res_lines:
                final_block += HEADERS_RES.get(detected_lang, "🔗 Resources:\n")
                for line in res_lines:
                    final_block += f"- {line}\n"

            recommendation_block = final_block.strip()

        except Exception as e:
            fallback_en = f"Error: {str(e)}"
            try:
                watson_reply = GoogleTranslator(source='en', target=detected_lang).translate(fallback_en) \
                                if detected_lang != 'en' else fallback_en
            except Exception:
                watson_reply = fallback_en
            session['history'].append({'sender': 'bot', 'text': watson_reply})

    return render_template('index.html',
                           history=session['history'],
                           recommendation=recommendation_block,
                           watson_reply=watson_reply)

# ---------------- Run App ----------------
if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
