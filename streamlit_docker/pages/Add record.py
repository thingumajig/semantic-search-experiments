import requests
import streamlit as st
import pandas as pd


st.set_option("deprecation.showfileUploaderEncoding", False)

st.title("Добавление записи")
index = st.text_input("Введите индекс:", value="tk")
column_name = st.text_input("Введите название колонки:", value="text")
data = st.text_input("Введите строку:")
if st.button("Добавить"):
    result = requests.post(f"http://172.21.0.4:80/add_record/", data={"index":index, "column_name":column_name, "data":data}).json()
    try:
        if result["_shards"]["failed"]==0:
            st.write(f"Была создана запись c id: {result['_id']}")
    except:
        st.write("Произошла ошибка: ", result)
