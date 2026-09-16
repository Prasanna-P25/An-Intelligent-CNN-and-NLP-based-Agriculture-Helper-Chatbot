from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt

import os
import cv2
import numpy as np
from numpy import dot
from numpy.linalg import norm
from sklearn.feature_extraction.text import TfidfVectorizer
import speech_recognition as sr
import pandas as pd
from keras.models import model_from_json


# ---------------- PLANT CLASSES ----------------
plants = [
    'Apple___Apple_scab','Apple___Black_rot','Apple___Cedar_apple_rust','Apple___healthy',
    'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot','Corn_(maize)___Common_rust_',
    'Corn_(maize)___healthy','Corn_(maize)___Northern_Leaf_Blight','Grape___Black_rot',
    'Grape___Esca_(Black_Measles)','Grape___healthy',
    'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)','Potato___Early_blight',
    'Potato___healthy','Potato___Late_blight','Tomato___Bacterial_spot',
    'Tomato___Early_blight','Tomato___healthy','Tomato___Late_blight',
    'Tomato___Leaf_Mold','Tomato___Septoria_leaf_spot',
    'Tomato___Spider_mites Two-spotted_spider_mite','Tomato___Target_Spot',
    'Tomato___Tomato_mosaic_virus','Tomato___Tomato_Yellow_Leaf_Curl_Virus'
]

recognizer = sr.Recognizer()

question = []
answer = []
counter = 0



dataset = pd.read_csv("Messages/diseases.txt", encoding='iso-8859-1', header=None).values
for i in range(len(dataset)):
    question.append(dataset[i, 0].strip().lower())
    answer.append(dataset[i, 1])



dataset = pd.read_csv("Messages/agriculture_chatbot_200_crops_real_seeds.csv")

for i in range(len(dataset)):
    crop = str(dataset.iloc[i, 0]).strip().lower()
    question.append(crop)

    row_data = dataset.iloc[i, 1:]
    details = []

    for col_name, value in row_data.items():
        if pd.notna(value):
            details.append(f"{col_name}: {value}")

    answer.append("\n".join(details))

tfidf_vectorizer = TfidfVectorizer()
tfidf = tfidf_vectorizer.fit_transform(question).toarray()


def index(request):
    return render(request, 'index.html')

def Upload(request):
    return render(request, 'Upload.html')

def Record(request):
    return render(request, 'Record.html')



def getChat(query):
    query = query.lower().strip()

    
    if "___" in query:
        for i in range(len(question)):
            if question[i] == query:
                return answer[i]
        return "No remedy found"

    
    matched = []
    for i in range(len(question)):
        if question[i] in query:
            matched.append(answer[i])

    if len(matched) > 0:
        return "\n\n------------------\n\n".join(matched)

    
    test = tfidf_vectorizer.transform([query]).toarray()[0]

    similarity = 0
    result = "I am not trained to answer given question"

    for i in range(len(tfidf)):
        if norm(tfidf[i]) != 0 and norm(test) != 0:
            score = dot(tfidf[i], test) / (norm(tfidf[i]) * norm(test))

            if score > similarity:
                similarity = score
                result = answer[i]

    return result



def ChatData(request):
    global counter

    query = request.GET.get('mytext', '').strip()
    output = getChat(query)

    if output == "I am not trained to answer given question":
        counter += 1

    if counter >= 3:
        output = "Please ask related questions"
        counter = 0

    return HttpResponse(output, content_type="text/plain")



@csrf_exempt
def record(request):
    if request.method == "POST":
        try:
            audio_data = request.FILES.get('data')
            fs = FileSystemStorage()

            webm_path = 'ChatBotApp/static/record.webm'
            wav_path = 'ChatBotApp/static/record.wav'

            if os.path.exists(webm_path):
                os.remove(webm_path)

            if os.path.exists(wav_path):
                os.remove(wav_path)

            fs.save(webm_path, audio_data)

            
            os.system(f'ffmpeg -i {webm_path} {wav_path}')

            with sr.AudioFile(wav_path) as source:
                audio = recognizer.record(source)

            try:
                text = recognizer.recognize_google(audio)
            except:
                text = "I am not trained to answer given question"

            output = getChat(text)

            return HttpResponse("You: " + text + "\nChatbot: " + output)

        except Exception as e:
            return HttpResponse("Error: " + str(e))

def UploadAction(request):
    if request.method == 'POST':
        myfile = request.FILES['t1']
        fs = FileSystemStorage()

        path = 'ChatBotApp/static/plant/test.png'

        if os.path.exists(path):
            os.remove(path)

        fs.save(path, myfile)

        with open('model/model.json', "r") as json_file:
            classifier = model_from_json(json_file.read())

        classifier.load_weights("model/model_weights.h5")

        img = cv2.imread(path)
        img = cv2.resize(img, (64, 64))

        test = np.asarray(img).reshape(1, 64, 64, 3).astype('float32') / 255

        preds = classifier.predict(test)
        predict = np.argmax(preds)

        disease_name = plants[predict]

        
        chat_msg = getChat(disease_name)

        result = (
            "Crop Disease Predicted as: " + disease_name +
            "\n\nPossible Remedy:\n" + chat_msg
        )

        return render(request, 'Chat.html', {'data': result})