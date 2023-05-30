from typing import Any, Callable, Dict, Optional

from nicegui.events import ValueChangeEventArguments, handle_event

from nicegui.element import Element
from nicegui.elements.mixins.text_element import TextElement
from nicegui import globals

class Toolbar(Element):
    def __init__(self, inset = False) -> None:

        super().__init__('q-toolbar')
        if inset:
            self._props['inset'] = inset


class ToolbarTitle(TextElement):
    def __init__(self, text: str = '') -> None:
        """Label

        Displays some text.

        :param text: the content of the label
        """
        super().__init__(tag='q-toolbar-title', text=text)

class MTree(Element):

    def __init__(self, nodes: list, *,
                 node_key: str = 'id',
                 label_key: str = 'label',
                 children_key: str = 'children',
                 on_select: Optional[Callable] = None,
                 on_expand: Optional[Callable] = None,
                 on_tick: Optional[Callable] = None) -> None:
        """Tree
        Display hierarchical data using Quasar's `QTree <https://quasar.dev/vue-components/tree>`_ component.
        If using IDs, make sure they are unique within the whole tree.
        :param nodes: hierarchical list of node objects
        :param node_key: property name of each node object that holds its unique id (default: "id")
        :param label_key: property name of each node object that holds its label (default: "label")
        :param children_key: property name of each node object that holds its list of children (default: "children")
        :param on_select: callback which is invoked when the node selection changes
        :param on_expand: callback which is invoked when the node expansion changes
        :param on_tick: callback which is invoked when a node is ticked or unticked
        """
        super().__init__('q-tree')
        self._props['nodes'] = nodes
        self._props['node-key'] = node_key
        self._props['label-key'] = label_key
        self._props['children-key'] = children_key
        self._props['selected'] = []
        self._props['expanded'] = []
        self._props['ticked'] = []

        def update_prop(name: str, value: Any) -> None:
            if self._props[name] != value:
                self._props[name] = value
                self.update()

        def handle_selected(msg: Dict) -> None:
            update_prop('selected', msg['args'])
            handle_event(on_select, ValueChangeEventArguments(sender=self, client=self.client, value=msg['args']))
        self.on('update:selected', handle_selected)

        def handle_expanded(msg: Dict) -> None:
            update_prop('expanded', msg['args'])
            handle_event(on_expand, ValueChangeEventArguments(sender=self, client=self.client, value=msg['args']))
        self.on('update:expanded', handle_expanded)

        def handle_ticked(msg: Dict) -> None:
            update_prop('ticked', msg['args'])
            handle_event(on_tick, ValueChangeEventArguments(sender=self, client=self.client, value=msg['args']))
        self.on('update:ticked', handle_ticked)


    def update_prop(self, name: str, value: Any) -> None:
        if self._props[name] != value:
            self._props[name] = value
            self.update()
