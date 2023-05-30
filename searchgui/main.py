#!/usr/bin/env python3
import work_pages
import home_page
import theme

from nicegui import ui

from elasticsearch import Elasticsearch
# import tensorflow_hub as hub
# import numpy as np
# import tensorflow_text
from tqdm import tqdm

es = Elasticsearch(["http://localhost:9200"], http_auth=('elastic', 'xxxxxx'), timeout=30)
es.cluster.health(wait_for_status='yellow', request_timeout=10)

# model_name = "https://tfhub.dev/google/universal-sentence-encoder-multilingual/3"
# model_name = 'https://tfhub.dev/google/universal-sentence-encoder-multilingual-large/3'
# embedder = hub.load(model_name)


from transformers import AutoTokenizer, AutoModel
import torch

# model_name = 'symanto/sn-xlm-roberta-base-snli-mnli-anli-xnli'
model_name = 'inkoziev/sbert_pq'

#Mean Pooling - Take attention mask into account for correct averaging
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


# Load model from HuggingFace Hub
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

def get_sentence_embeddings(sentences):
    # Tokenize sentences
    encoded_input = tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')

    # Compute token embeddings
    with torch.no_grad():
        model_output = model(**encoded_input)

    # Perform pooling. In this case, mean pooling.
    return mean_pooling(model_output, encoded_input['attention_mask'])

# here we use our custom page decorator directly and just put the content creation into a separate function
@ui.page('/')
def index_page() -> None:
    with theme.frame(''):
        home_page.content(es, get_sentence_embeddings)


# this call shows that you can also move the whole page creation into a separate file
work_pages.create()

ui.run(title='Поиск в документах')