from flask import Flask, request, jsonify, render_template, send_from_directory
from chat_with_sentiment.SentimentAnalysis import analyze_sentiment, get_custom_response
from image_text_extraction.process_image_webcam import process_image_webcam
from image_text_extraction.process_image_upload import process_image_upload
from image_text_extraction.process_image_url import process_image_url
from vision_recomendation.ProductRecomendation import capture_image_from_webcam, find_most_similar, extract_features
import os
from PIL import Image
from io import BytesIO
import requests


app = Flask(__name__, static_folder='templates/static', template_folder='templates')

@app.route('/vision_recomendation/productos/<path:filename>')
def custom_static(filename):
    return send_from_directory('vision_recomendation/productos', filename)

def find_products_based_on_text(text_content, folder_path):
    # Supongamos que tenemos una lista de productos con sus nombres de archivo
    product_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

    # Filtrar los productos cuyos nombres de archivo coincidan con el texto extraído
    matching_products = [os.path.join(folder_path, f) for f in product_files if any(word in f for word in text_content.split())]

    return matching_products

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.form.get('message')
        image = request.files.get('image')

        if user_message and image:
            image_path = os.path.join('templates/static', 'uploaded_image.png')
            image.save(image_path)
            text_content = process_image_upload(image_path)

            # Aquí puedes unir el texto del mensaje y el texto extraído de la imagen
            combined_message = f"{user_message} {text_content}"
            sentiment, score = analyze_sentiment(combined_message)
            conversation_history = [
                {"role": "system", "content": "You are a helpful assistant for an online store. You must simulate that you have a wide variety of products and during the conversation with users feel free to generate links to products within the store based on the domain allshop.com"},
                {"role": "user", "content": combined_message}
            ]
            custom_response = get_custom_response(conversation_history)

            # Obtener la recomendación del producto
            captured_features = extract_features(image_path)
            folder_path = 'vision_recomendation/productos'
            most_similar_image = find_most_similar(captured_features, folder_path)

            # Devolver la respuesta, la URL de la imagen del usuario y la URL de la imagen recomendada
            return jsonify({
                'response': custom_response,
                'user_image_url': f'/static/uploaded_image.png',
                'recommended_image_url': f'/{folder_path}/{os.path.basename(most_similar_image)}'
            })

        if user_message:
            sentiment, score = analyze_sentiment(user_message)
            conversation_history = [
                {"role": "system", "content": "You are a helpful assistant for an online store. You must simulate that you have a wide variety of products and during the conversation with users feel free to generate links to products within the store based on the domain allshop.com"},
                {"role": "user", "content": user_message}
            ]
            custom_response = get_custom_response(conversation_history)
            return jsonify({'response': custom_response})

        if image:
            image_path = os.path.join('templates/static', 'uploaded_image.png')
            image.save(image_path)

            # Intentar identificar productos en la imagen
            captured_features = extract_features(image_path)
            folder_path = 'vision_recomendation/productos'
            most_similar_image = find_most_similar(captured_features, folder_path)

            if most_similar_image:
                return jsonify({
                    'response': "Hemos encontrado un producto que puede interesarte.",
                    'user_image_url': f'/static/uploaded_image.png',
                    'recommended_image_url': f'/{folder_path}/{os.path.basename(most_similar_image)}'
                })

            # Si no se encuentran productos, proceder a extraer texto y recomendar productos basados en el texto
            text_content = process_image_upload(image_path)
            # Aquí puedes realizar el análisis de texto y buscar productos basados en el texto extraído
            product_images = find_products_based_on_text(text_content, folder_path)

            if product_images:
                # Aquí se supone que `product_images` es una lista de imágenes que coinciden con el texto
                # Seleccionamos la más similar basada en las características
                most_similar_image = find_most_similar(captured_features, product_images)

                return jsonify({
                    'response': text_content,
                    'user_image_url': f'/static/uploaded_image.png',
                    'recommended_image_url': f'/{folder_path}/{os.path.basename(most_similar_image)}'
                })

            return jsonify({'response': "No se encontró ningún producto ni texto relevante en la imagen."})

        return jsonify({'response': "No message or image provided."})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/capture', methods=['GET'])
def capture():
    try:
        image_path = 'templates/static/captured_image.jpg'
        if capture_image_from_webcam(image_path):
            captured_features = extract_features(image_path)
            folder_path = 'vision_recomendation/productos'
            most_similar_image = find_most_similar(captured_features, folder_path)

            if most_similar_image:
                recommended_product = {
                    "image": most_similar_image,
                    "text": "Basado en tu imagen, recomendamos este producto."
                }
                return jsonify({'response': f'Imagen más similar: {most_similar_image}', 'recommended_product': recommended_product})
            else:
                return jsonify({'response': "No se encontró ninguna imagen similar."})
        else:
            return jsonify({'response': "No se capturó ninguna imagen."})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process_url', methods=['POST'])
def process_url():
    try:
        data = request.get_json()
        image_url = data.get('image_url')
        message_text = data.get('message', '')

        if image_url:
            print(f"Processing URL: {image_url}")
            # Descargar y guardar la imagen
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            image = image.convert("RGB")  # Convertir a RGB si es necesario

            image_path = 'templates/static/uploaded_image_from_url.png'
            image.save(image_path, format="PNG")
            
            print(f"Image saved to {image_path}")

            # Procesar la imagen descargada
            text_content = process_image_upload(image_path)
            print(f"Text content extracted: {text_content}")

            captured_features = extract_features(image_path)
            folder_path = 'vision_recomendation/productos'
            most_similar_image = find_most_similar(captured_features, folder_path)
            if most_similar_image:
                recommended_product = {
                    "image": most_similar_image,
                    "text": "Basado en tu imagen, recomendamos este producto."
                }
                print(f"Recommended product: {recommended_product}")
            
            # Combina el texto extraído y el mensaje del usuario
            combined_message = f"{message_text} {text_content}"
            sentiment, score = analyze_sentiment(combined_message)
            conversation_history = [
                {"role": "system", "content": "You are a helpful assistant for an online store. You must simulate that you have a wide variety of products and during the conversation with users feel free to generate links to products within the store based on the domain allshop.com"},
                {"role": "user", "content": combined_message}
            ]
            custom_response = get_custom_response(conversation_history)
            
            return jsonify({'response': custom_response, 'recommended_image_url': f'/{folder_path}/{os.path.basename(most_similar_image)}'})

        return jsonify({'response': "No image URL provided."})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
