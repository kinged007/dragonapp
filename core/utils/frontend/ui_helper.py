"""
Helper functions for NiceGUI
"""
from nicegui import ui
from typing import Literal, Union, List, Dict, Optional, Any, Callable, Iterator
from core.utils.string import to_snake_case

def alert_info(message:str):
    ui.label(message).classes("full-width bg-blue-100 border-t border-b border-blue-500 text-blue-700 px-4 py-3")
def alert_warning(message:str):
    ui.label(message).classes("full-width bg-yellow-100 border-t border-b border-yellow-500 text-yellow-700 px-4 py-3")
def alert_error(message:str):
    ui.label(message).classes("full-width bg-red-100 border-t border-b border-red-500 text-red-700 px-4 py-3")
def alert_success(message:str):
    ui.label(message).classes("full-width bg-green-100 border-t border-b border-green-500 text-green-700 px-4 py-3")
def alert_primary(message:str):
    ui.label(message).classes("full-width bg-blue-100 border-t border-b border-blue-500 text-blue-700 px-4 py-3")
def alert_secondary(message:str):
    ui.label(message).classes("full-width bg-gray-100 border-t border-b border-gray-500 text-gray-700 px-4 py-3")
def alert_danger(message:str):
    ui.label(message).classes("full-width bg-red-100 border-t border-b border-red-500 text-red-700 px-4 py-3")


def json_schema_parser(schema:Dict[str,Any],  defs:str = "$defs" ):
    """
    Parse JSON schema to useable dictionary comatible with DragonApp FormBuilder.
    # TODO build JSON Schema parser method
    
    Args:
    - schema: JSON schema
    - defs: key for definitions. default is "$defs"
    
    Returns:
    - schema: parsed JSON schema
    
    """
    if not any(k in schema for k in ['type','properties','title']):
        # Not a valid schema
        raise ValueError('Invalid JSON schema')
    
    new_schema = {
        'type': schema.get('type', None),
        'title': schema.get('title', None),
        'required': False,
        'format': schema.get('format', None),
        'properties': {}
    }
    
    return new_schema


def table(rows:list, row_key:str, columns:list = None,  title:str = "", selection:Literal['multiple','single'] = 'single', pagination:Union[dict,int] = {'rowsPerPage': 10, 'page': 1}, on_select:callable = None, on_pagination_change: callable = None) -> ui.table:
    """
    Table component
    
    Args:
    - columns: list of column name objects: [{'name': 'Name', 'label': 'label', 'field': 'related field name','sortable':True,'align':'left','classes':'','headerClass':''}, ...]
    - rows: list of row objects: [{'id': 1, 'name': 'John Doe', 'age': 30}, ...]
    - row_key: key to identify each row. Should be unique value
    - title: table title
    - selection: 'multiple' or 'single'
    - pagination: {'rowsPerPage': 10, 'page': 1} or 10
    
    """
    if not columns:
        columns = []
        _added_keys = []
        _col_count = 0
        for key in rows[0].keys():
            if key not in _added_keys:        
                _hidden = _col_count > 6 or key in ['id','_id','created_on','updated_on','created_by','updated_by', row_key]
                # Hide if value is not a string/int/float/bool
                _hidden = _hidden or type(rows[0].get(key,None)) not in [str, int, float, bool ]
                columns.append({
                    'name': key,
                    'label': to_snake_case(key),
                    'field': key,
                    'sortable': True,
                    'align': 'right' if type(rows[0].get(key,None)) in [int,float] else 'left',
                    'classes': 'hidden' if _hidden else '',
                    'headerClasses': 'hidden' if _hidden else '',

                })
                _col_count += 1 if not _hidden else 0
                _added_keys.append(key)
    # Preprocess rows, cant display dict, convert to string       
    _table_items = []
    for item in rows:
        _table_items.append({k:str(v) for k,v in item.items()})
    
    table = ui.table(
        columns=columns,
        rows=rows,
        selection=selection,
        row_key=row_key,
        title=title,
        pagination=pagination,
        on_pagination_change=on_pagination_change,
        on_select=on_select,
    )
    
    return table


def table_buttons(table:ui.table, options:List[Literal['fullscreen','columns','search','refresh']], real_rows:List[dict] = None):
    """
    Table slot component
    
    Args:
    - table: table component
    - options: list of options to display: ['fullscreen','columns','search','refresh']
    - real_rows: list of rows to display in json viewer. Use callback (lambda) to get the rows if rows are updated during operation
    
    """
    
    def toggle_fullscreen():
        table.toggle_fullscreen()
        button.props('icon=fullscreen_exit' if table.is_fullscreen else 'icon=fullscreen')
    def toggle_cols(column: dict, visible: bool) -> None:
        column['classes'] = '' if visible else 'hidden'
        column['headerClasses'] = '' if visible else 'hidden'
        table.update()
    def view_json():
        if real_rows:
            if callable(real_rows):
                _rows = real_rows()
            else:
                _rows = real_rows
            _selected_rows = [r.get(table.row_key) for r in table.selected]
            _json = [l for l in _rows if l.get(table.row_key) in _selected_rows]
        else:
            _json = table.selected
        __json_viewer.run_editor_method('updateProps', {'content': {'json': _json}})
        dialo_json_viewer.open()

    with ui.row() as row:
        
        for opt in options:
                
            if 'search' == opt:
                # ui.input().bind(table.search, placeholder='Search')
                pass
            
            if 'json' == opt:
                with ui.dialog() as dialo_json_viewer:
                    __json_viewer = ui.json_editor({'content': {'json': []}}).props('full-width')
                    
                ui.button(icon='data_object', on_click=view_json).props('flat')
                    
            if 'fullscreen' == opt:
                button = ui.button(None, icon='fullscreen', on_click=toggle_fullscreen).props('flat')
            if 'columns' == opt:
                with ui.button(icon='visibility_off').props('flat'):
                    with ui.menu(), ui.column().classes('gap-0 p-2'):
                        for column in table.columns:
                            ui.switch(column['label'], value=True if column['classes']=='' else False, on_change=lambda e,
                                    column=column: toggle_cols(column, e.value))

    return row