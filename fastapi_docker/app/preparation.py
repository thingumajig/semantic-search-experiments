import numpy as np
import pandas as pd
import os
import time
import zipfile
import requests
import io
import base64
from pathlib import Path
from PIL import Image
from time import sleep

from tqdm import tqdm
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import elasticsearch as eees

        
def embed_text(text):
    while True:
        try:
            str_vec = requests.post(f"http://172.21.0.6:89/emb_text/", data={"data":text}).json()
            break
        except:
            sleep(0.01)
            print("Failed to receive response")
            
    return np.array([float(x) for x in str_vec.strip("][").split(", ")])

def embed_text_img(text):
    while True:
        try:
            str_vec = requests.post(f"http://172.21.0.6:89/emb_img_text/", data={"data":text}).json()
            break
        except:
            sleep(0.01)
            print("Failed to receive response")
            
    return np.array([float(x) for x in str_vec.strip("][").split(", ")])

def embed_pil_img(img):
    
    while True:
        try:
            
            str_vec = requests.post(f"http://172.21.0.6:89/emb_img/", files={'file': ('image.png', img, 'image/png')}).json()
            break
        except:
            sleep(0.01)
            print("Failed to receive response")
            
            
    return np.array([float(x) for x in str_vec.strip("][").split(", ")])

def heads_actions(df):
    for index, row in df.iterrows():
        # print(row['ID'], row['NEWS_HEAD'])
        # print(embed(row['NEWS_HEAD']).numpy()[0])
        yield {
          "_op_type": "index",
          "_index": index_name,

          "_id": row['ID'],
          "db_id": row['ID'],
          "title": row['NEWS_HEAD']

        }
        

def vector_actions(df):
    for index, row in df.iterrows():
        yield {
            "_op_type": "update",
            "_index": index_name,

            "_id": row['ID'],
            "doc": {
              "title_emb": { "values": embed_text(row['NEWS_HEAD']) }
            }
        }


def get_closest(query, num_results):
    body = {
          "query": {
            "multi_match": {
              "query": query,
              "fields": ["title^2"]
            }
          }
        }

    res = es.search(index=index_name, body=body, size=int(num_results), _source=source_no_vecs)
    return res

def get_by_id(index, id):
    res = es.get(index=index, id=id)
    return res

def add_image(index, column_name, img_path):
    
    img = Image.open(img_path)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    embed_vector = embed_pil_img(img_byte_arr)
    img_byte_arr.seek(0)
    
    mapping_fields = list(es.indices.get_mapping(index=index)[index]["mappings"]["properties"].keys())
    if column_name not in mapping_fields:
        body = {
                "properties": {
                    column_name: {"type": "text" },
                    column_name+"_data": {"type": "binary" },
                    column_name+"_emb": {
                        "type": "elastiknn_dense_float_vector", # 1
                        "elastiknn": {
                            "dims": vector_dims,                        # 2
                            "model": "lsh",                     # 3
                            "similarity": "cosine",             # 4
                            "L": 99,                            # 5
                            "k": 3                              # 6
                            }
                        }
                    }
                }
        es.indices.put_mapping(body=body, index=index)
        
    res = es.index(index=index, id=None, document={column_name: img_path.name, 
                                                   column_name+"_data": str(base64.b64encode(img_byte_arr.read())), 
                                                   column_name+"_emb": embed_vector}, refresh="wait_for")
    
    return res

def news_addition():
    tqdm.pandas(desc="pandas processing...")
    df = pd.read_excel("ЭТ_Новости.xlsx")

    bulk(es, heads_actions(df), chunk_size=1000, max_retries=2)

    es.indices.refresh(index=index_name)
    es.indices.forcemerge(index=index_name, max_num_segments=1, request_timeout=120)

    bulk(es, vector_actions(df), chunk_size=50, max_retries=10, request_timeout=60)

    es.indices.refresh(index=index_name)
    es.indices.forcemerge(index=index_name, max_num_segments=1, request_timeout=300)

def image_addition():
    with zipfile.ZipFile("search_imgs.zip", 'r') as zip_ref:
        zip_ref.extractall("imgs_for_search")
        
    imgs_list = list(Path("./imgs_for_search/").rglob("*.jpg"))
    i = 0
    
    for img_path in imgs_list:
        add_image(index_name, "image", img_path)
        i+=1
        
    return i
        
def add_record(index, column_name, data):
    mapping_fields = list(es.indices.get_mapping(index=index)[index]["mappings"]["properties"].keys())
    if column_name not in mapping_fields:
        body = {
                "properties": {
                    column_name: {"type": "text" },
                    }
                }
        es.indices.put_mapping(body=body, index=index)
    res = es.index(index=index, id=None, document={column_name: data},refresh="wait_for")
    
    return res

def add_embs(index, id, column_name):
    data = get_by_id(index, id)["_source"][column_name]
    _create_mapping_for_emb(index, column_name)
        
    doc = { 
              column_name+"_emb": { "values": embed_text(data) }
          }
        
    res = es.update(index=index, id=id, body={"doc":doc})
    return res

def reindex(index, new_index):
    res = es.reindex({
    "source": {
        "index": index,
    },
    "dest": {
        "index": new_index
    }})
    return res

def count_index(index):
    return es.cat.count(index, params={"format": "json"})[0]

def search_and_recalc_embs(index, column_name, empty_only=False):
    changed = 0
    def recalc_generator(index, data, column_name, empty_only):
        nonlocal changed
        for hit in data["hits"]["hits"]:
            if not empty_only or (empty_only and column_name+"_emb" not in hit["_source"].keys()):
                yield {
                    "_op_type": "update",
                    "_index": index,

                    "_id": hit["_id"],
                    "doc": {
                      column_name+"_emb": { "values": embed_text(hit["_source"][column_name]) }
                    }
                }
                changed +=1  
                
    data = es.search(
        index=index,
        query={
                "exists": {
                    "field": column_name
                    },
                },
        scroll='5m',
        size=1000,
        )

    # Get the scroll ID
    sid = data['_scroll_id']
    scroll_size = len(data['hits']['hits'])
    
    while scroll_size > 0:
        # Scrolling...
        # Before scroll, process current batch of hits
        bulk(es, recalc_generator(index, data, column_name, empty_only), chunk_size=50, max_retries=10, request_timeout=60)

        data = es.scroll(scroll_id=sid, scroll='5m')

        # Update the scroll ID
        sid = data['_scroll_id']

        # Get the number of results that returned in the last scroll
        scroll_size = len(data['hits']['hits'])

    es.clear_scroll(scroll_id=sid)
    return changed

def _create_mapping_for_emb(index, column_name):
    mapping_fields = list(es.indices.get_mapping(index=index)[index]["mappings"]["properties"].keys())
    if column_name+"_emb" not in mapping_fields:
        body = { 
                "properties": {
                    column_name+"_emb": {
                        "type": "elastiknn_dense_float_vector", # 1
                        "elastiknn": {
                            "dims": vector_dims,                        # 2
                            "model": "lsh",                     # 3
                            "similarity": "cosine",             # 4
                            "L": 99,                            # 5
                            "k": 3                              # 6
                            }
                        }
                    }
               }
        es.indices.put_mapping(body=body, index=index)
        

es = Elasticsearch(["http://172.21.0.3:9200"], http_auth=('elastic', 'xxxxxx'), timeout=30)

while True:
    try:
        st = requests.get(f"http://172.21.0.6:89/").status_code
        if st==200:
            break
    except:
        print("Error connecting to embedding server, retrying..", flush=True)
        time.sleep(5)
        
while True:
    try:
        es.cluster.health(wait_for_status='yellow', request_timeout=10)
        break
    except:
        print("Error connecting to elasticsearch, retrying..", flush=True)
        time.sleep(5)
        
index_name = 'news-headers'

source_no_vecs = ['title', 'db_id']
vector_dims = 512

settings = {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "elastiknn": True,
}

mapping = {
  "dynamic": False,
  "properties": {
    "db_id": { "type": "text" },
    "title": {"type": "text" },  
      
      
    "title_emb": {
        "type": "elastiknn_dense_float_vector", # 1
        "elastiknn": {
            "dims": vector_dims,                        # 2
            "model": "lsh",                     # 3
            "similarity": "cosine",             # 4
            "L": 99,                            # 5
            "k": 3                              # 6
        }
    },
    
  }
}

if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name, settings=settings)
    es.indices.put_mapping(body=mapping, index=index_name,  )


es.cluster.put_settings({
    "persistent": { "cluster.max_shards_per_node": "5000" },
    "transient": {
        "cluster.routing.allocation.total_shards_per_node": 5100
    }
})

es.indices.refresh(index=index_name)

def create_mapping_and_reindex(index, text_column_name, empty_only):
    # 1. Add mapping for text_column_name with _emb postfix
    new_mapping = _create_mapping_for_emb(index, text_column_name)
    # 2. Recalculate embeddings for each row in index
    changed = search_and_recalc_embs(index, text_column_name, empty_only=empty_only)
    # 3. Refresh index
    es.indices.refresh(index=index)
    es.indices.forcemerge(index=index, max_num_segments=1, request_timeout=300)
    return changed

def reindex_existing_embs(index):
    # 0. get column name set with "*_emb"
    mapping_fields = list(es.indices.get_mapping(index=index)[index]["mappings"]["properties"].keys())
    emb_fields = [x[:-4] for x in mapping_fields if x.endswith("_emb")]
    changed = 0
    for emb_field in emb_fields:
        ch = create_mapping_and_reindex(index, emb_field, empty_only=True)
        changed += ch
    # 1. get rows without *_emb==Empty
    # 2. for each row with *_emb==Empty
    #       recalculate embeddings for new rows
    # 3. reindex elastic
    return changed

def semantic_search(index, column_name, search_text, num_results, data_columns="", img_flag=False):
    if img_flag.lower()=="true":
        search_text_emb = embed_text_img(search_text)
    else:
        search_text_emb = embed_text(search_text)
        
    body = {
    "query": {
        "elastiknn_nearest_neighbors": {
            "field": column_name+"_emb",                     # 1
            "vec": {                               # 2
                "values": search_text_emb
            },
            "model": "lsh",                        # 3
            "similarity": "cosine",                # 4
            "candidates": int(num_results)         # 5
            }
        }
    }
    res = es.search(index=index, body=body, size=int(num_results), _source=[column_name, *(data_columns.split(",") if data_columns else [])])
    return res


# Image embedding part

# 

# image_addition()