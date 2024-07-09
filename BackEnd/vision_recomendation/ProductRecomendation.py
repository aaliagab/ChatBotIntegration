import torch
import torch.nn as nn
from torchvision import models, transforms
from torchvision.models import ResNet50_Weights
from PIL import Image, ImageTk
import numpy as np
import os
import cv2
import tkinter as tk
from tkinter import Label

# Load the ResNet model with weights
weights = ResNet50_Weights.DEFAULT
model = models.resnet50(weights=weights)
model.eval()
model = nn.Sequential(*list(model.children())[:-1])

# Transformations for preprocessing the images
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=weights.transforms().mean, std=weights.transforms().std),
])

# Function to extract features from an image
def extract_features(image_path):
    image = Image.open(image_path).convert('RGB')
    image = preprocess(image)
    image = image.unsqueeze(0)
    
    with torch.no_grad():
        features = model(image)
    return features.squeeze().numpy()

# Function to find the most similar image in the folder
def find_most_similar(captured_features, folder_path):
    min_distance = float('inf')
    most_similar_image = None
    
    for filename in os.listdir(folder_path):
        if filename.endswith(('.jpg', '.png', '.jpeg')):
            image_path = os.path.join(folder_path, filename)
            image_features = extract_features(image_path)
            distance = np.linalg.norm(captured_features - image_features)
            
            if distance < min_distance:
                min_distance = distance
                most_similar_image = image_path
                
    return most_similar_image

# Function to capture image from the webcam
def capture_image_from_webcam(image_path: str):
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return False

    def show_frame():
        ret, frame = cap.read()
        if ret:
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            label.imgtk = imgtk
            label.configure(image=imgtk)
            label.after(10, show_frame)
    
    root = tk.Tk()
    label = Label(root)
    label.pack()
    show_frame()
    
    root.after(5000, lambda: root.destroy())
    root.mainloop()
    
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(image_path, frame)
        print(f"Image saved to {image_path}")
        cap.release()
        return True
    else:
        print("Error: Could not capture image")
        cap.release()
        return False

# Function to show the recommended image
def show_image(image_path):
    if image_path is None:
        print("No se encontró ninguna imagen similar.")
        return
    
    img = Image.open(image_path)
    img.show()
