import tensorflow_hub as hub
import numpy as np
import tensorflow_text
import pandas as pd
import os
import time

from tqdm import tqdm
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import elasticsearch as eees


def heads_actions():
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
        

def vector_actions():
    for index, row in df.iterrows():
        yield {
            "_op_type": "update",
            "_index": index_name,

            "_id": row['ID'],
            "doc": {
              "title_emb": { "values": embed(row['NEWS_HEAD']).numpy()[0] }
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

def add_record(index, column_name, data):
    #id = None if "id" not in record else record["id"] 
    res = es.index(index=index, id=None, document={column_name: data})
    return res

def add_embs(index, id, column_name):
    data = get_by_id(index, id)["_source"][column_name]
    doc = { 
              column_name+"_emb": { "values": embed(data).numpy()[0] }
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
    return es.cat.count(index_name, params={"format": "json"})[0]
    

es = Elasticsearch(["http://172.21.0.3:9200"], http_auth=('elastic', 'xxxxxx'), timeout=30)

while True:
    try:
        es.cluster.health(wait_for_status='yellow', request_timeout=10)
        break
    except:
        print("Error connecting, retrying..", flush=True)
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
    es.indices.put_mapping(mapping=mapping, index=index_name,  )


es.cluster.put_settings({
    "persistent": { "cluster.max_shards_per_node": "5000" },
    "transient": {
        "cluster.routing.allocation.total_shards_per_node": 5100
    }
})

es.indices.refresh(index=index_name)

embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder-multilingual/3")

tqdm.pandas(desc="pandas processing...")
df = pd.read_excel("ЭТ_Новости.xlsx")

bulk(es, heads_actions(), chunk_size=1000, max_retries=2)

es.indices.refresh(index=index_name)
es.indices.forcemerge(index=index_name, max_num_segments=1, request_timeout=120)

bulk(es, vector_actions(), chunk_size=50, max_retries=10, request_timeout=60)

es.indices.refresh(index=index_name)
es.indices.forcemerge(index=index_name, max_num_segments=1, request_timeout=300)