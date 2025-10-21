# 🧠 LangChain + Gemini Chatbot (Streamlit)

A polished Streamlit app that wraps LangChain with Google Gemini (via langchain-google-genai). It ships with themed UI, multiple chat modes, a fun Explore toolbox, simple multi-chat history, and lightweight local theme persistence.

# ✨ Features
Gemini-powered chat via LangChain pipeline
Modes: Default, Math Tutor, Doctor, Travel Guide, Grammar Fixer, Summarizer, Quiz Generator
Explore tools: Career Counselor, Cover Letter, Wellness Tip, Random Fact, Recipe
Multi-chat sessions with titles & downloadable responses
Sleek theming: Light / Dark Neon + “Reduce motion” option
Local theme persistence at ~/.appdata/ai-chat/theme.json
Responsive, custom CSS with a centered “composer” search box

# 🧱 Tech Stack
Python 3.10+
Streamlit for UI
LangChain core + output parsing
Google Gemini via langchain-google-genai
python-dotenv for environment config

# Install Dependencies
pip install -r requirements.txt

# Add your API key
Create a .env file in the repo root
File name: (.env)
YOUR_API_KEY = your_google_generative_ai_key_here

# Run the app:
streamlit run langchain_chatbot.py
