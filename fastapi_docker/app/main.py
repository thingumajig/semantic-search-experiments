from fastapi import FastAPI, Form
import sys
sys.path.append('./app')
import preparation as pr

app = FastAPI()

@app.get("/")
async def root():
    return "Ready!"

@app.get("/prepare_img_data/")
async def prepare_img_data():
    num = pr.image_addition()
    return f"Done! {num} images added"

@app.get("/prepare_text_data/")
async def prepare_text_data():
    pr.news_addition()
    return "Done!"

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

@app.post("/create_mapping_and_reindex/")
async def create_mapping_and_reindex(index: str = Form(default=""),
                                     column_name: str = Form(default="")):
    return pr.create_mapping_and_reindex(index, column_name, empty_only=False)

@app.post("/reindex_existing_embs/")
async def reindex_existing_embs(index: str = Form(default="")):
    return pr.reindex_existing_embs(index)

@app.post("/semantic_search/")
async def semantic_search(index: str = Form(default=""), 
                column_name: str = Form(default=""), 
                query: str = Form(default=""), 
                num_results: str = Form(default="5"),
                data_columns: str = Form(default=""),
                img_flag: str = Form(default="False")):
    return pr.semantic_search(index, column_name, query, num_results, data_columns, img_flag)


