import requests
import streamlit as st
import pandas as pd
import io
from PIL import Image
import json
import base64
from pandas.io.json import json_normalize

# https://discuss.streamlit.io/t/version-0-64-0-deprecation-warning-for-st-file-uploader-decoding/4465
st.set_option("deprecation.showfileUploaderEncoding", False)
st.set_page_config(layout="wide")
candidates = 100

def get_images_from_response(json, column_name, k):
    records = json["hits"]["hits"]

    for i in range(0, min([len(records), int(k)])):
        yield records[i]["_source"][column_name], records[i]["_score"], records[i]["_source"][column_name+"_data"]


st.title("Поиск по embeddings среди изображений")
index = st.text_input("Введите индекс:", value="news-headers")
column_name = st.text_input("Введите column_name:")
title = st.text_input("Введите текст запроса:")
num_results = json.load(open("./settings.json", "r"))["search_k"]
if st.button("Поиск"):
    result = requests.post(f"http://172.21.0.4:80/semantic_search/", data={"index":index, "column_name":column_name, "query": title, "num_results": str(candidates), "data_columns": "image_data", "img_flag": "true"}).json()
    st.write(f"Было найдено {result['hits']['total']['value']} совпадений. Показаны топ-{num_results}")
    for name, score, img in get_images_from_response(result, column_name, num_results):
        st.image(Image.open(io.BytesIO(base64.b64decode(img[2:-1]))), caption=f"{score} - {name}")

    
