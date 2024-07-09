from openai import OpenAI
from transformers import pipeline
import os

# Configuración de la API de OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Cargar el modelo preentrenado para análisis de sentimientos una vez
sentiment_analysis = pipeline('sentiment-analysis', model="distilbert-base-uncased-finetuned-sst-2-english")

def analyze_sentiment(text):
    try:
        result = sentiment_analysis(text)
        return result[0]['label'], result[0]['score']
    except Exception as e:
        return "Error", str(e)

def get_custom_response(conversation_history):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation_history
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"
