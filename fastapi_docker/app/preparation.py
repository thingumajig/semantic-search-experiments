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
                      column_name+"_emb": { "values": embed(hit["_source"][column_name]).numpy()[0] }
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
    es.indices.put_mapping(body=mapping, index=index_name,  )


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

def semantic_search(index, column_name, search_text, num_results):
    search_text_emb = embed(search_text).numpy()[0]
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

    res = es.search(index=index, body=body, size=int(num_results), _source=[column_name])
    return res