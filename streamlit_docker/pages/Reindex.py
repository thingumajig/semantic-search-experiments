import requests
import streamlit as st
import pandas as pd


# https://discuss.streamlit.io/t/version-0-64-0-deprecation-warning-for-st-file-uploader-decoding/4465
st.set_option("deprecation.showfileUploaderEncoding", False)

st.title("Реиндексация записей без эмбеддингов")
index = st.text_input("Введите индекс:")
if st.button("Реиндексировать"):
    result = requests.post(f"http://172.21.0.4:80/reindex_existing_embs/", data={"index":index}).json()
    st.write(result)
    