import torch
from transformers import BertForSequenceClassification, AutoTokenizer

path = 'Djacon/rubert-tiny2-russian-emotion-detection'
model = BertForSequenceClassification.from_pretrained(path)
tokenizer = AutoTokenizer.from_pretrained(path)

LABELS = ['радость', 'интерес', 'удивление', 'печаль', 'гнев', 'отвращение',
          'страх', 'вина', 'нейтрально']


# Predicting emotion in text
@torch.no_grad()
def predict_emotion(text):
    inputs = tokenizer(text, max_length=512, truncation=True,
                       return_tensors='pt')
    inputs = inputs.to(model.device)

    outputs = model(**inputs)

    pred = torch.nn.functional.softmax(outputs.logits, dim=1)
    pred = pred.argmax(dim=1)

    return LABELS[pred[0]]


# Probabilistic prediction of emotion in a text
@torch.no_grad()
def predict_emotions(text):
    inputs = tokenizer(text, max_length=512, truncation=True,
                       return_tensors='pt')
    inputs = inputs.to(model.device)

    outputs = model(**inputs)

    pred = torch.nn.functional.softmax(outputs.logits, dim=1)

    emotions_list = {}
    for i in range(len(pred[0].tolist())):
        emotions_list[LABELS[i]] = pred[0].tolist()[i]
    return emotions_list
