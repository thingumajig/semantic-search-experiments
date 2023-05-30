from nicegui import ui

exact_search = None
exact_search_flag = False

def menu() -> None:
    global exact_search

    def exact_search_change():
        global exact_search_flag, exact_search
        exact_search_flag = not exact_search_flag
        if exact_search_flag:
            exact_search.set_text("Exact search ✔️")
        else:
            exact_search.set_text("Exact search  ")

    # ui.link('Home', '/').classes(replace='text-white')
    # ui.link('A', '/a').classes(replace='text-white')
    # ui.link('B', '/b').classes(replace='text-white')
    # ui.link('C', '/c').classes(replace='text-white')

    with ui.menu() as menu_system:
        exact_search = ui.menu_item("Exact search  ", on_click=exact_search_change)
        ui.separator()
        ui.menu_item("Config ⚙️")

    ui.button(on_click=menu_system.open).props('flat icon=settings color=white')