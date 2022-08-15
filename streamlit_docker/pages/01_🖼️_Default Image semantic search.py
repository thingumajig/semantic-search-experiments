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
st.set_page_config(layout="wide", initial_sidebar_state='collapsed')
candidates = 100
num_cols = 3

def get_images_from_response(json, column_name, k):
    records = json["hits"]["hits"]

    for i in range(0, min([len(records), int(k)])):
        yield records[i]["_source"][column_name], records[i]["_score"], records[i]["_source"][column_name+"_data"]


st.title("Семантический поиск изображений")
st.caption("Поиск изображений по текстовым описаниям")
index = 'news-headers'   ## st.text_input("Введите индекс:", value="news-headers")
column_name = 'image' ## st.text_input("Введите column_name:")
title = st.text_input("Введите текст запроса:")
num_results = json.load(open("./settings.json", "r"))["search_k"]
if title:
    with st.spinner('Поиск....'):
        result = requests.post(f"http://172.21.0.4:80/semantic_search/", data={"index":index, "column_name":column_name, "query": title, "num_results": str(candidates), "data_columns": "image_data", "img_flag": "true"}).json()
        st.write(f"Было найдено {result['hits']['total']['value']} совпадений. Показаны топ-{num_results}")

        cc=0
        cols = st.columns(num_cols)
        delta=0.
        for name, score, img in get_images_from_response(result, column_name, num_results):
            col_ix = cc % num_cols
            with cols[col_ix]:
                st.markdown(f'<div style="font-size: 12px;">{cc+1}.<b>Оценка:</b> {score-1.:.2f} <b>Имя:</b>{name}</div>', unsafe_allow_html=True)
                st.image(Image.open(io.BytesIO(base64.b64decode(img[2:-1]))))

            cc+=1
    
