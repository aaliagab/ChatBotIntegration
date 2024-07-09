from openai import OpenAI
import base64
import cv2
import os

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def capture_image_from_webcam(image_path: str):
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return False
    
    ret, frame = cap.read()
    
    if ret:
        cv2.imwrite(image_path, frame)
        print(f"Image saved to {image_path}")
        cap.release()
        cv2.destroyAllWindows()
        return True
    else:
        print("Error: Could not capture image")
        cap.release()
        cv2.destroyAllWindows()
        return False

def process_image_webcam(image_path: str):
    if capture_image_from_webcam(image_path):
        try:
            with open(image_path, 'rb') as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            response = client.chat.completions.create(
                model='gpt-4o',
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract text from this image."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]
                    }
                ],
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
    return "Error: Could not capture image"
