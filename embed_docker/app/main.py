from fastapi import FastAPI, Form, UploadFile, File
import sys
import json
import io
import numpy as np
from PIL import Image
sys.path.append('./app')
import ruclip
import tensorflow_hub as hub
import tensorflow_text

device = 'cpu'
clip, processor = ruclip.load('ruclip-vit-base-patch32-384', device=device)
predictor = ruclip.Predictor(clip, processor, device, bs=8, templates=['{}'])

embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder-multilingual/3")

app = FastAPI()

@app.get("/")
async def root():
    return "Ready!"

@app.post("/emb_text/")
async def emb_text(data: str = Form(default="")):
    return json.dumps(embed(data).numpy()[0].tolist())

@app.post("/emb_img_text/")
async def emb_img_text(data: str = Form(default="")):
    print(len(data), data)
    return json.dumps(predictor.get_text_latents([data]).detach().cpu().numpy()[0].tolist())

@app.post("/emb_img/")
async def emb_img(file: UploadFile = File(...)):
    contents = await file.read()
    print(len(contents))
    return json.dumps(predictor.get_image_latents([Image.open(io.BytesIO(contents))]).cpu().detach().numpy()[0].tolist())
