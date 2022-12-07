import requests
import streamlit as st
import pandas as pd
import json

settings_file = "./settings.json"

def set_settings(new_num):
    with open(settings_file, "r") as f:
        data = json.load(f)
        data["search_k"] = int(new_num)
    with open(settings_file, "w") as f:
        json.dump(data, f)

def get_settings():
    with open(settings_file, "r") as f:
        data = json.load(f)
        return data["search_k"]

st.set_option("deprecation.showfileUploaderEncoding", False)
    
st.title("Настройки")
new_num = st.text_input("Количество результатов семантического поиска:", value=str(get_settings()))
if st.button("Изменить"):
    set_settings(new_num)
    st.write("Сохранено!")
    
if st.button("Индексировать данные"):
    result = requests.get("http://172.21.0.4:80/prepare_text_data/").json()
    st.write(result)
