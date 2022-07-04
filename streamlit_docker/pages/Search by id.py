import requests
import streamlit as st
import pandas as pd


# https://discuss.streamlit.io/t/version-0-64-0-deprecation-warning-for-st-file-uploader-decoding/4465
st.set_option("deprecation.showfileUploaderEncoding", False)

st.title("Поиск по индексу и id")
index = st.text_input("Введите индекс:", value="news-headers")
id = st.text_input("Введите id:")
if st.button("Поиск"):
    result = requests.post(f"http://172.21.0.4:80/get_by_id/", data={"index":index, "id":id}).json()
    st.write(result)
    
