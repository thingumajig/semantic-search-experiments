from contextlib import contextmanager
from menu import menu
from nicegui import ui

from components import Toolbar, ToolbarTitle

filter_container = None
option_container = None
@contextmanager
def frame(navtitle: str):
    '''Custom page frame to share the same styling and behavior across all pages'''

    global filter_container, option_container
    ui.colors(primary='#6E93D6', secondary='#53B689', accent='#111B1E', positive='#53B689')
    with ui.header().classes('q-pa-sm gap-1', remove='q-pa-md gap-4'):
        with Toolbar().props('text-white'):
            ui.button().props('icon=menu flat round dense color=white').classes('q-mr-sm')
            # ui.separator().props('vertical dense inset')
            ToolbarTitle('Семантический поиск в документах')
            # ui.label('Семантический поиск в документах').classes('font-bold')
            # ui.label(navtitle)
            with ui.row():
                menu()
    # with ui.row().classes('absolute-center'):
    #     yield
    with ui.left_drawer(fixed=True, top_corner=False):
        with ui.expansion('Фильтры', icon='filter_alt').props('default-opened'):
            filter_container = ui.column()
        with ui.expansion('Опции', icon='gear').props('default-opened'):
            option_container = ui.column()

    with ui.column():
        yield