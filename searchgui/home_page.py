from nicegui import ui
import asyncio
import theme as th
from components import MTree

index_name = 'labor_law'
columns_to_add_as_text = [
    "party",
    "section_number",
    "section_text",
    "chapter_number",
    "chapter_text",
    "article_number",
    "article_text",
    "text",
    "href",
    "doc_structure_tags",
    "source_law",
]

top_k = 50
min_score = 1.306

aggs_sequence = ["party", "section_number", "chapter_number", "article_number"]
def filter_body(filters):
    fs = []
    for x in filters:
        if type(x) is tuple:
            fs.append({"term":{x[0]:x[1]}})
        elif type(x) is str:
            t = x.split(':', maxsplit=1)
            fs.append({"term":{t[0]:t[1]}})
    return fs

def search(es, embedder, query, search_model='lsh'):
    query_vec = embedder(query).numpy()[0]
    # %%
    body = {
        "min_score": 1,
        "query": {
            "elastiknn_nearest_neighbors": {
                "field": "text_emb",  # 1
                "vec": {  # 2
                    "values": query_vec
                },
                "model": search_model,  # 3
                "similarity": "cosine",  # 4
                "candidates": 50  # 5
            }
        }
    }

    return es.search(index=index_name, body=body, size=20, _source=columns_to_add_as_text)

def complex_search(es, embedder, query, search_model='exact', filters=[]):
    print(f'Filters:{filters}')

    query_vec = embedder(query).numpy()[0]
    body = {
        "size": top_k, "min_score": min_score,
        "query": {
            "bool": {
                "must": {
                    "elastiknn_nearest_neighbors": {
                        "field": "text_emb",  # 1
                        "vec": {  # 2
                            "values": query_vec
                        },
                        "model": "exact",  # 3
                        "similarity": "cosine",  # 4
                        "candidates": 50  # 5
                    }
                },
                "should": {
                    "match": {
                        "article_text": {
                            "query": query
                        }
                    }
                },
                "filter": filter_body(filters),
            }
        },

        "aggs": {
            "party_a": {
                "terms": {"field": "party"},
                "aggs": {
                    "section_number_a": {
                        "terms": {"field": "section_number"},
                        "aggs": {
                            "chapter_number_a": {
                                "terms": {"field": "chapter_number"},
                                "aggs": {
                                    "article_number_a": {
                                        "terms": {"field": "article_number"}
                                    }
                                }
                            },
                        },
                    },
                }

            },

        },
    }

    return es.search(index=index_name, body=body, size=10, _source=columns_to_add_as_text)



def content(es, embedder) -> None:
    container = None


    def show_hits(query, filters):
        ui.notify('Поиск запущен...', closeBtn=True)
        container.clear()
        res = complex_search(es, embedder, query, filters=filters)

        with ui.footer().classes('text-white'):
            ui.label(
                f"Найдено {res['hits']['total']['value']} пунктов за {res['took']} ms. Показано первые {len(res['hits']['hits'])}.")

        with container:
            # with ui.card().tight() as card:
            #     ui.image('http://placeimg.com/640/360/nature')
            #     with ui.card_section():
            #         ui.label('Lorem ipsum dolor sit amet, consectetur adipiscing elit, ...')

            for hit in res['hits']['hits']:
                with ui.card().tight() as card:
                    s = hit['_source']
                    # print(f"Id:{s.get('db_id', None)} Title   {s.get('title', None)}")
                    section_text = s.get('section_text').replace('_x000D_\n', ' ')
                    chapter_text = s.get('chapter_text').replace('_x000D_\n', ' ')
                    with ui.card_section():
                        ui.label(
                            f"({hit.get('_id')}) {s.get('source_law')}: {s.get('party')} > {s.get('section_number')} {section_text} > {s.get('chapter_number')} {chapter_text} > {s.get('article_number')}").classes(
                            'font-bold')
                        ui.label(s.get('text'))
                        with ui.row():
                            ui.label(f"🔹Score: {hit.get('_score', None) - 1.:.3f}").classes("font-small")
                            ui.link(text='🔗 Контекст', target=s.get('href'), new_tab=True).style('text-decoration: none').classes('font-small')


        show_facets(res, query, filters)
        ui.notify('Поиск закончен...', closeBtn=True)

    def show_facets(res, query, filters):
        th.filter_container.clear()
        with th.filter_container:
            aggs = res['aggregations']
            cc = 0

            def reccurent_aggs(aggs, level=0):
                nonlocal cc
                buckets = aggs['buckets']
                tree = []
                for b in buckets:
                    indent = '-' * level

                    id = f"{aggs_sequence[level]}:{b['key']}"
                    if level + 1 < len(aggs_sequence) and aggs_sequence[level + 1] + '_a' in b.keys():
                        # ui.checkbox(f"{indent} {b['key']}").props('dense left-label size=xs checked-icon=star')
                        children = reccurent_aggs(b[aggs_sequence[level + 1] + '_a'], level + 1)
                        cc += 1
                        tree.append({'id': id, 'name': b['key'], 'children': children})
                    else:
                        # ui.checkbox(f"{indent}{b['key']}: {b['doc_count']}").props('dense left-label size=xs checked-icon=star')
                        cc += 1
                        tree.append({'id': id, 'name': f"{b['key']}  :{b['doc_count']}"})
                return tree

            tree_list = reccurent_aggs(aggs[aggs_sequence[0] + '_a'], 0)
            # print(tree_list)

            # ui.tree(tree_list, node_key='id', label_key='name', children_key='children', on_select=lambda e: ui.notify(f'{e.value} xx:{e}')).props('default-expand-all dense tick-strategy=strict')
            facet_tree = MTree(tree_list, node_key='id', label_key='name', children_key='children',
                  on_select=lambda e: ui.notify(f'{e.value} xx:{e}'),
                  on_tick=lambda e: show_hits(query, e.value),
                  ).props('default-expand-all dense tick-strategy=leaf')
            facet_tree.update_prop('ticked', filters)


    ## Main body
    with ui.row().props('dense').classes('items-center'):
        with ui.input(placeholder='Введите запрос здесь').style('width:600px').props('outlined input-style=padding:0 dense') as search_input:
            ui.button(on_click=lambda: show_hits(search_input.value, filters=[])).props('flat icon=search dense')

    with ui.row():
        container = ui.column()