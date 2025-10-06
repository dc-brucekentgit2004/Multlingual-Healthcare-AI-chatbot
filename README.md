AI-Powered Multilingual Healthcare Assistant
An Intelligent, Conversational Healthcare System using IBM Watson, Google Cloud, Rasa, and Flask
🚀 Overview

The AI-Powered Multilingual Healthcare Assistant is an advanced AI-driven chatbot designed to provide symptom analysis, hospital recommendations, and multilingual support.
Built using IBM Watson Assistant, Watson NLU, Rasa NLU, Google Cloud Translation API, and Flask, it offers real-time, intelligent healthcare guidance with natural, human-like interaction.

This project bridges the gap between AI and accessible healthcare, enabling users to communicate in their preferred language and receive instant, context-aware medical suggestions — along with nearby hospital information.

⚙️ Tech Stack

Frontend: HTML, CSS, JavaScript (Chat-style interface with dynamic message rendering)

Backend: Flask (Python)

AI Services: IBM Watson Assistant V2, IBM Watson NLU, Rasa NLU

Translation: Google Cloud Translation API

APIs: Google Places / OpenStreetMap for Hospital Finder

Database (optional): SQLite / MongoDB for chat logs

Deployment: IBM Cloud / Render / Heroku

🧩 Key Features
🗣️ 1. Conversational AI (Watson + Rasa Integration)

Watson Assistant manages multi-turn dialogues and intent classification.

Rasa NLU handles custom intent recognition (e.g., “find nearest hospital in Lucknow”).

Hybrid design — if Watson doesn’t detect an intent, it’s routed through Rasa’s fallback intent recognition for improved accuracy.

🌐 2. Multilingual Support (Google Cloud Translation API)

Detects the language of user input automatically using langdetect.

Translates non-English queries (like Hindi) → English before sending to Watson / Rasa.

Translates AI responses back to the user’s native language.

Fully supports English ↔ Hindi and easily extendable to other languages.

🏥 3. Nearby Hospital Finder API

Extracts location entities from user input via Rasa / Watson NLU.

Fetches real-time hospital data using Google Places API or OpenStreetMap.

Displays:

Hospital Name

Address

Rating / Contact

Direct Google Maps link

Example:

“Nearest hospital in Hazratganj Lucknow”
→ Returns top 5 hospitals with location pins and details.

🔍 4. Dynamic Search & Knowledge Enhancement

If symptom information is missing, Flask dynamically performs a Google Search API query to fetch validated health information.

The results are summarized and contextually merged with Watson’s output.

💬 5. Intelligent Conversation Memory

Stores previous interactions (using Flask sessions).

Remembers user context across turns for a continuous dialogue (e.g., remembers “my fever started yesterday”).

💻 6. Flask Backend Integration

Flask handles all communication between:

Frontend UI

Watson Assistant

Rasa NLU

Google APIs

Uses requests module to call external APIs asynchronously for faster responses.

Session-based conversation handling ensures personalized flow for each user.

🧠 7. Emotion & Keyword Analysis (Watson NLU)

Analyzes user input for:

Keywords

Emotion

Sentiment

Enables adaptive tone in responses — e.g., detecting anxiety or urgency in user input.

🖥️ 8. Modern Chat UI

Built using HTML, CSS, and JS with real-time message rendering.

Features:

Typing animation

Scrollable chat window

Voice input (optional via SpeechRecognition)

PDF chat export

🧪 Example Workflow

User: “मुझे बुखार और सीने में दर्द है”

System: Detects Hindi → translates to English (“I have fever and chest pain”)

Watson Assistant → Analyzes symptoms

Watson NLU → Extracts “fever” and “chest pain” as key symptoms

Flask merges insights + recommends nearby hospitals

Response (translated back to Hindi):
“यह गंभीर हो सकता है। कृपया निकटतम अस्पताल जाएँ।
🏥 Apollo Hospital, Hazratganj – 1.2 km away”
