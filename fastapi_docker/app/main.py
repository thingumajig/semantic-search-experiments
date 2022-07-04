from fastapi import FastAPI, Form
import sys
sys.path.append('./app')
import preparation as pr

app = FastAPI()

@app.get("/")
async def root():
    return "Ready!"

@app.post("/add_record/")
async def add_record(index: str = Form(default=""), column_name: str = Form(default=""), data: str = Form(default="")):
    return pr.add_record(index, column_name, data)

@app.post("/add_embs/")
async def add_embs(index: str = Form(default=""), id: str = Form(default=""), column_name: str = Form(default="")):
    return pr.add_embs(index, id, column_name)

@app.post("/get_by_id/")
async def get_by_id(index: str = Form(default=""), id: str = Form(default="")):
    return pr.get_by_id(index, id)

@app.post("/get_closest/")
async def get_closest(query: str = Form(default=""), num_results: str = Form(default="5")):
    return pr.get_closest(query, num_results)

@app.post("/reindex/")
async def reindex(index: str = Form(default=""), new_index: str = Form(default="")):
    return pr.reindex(index, new_index)

@app.get("/count/")
async def count(index: str = Form(default="")):
    return pr.count_index(index)

