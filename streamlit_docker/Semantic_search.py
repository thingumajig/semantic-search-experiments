import requests
import streamlit as st
import pandas as pd
import json
from pandas.io.json import json_normalize

# https://discuss.streamlit.io/t/version-0-64-0-deprecation-warning-for-st-file-uploader-decoding/4465
st.set_option("deprecation.showfileUploaderEncoding", False)
st.set_page_config(layout="wide")

@st.cache
def create_df_from_json(json, k):
    records = json["hits"]["hits"]
    df = pd.DataFrame()
    for i in range(0, int(k)):
        df = df.append(json_normalize(records[i]), ignore_index=True)
    df.drop(["_type"], axis=1, inplace=True)
    df.rename(lambda x: x[1:], axis=1, inplace=True)
    df.sort_values("score", inplace=True, ascending=False)
    return df

# defines an h1 header
st.title("Семантический поиск")
title = st.text_input("Введите текст запроса:")
num_recs = json.load(open("./settings.json", "r"))["search_k"]
if st.button("Поиск"):
    result = requests.post(f"http://172.21.0.4:80/get_closest/", data={"query":title, "num_results":num_recs}).json()
    st.write(f"Было найдено {result['hits']['total']['value']} совпадений. Показаны топ-{num_recs}")
    st.dataframe(create_df_from_json(result, num_recs), width=1000)