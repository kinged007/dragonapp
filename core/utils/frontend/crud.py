# from beanie import Document
from nicegui import ui
from typing import List, Dict, Any, Tuple, Optional, Union

import pymongo.collection
from core.utils.database import Database
from core.schemas.database import DatabaseMongoBaseModel

import pymongo
from bson import ObjectId
from datetime import datetime, timedelta, timezone

from core.utils.logging import logger as log, print
from core.utils.string import to_snake_case
from core.utils.frontend.form_builder import FormBuilder
from core.utils.frontend import ui_helper
from core.utils.cache import SimpleCache
from core.events import trigger_event



# @ui.refreshable
# async def mongo_list_items(db:pymongo.collection.Collection) -> None:
#     async def delete(item) -> None:
#         # item.delete()
#         print(item)
#         _id = item.get('id', item.get('_id', None))
#         if _id:
#             print(db.delete_one({'_id': ObjectId(item['_id'])}))
#         mongo_list_items.refresh()

#     items: List[db] = list(db.find({}))
    
#     for item in reversed(items):
#         item = {k:str(v) if type(v) == ObjectId else v for k,v in item.items()}
#         with ui.card():
#             print(type(item), item)
#             ui.json_editor({'content': {'json': item }})
#             with ui.row().classes('items-center full-width px-4'):
#                 # ui.input('Name', on_change=item.save) \
#                 ui.input('Name') \
#                     .bind_value(item, 'name').on('blur', mongo_list_items.refresh)
#                 # ui.number('Age', on_change=item.save, format='%.0f') \
#                 ui.input('Nationality') \
#                     .bind_value(item, 'nationality').on('blur', mongo_list_items.refresh).classes('w-20')
#                 ui.button(icon='delete', on_click=lambda u=item: delete(u)).props('flat')


class CrudBuilder:
    
    base_model: DatabaseMongoBaseModel = None
    db:pymongo.collection.Collection = None
    db_name:str = None
    date_format:str = "%Y-%m-%d %H:%M:%S"
    new_dialog: ui.dialog = None
    edit_dialog: ui.dialog = None
    _cache: SimpleCache = SimpleCache()
    
    def __init__(self, 
            base_model: Optional[DatabaseMongoBaseModel] = None,
            # TODO remove these options. CRUD builder will be based on the model itself as it interacts with the db.
            collection:Optional[pymongo.collection.Collection] = None, 
            schema: Optional[dict] = None,
            module_name: Optional[str] = None,
        ) -> None:
        """
        Database CRUD Builder. Collection AND Schema are required to build the CRUD interface. 
        If you pass a base_model, the schema will be generated from the model.
        
        Args:
            collection (Optional[pymongo.collection.Collection], optional): Database Collection. Defaults to None.
            schema (Optional[dict], optional): JSON Schema for the model. Defaults to None.
            base_model (Optional[DatabaseMongoBaseModel], optional): Base Model for the database. Defaults to None.
        """
        # Determine the type of database
        # if the database is a Document
        
        self.module_name = module_name
        
        if base_model and issubclass(base_model, DatabaseMongoBaseModel):
            self.db_name = base_model.Settings.name
            self.db = Database.get_collection(self.db_name)
            self.schema = base_model.model_json_schema()
            self.base_model: DatabaseMongoBaseModel = base_model
        elif collection and schema:
            self.db = collection
            self.schema = schema
            self.db_name = collection.name
        else:
            raise Exception("Collection and Schema are required, OR a Base Model is required.")
        
        self._table = None
    
    def _friendly_format(self, item:dict):
        _output = {}
        for k,v in item.items():
            if type(v) == ObjectId:
                _output[k] = str(v)
            elif type(v) == datetime:
                _output[k] = v.strftime(self.date_format)
            else:
                _output[k] = str(v)
        return _output
    
    ### Actions and Callbacks
    def _create(self, data:dict):
        try:
            print("CRUD CREATE SUBMITTED", data)
            
            model_data = self.base_model(**data)
            _json = model_data.model_dump_json()
            log.debug("Got JSON: "+ str(_json) )
            res = self.db.insert_one(_json)
            if res and res.inserted_id:
                log.debug(f"Successful insert. Inserted ID: {res.inserted_id}")
                self.new_dialog.close()
                new_item = self.db.find_one({'_id': res.inserted_id})
                if new_item:
                    self._table.add_rows(self._friendly_format(new_item))
                    self._table.update()
                    self._table.run_method('scrollTo', len(self._table.rows)-1)
                    ui.notification('Created new item', position='bottom', type='positive', icon='check', timeout=10, close_button=True)
                
                # Trigger event
                trigger_event('crud_item_created', module=self.module_name, item=new_item, base_model=self.base_model)
                
                return True
            raise Exception(str(res))
        except Exception as e:
            log.error(e)
            ui.notification('Error: '+str(e), position='bottom', type='negative', icon='error', timeout=60, close_button=True)
        
        return False
    
    def _edit(self, data:dict):
        try:
            pass
            print("EDIT", data)            
            model_data = self.base_model(**data)
            _json = model_data.model_dump_json()
            log.debug("Got JSON: "+ str(_json) )
            _edit = {k:v for k,v in _json.items() if k not in ['_id']}
            res = self.db.update_one({'_id': ObjectId(data.get('_id'))}, {'$set': _edit })
            # print(res, res.__dict__)
            # if res and res.modified_count == 1: # NOTE no modified_count with tinyMongo
            if res and res.acknowledged == True:
                log.debug(f"Successful update. Item ID: {data.get('_id')}")
                self.edit_dialog.close()
                # new_item = self.db.find_one({'_id': res.inserted_id})
                # if new_item:
                #     self._table.add_rows(self._friendly_format(new_item))
                self._table.update_rows(self.items({}))
                # self._table.update()
                #     self._table.run_method('scrollTo', len(self._table.rows)-1)
                ui.notification('Updated item', position='bottom', type='positive', icon='check', timeout=10, close_button=True)
                
                # Trigger event
                trigger_event('crud_item_modified', module=self.module_name, item=_json, base_model=self.base_model)
                
                return True
            raise Exception(str(res))
        except Exception as e:
            log.error(e)
            ui.notification('Error: '+str(e), position='bottom', type='negative', icon='error', timeout=60, close_button=True)
        
        return False
    
    def _delete(self, items:Union[Dict, List[Dict]]):
        if isinstance(items, dict):
            items = [items]
        _delete = []
        try:
            for item in items:
                _id = item.get('_id', item.get('id', None))
                if _id:
                    _delete.append({'_id': ObjectId(_id)})
            if _delete:
                _q = {'$or': _delete} 
                res = self.db.delete_many( _q )
                if res:
                    log.debug(res.raw_result)
                    log.debug(res.acknowledged)
                    log.debug(res.deleted_count)
                    self._table.remove_rows(*items)
                    self._table.update()
                    ui.notification('Deleted items', position='bottom', type='positive', icon='check', timeout=10, close_button=True)
                    
                    # Trigger event
                    trigger_event('crud_item_deleted', module=self.module_name, item=items, base_model=self.base_model)
                
                else:
                    raise Exception(str(res))
        except Exception as e:
            log.error(e)
            ui.notification('Error: '+str(e), position='bottom', type='negative', icon='error', timeout=60, close_button=True)
    
    def _view(self):
        pass
    
    def get_selected_items(self):
        if len(self._table.selected)>0:
            return [r for r in self.db_items if r.get('_id') in [i.get('_id') for i in self._table.selected]]
        return []
        
        
    # @ui.refreshable
    def items(self, query:dict = {}) -> None:
        
        self.db_items: List[self.db] = list(self.db.find(query))
        self.table_items: List[self.db] = []
        
        for item in reversed(self.db_items):
            item = self._friendly_format(item)
            self.table_items.append(item)
        
        print("CRUD ITEMS", self.table_items)
        return self.table_items
    
    # def _create_form(self):
    #     with ui.dialog() as dialog:
    #         with ui.form():
    #             ui.json_editor(self.schema)
    #             ui.button('Create', on_click=self._create)
    #     pass
    
    def build(self):
        """
        Simple method that builds a complete CRUD interface for a database, using a default template/layout.
        A CRUD interface may be customized by calling each method individually.
        """
        with ui.column().classes('full-width'):
            
            with ui.row().classes('full-width px-4'):
                self.button_new().props('flat') # schema = different_model.model_json_schema() 
                # self.button_edit()
                self.button_delete().props('flat')
                self.button_edit().props('flat')
                
                # Trigger event
                # TODO Transfer the selected table items to the callback!? 
                trigger_event('crud_interface_top_left', module=self.module_name, base_model=self.base_model, selected_items=lambda: self.get_selected_items() )
                
                ui.space()
                
                self.search()
        #         self.filter()
        #         self.sort()
        
                # Trigger event
                trigger_event('crud_interface_top_right', module=self.module_name, base_model=self.base_model, selected_items=lambda: self.get_selected_items())
                
            # Trigger event
            trigger_event('crud_interface_before_table', module=self.module_name, base_model=self.base_model, selected_items=lambda: self.get_selected_items())

            self.table(
                multi_select = True, # adds checkboxes to each row
                pagination={'rowsPerPage': 10, 'page': 1},
                columns=None,
            )
            
            # Trigger event
            trigger_event('crud_interface_after_table', module=self.module_name, base_model=self.base_model, selected_items=lambda: self.get_selected_items())
            
        #     self.pagination()
            
            with ui.row():
                self.button_refresh()
                # self.button_save()
        #         self.button_cancel()
        #         self.button_settings()
        
                # Trigger event
                trigger_event('crud_interface_bottom_left', module=self.module_name, base_model=self.base_model, selected_items=lambda: self.get_selected_items())

                ui.space()
        #         self.button_export()
        #         self.button_import()
        
                # Trigger event
                trigger_event('crud_interface_bottom_right', module=self.module_name, base_model=self.base_model, selected_items=lambda: self.get_selected_items())
                    
        
        return self
            
    def button_new(self, label = "New", icon='add', color='primary', schema=None) -> ui.button:
        """
        Button to create a new item
        """
        # TODO red Make the dialog wider. Explore option of using sidebar instead?
        with ui.dialog().classes().props() as self.new_dialog, ui.card().classes().style("max-width:70vw"):
        # with ui.right_drawer(value=False, bordered=True, elevated=True, fixed=True).classes('') as self.new_dialog:
            with ui.card_section().classes('full-width col-md-8'):
                ui.label('Create New Item').classes('text-lg font-bold')
                ui.button(icon="close", on_click=self.new_dialog.close).props('flat dense').classes('absolute top-5 right-5')
            
            ui.separator()
            
            with ui.card_section().classes('full-width col-md-8 scroll').style("max-height:50vh"):
                # ui.json_editor({'content': {'json': self.schema }})
                # with ui.row():
                #     with ui.button("Close", on_click=lambda: self.new_dialog.toggle()).props('flat'):
                #         ui.icon('close')
                #     ui.label('Create New Item').classes('text-lg font-bold')
                form = FormBuilder(self.schema if not schema else schema, {}, self._create )
                form.submit_value = 'Create'
                form.clear_on_submit = True
                # form.build()
                form.build_main_form()

                # ui.button('Create', on_click=self._create)
            
            ui.separator()
            
            with ui.card_actions().classes('full-width col-md-8'):
                form.submit_button()
                ui.button('Cancel', on_click=self.new_dialog.close).props("primary")
                # ui.button('Create', on_click=self._create).props('positive')

        return ui.button(label, on_click=self.new_dialog.open, icon=icon, color=color)
        # return ui.button(label, on_click=lambda: self.new_dialog.toggle(), icon=icon, color=color)
    
    def button_delete(self, label = "Delete", icon='delete', color='negative') -> ui.button:
        """
        Button to delete an item
        """
        with ui.dialog() as dialog, ui.card():
            ui.label('Are you sure you want to delete these items?')
            with ui.row():
                with ui.button('Delete', on_click=lambda: _delete()).props('negative'):
                    ui.icon('delete')
                ui.button('Close', on_click=dialog.close).props("primary")
            
        def _confirm():
            # lambda: self._table.remove_rows(*self._table.selected)
            if not self._table.selected:
                ui.notification('No items selected', position='bottom', type='negative', icon='error', timeout=10, close_button=True)
                return
            dialog.open()

        def _delete():
            self._delete(self._table.selected)
            dialog.close()

            # ui.label().bind_text_from(self._table, 'selected', lambda val: f'Current selection: {val}')
            pass
        
        # if self._table:
        return ui.button(label, icon=icon, color=color, on_click=_confirm)\
            .bind_visibility_from(self._table, 'selected', backward=lambda val: len(val)>0 )
            # TODO fix the visibility binding

        # return ui.button(label, icon=icon, color=color, on_click=_delete)
    
    def button_edit(self, label = "Edit", icon='edit', color='primary', schema:dict = None) -> ui.button:
        
        def _edit():
            
            if not self._table.selected:
                ui.notification('No item selected.', position='bottom', type='negative', icon='error', timeout=10, close_button=True)
                return
            
            if len(self._table.selected) > 1:
                ui.notification('Only one item can be edited at a time', position='bottom', type='negative', icon='error', timeout=10, close_button=True)
                return
            
            try:
                item = [i for i in self.db_items if i.get('_id') == self._table.selected[0]['_id']][0]
            except Exception as e:
                # log.error(e)
                ui.notification('Error: '+str(e), position='bottom', type='negative', icon='error', timeout=60, close_button=True)
                return
            
            # item = self._table.selected[0]
            
            with ui.dialog().classes('px-4 py-2 full-width') as self.edit_dialog, ui.card().classes('').style("max-width:70vw"):
                with ui.card_section().classes('full-width col-md-8'):
                    ui.label('Update Item').classes('text-lg font-bold')
                    ui.button(icon="close", on_click=self.edit_dialog.close).props('flat dense').classes('absolute top-5 right-5')

                ui.separator()
                
                with ui.card_section().classes('full-width col-md-8 scroll').style("max-height:50vh"):
                    form = FormBuilder(self.schema if not schema else schema, item, self._edit )
                    form.submit_value = 'Update'
                    form.clear_on_submit = True
                    # form.build()
                    form.build_main_form()

                    # ui.button('Create', on_click=self._create)
                
                ui.separator()
                
                with ui.card_actions().classes('full-width col-md-8'):
                    form.submit_button()
                    ui.button('Cancel', on_click=self.edit_dialog.close).props("primary")
                    # ui.button('Create', on_click=self._create).props('positive')

            self.edit_dialog.open()
        
            
        return ui.button(label, icon=icon, color=color, on_click=_edit ).bind_visibility_from(self._table, 'selected', backward=lambda val: len(val)==1 )
        # TODO fix the visibility binding
    
    
    def button_refresh(self, label = "Refresh", icon='refresh', color='primary') -> ui.button:
        """
        Button to refresh the table
        """
        def _refresh():
            self._table.update_rows(self.items({}))
            
        return ui.button(label, icon=icon, color=color, on_click=_refresh)
    
    def search(self, label = "Search", icon='search', color='primary') -> ui.input:
        """
        Search input field
        """
        @self._cache.cache(ttl=30)
        def _search(e):
            # TODO Set a rate limit on the db requests. ie. throttle the on_change event
            # TODO implement other fields from the schema instead of hardcoding 'name' and to allow for multi column searching.
            log.error(e.value)
            _query = e.value
            self._table.update_rows(self.items({'$or': [{'name': {'$regex': _query, '$options': 'i'}},]}))
        return ui.input(label, on_change=_search)
    
    def preprocess_table(self, data:List[dict]) -> List[dict]:
        """
        Preprocess the table data before displaying
        """
        """
        # TODO Implement slot templates for links and other custom cells
        # Customer cells: links, buttons, etc.
        table.add_slot('body-cell-link', '''
            <q-td :props="props">
                <a :href="props.value">{{ props.value }}</a>
            </q-td>
        ''')
        return data, (slot_name, slot_template)
        """
        _out = []
        for item in data:
            _out.append({k:str(v) for k,v in item.items()})
        return _out
    
    def table(self, multi_select:bool = False, columns: list = [], pagination:Union[dict,int] = {'rowsPerPage': 10, 'page': 1} ) -> ui.table:
        """
        Simple Table to display items
        """
        _data = list(self.items({}))
        _added_keys = []
        _col_count = 0
        #Use passed columns arg for matching to schema IF str value, if dict, use that instead
        if not columns or len(columns) == 0:
            if columns == None:
                columns = []
            for field, properties in self.schema.get('properties', {}).items():
                if field not in _added_keys:            
                    # Hide columns with more than 5 fields or if it's a system field
                    _hidden = _col_count > 5 or field in ['id','_id','created_on','updated_on','created_by','updated_by']
                    # Hide if value is not a string/int/float/bool
                    _hidden = _hidden or properties.get('type', 'string') not in ['string','integer','number','boolean']
                    
                    # Hide if it's a reference field
                    if field in ['id','_id']: 
                        # is it id or _id ?
                        field = '_id'
                    
                    # Append the column to the list
                    columns.append({ 
                        'name': field,
                        'label': properties.get("title") or to_snake_case(field),
                        'field': field,
                        'sortable': True,
                        'align': 'right' if _data and type(_data[0].get(field,None)) == int else 'left',
                        'classes': 'hidden' if _hidden else '',
                        'headerClasses': 'hidden' if _hidden else '',
                    })
                    _col_count += 1 if not _hidden else 0
                    _added_keys.append(field)
                    
        # Action buttons
        # columns.append({
        #     'label': 'Actions',
        #     'field': 'actions',
        #     'sortable': False,
        #     'align': 'right',
        #     'classes': '',
        #     'headerClasses': '',
        # })
        # log.debug(columns)
        rows = _data #self.preprocess_table(_data)
        
        table = ui.table(
            columns = columns,
            rows=rows,
            selection='multiple' if multi_select else 'single',
            row_key='id' if 'id' in _added_keys else '_id',
            title=to_snake_case(self.schema.get('title', None)),
            pagination=pagination,
            
        ).classes('full-width')
        
        # Save the table to the global space
        self._table = table
        
        with self._table.add_slot('top-right'):
            # Trigger event
            trigger_event('crud_interface_table_slot_top_right', module=self.module_name, base_model=self.base_model)

            ui_helper.table_buttons(self._table, ['search','refresh','json','fullscreen','columns'], real_rows=self.db_items)
            
            # def toggle_fullscreen():
            #     self._table.toggle_fullscreen()
            #     button.props('icon=fullscreen_exit' if self._table.is_fullscreen else 'icon=fullscreen')
            # def toggle_cols(column: Dict, visible: bool) -> None:
            #     column['classes'] = '' if visible else 'hidden'
            #     column['headerClasses'] = '' if visible else 'hidden'
            #     self._table.update()

            # with ui.row():
            #     button = ui.button(None, icon='fullscreen', on_click=toggle_fullscreen).props('flat')
            #     with ui.button(icon='visibility_off').props('flat'):
            #         with ui.menu(), ui.column().classes('gap-0 p-2'):
            #             for column in columns:
            #                 ui.switch(column['label'], value=True if column['classes']=='' else False, on_change=lambda e,
            #                         column=column: toggle_cols(column, e.value))

        return table
    
    def aggrid(self, data:List[dict]) -> ui.aggrid:
        """
        AG-Grid Table to display items
        """
        return ui.aggrid({
            # 'defaultColDef': {'flex': 1},
            'columnDefs': [
                {'headerName': 'Name', 'field': 'name'},
                {'headerName': 'Age', 'field': 'age'},
                {'headerName': 'Parent', 'field': 'parent', 'hide': True},
            ],
            'rowData': [
                {'name': 'Alice', 'age': 18, 'parent': 'David'},
                {'name': 'Bob', 'age': 21, 'parent': 'Eve'},
                {'name': 'Carol', 'age': 42, 'parent': 'Frank'},
            ],
            'rowSelection': 'multiple',
        })
        
"""
From streamlit dragon panel


import requests
from loguru import logger as log
from typing import Iterable
from time import sleep
from typing import Optional, Union
import pandas as pd

from core.form import process_form_submission, dict_to_form_elements, create_form_element, config_field_schema_to_form_elements, ConfigFieldConfig, ConfigField

class CRUDBuilder:
    
    
    def __init__(self, 
        st,
        endpoint:str, # URL endpoint
        data_key:str = "data", # default if using CRUDEndpoints
        headers:dict = {},
        name_singular:str = "",
        name_plural:str = "",
        methods:list = ['get','patch','post','delete'],
        data_frame: Optional[Union[pd.DataFrame, dict, list]] = None,
        # Move the below items to view_table() args
        insert_from_table: bool = True,
        use_container_width:bool = True,
        hide_index:bool = True,
        column_order:list = [],
        column_config:dict = {},
        disabled: bool | Iterable[str] = False,
        ):
        self.st = st
        self.endpoint = endpoint.strip("/")
        self.data_key = data_key
        self.name_singular = name_singular
        self.name_plural = name_plural
        self.headers = headers
        self.methods = [m.upper() for m in methods]
        self.data_frame = data_frame
        if not name_plural or not name_singular:
            raise Exception("Name_singular and Name_plural are required.")
        
        # Move the below items to view_table() args
        # self.use_container_width = use_container_width
        # self.hide_index = hide_index
        # self.column_order = column_order
        # self.column_config = column_config
        # self.disabled = disabled 
        # self.insert_from_table = insert_from_table
        
        # self.build()
        
    
    def _server_request(self, endpoint, method="GET", data=None, params=None):
        try:
            
            endpoint = endpoint.strip("/")
            
            method = method.upper()
            
            headers = self.headers
            
            if method == "GET":
                res = requests.get(f"{self.endpoint}/{endpoint}", headers=headers)
            elif method == "POST":
                res = requests.post(f"{self.endpoint}/{endpoint}", headers=headers, json=data)
            elif method == "PUT":
                res = requests.put(f"{self.endpoint}/{endpoint}", headers=headers, json=data)
            elif method == "DELETE":
                res = requests.delete(f"{self.endpoint}/{endpoint}", headers=headers, json=data)
            elif method == "PATCH":
                res = requests.patch(f"{self.endpoint}/{endpoint}", headers=headers, json=data)
            else:
                raise Exception("Invalid method")
            return res

        except Exception as e:
            log.error(e)

        return None
    
    def build(self):
        log.warning("build() is deprecated. Use view_table() instead.")
        return self.view_table()
            
    def view_table(self,
        insert_from_table: bool = True,
        use_container_width:bool = True,
        hide_index:bool = True,
        column_order:list = [],
        column_config:dict = {},
        disabled: bool | Iterable[str] = False,
        data_frame: Optional[Union[pd.DataFrame, dict, list]] = None,
    ):
        # Get data to start with
        if data_frame: self.data_frame = data_frame
        
        if not self.data_frame and self.name_plural:
            data = self._server_request(self.name_plural, method="GET")
            if data.status_code != 200 or not data.json():
                self.st.error("Error fetching data")
                return
            try:
                data = data.json()
                data = data[self.data_key]
            except:
                pass
        
        else :
            data = self.data_frame
        
        self.data_frame = data
        
        self.st.data_editor(
            data, 
            key=self.name_plural, 
            use_container_width=use_container_width, 
            hide_index=hide_index, 
            column_order=column_order, 
            column_config=column_config,
            num_rows = "dynamic" if any(x in self.methods for x in ["POST","DELETE","PATCH"]) else "fixed",
            disabled = disabled
        )
        
        c1,c2,c3 = self.st.columns([0.5,0.5,1])
        with c1:
            if self.st.button("Refresh"):
                self.st.rerun()
        with c2:
            _changes = self.st.session_state[self.name_plural]
            if _changes.get('added_rows', None) or _changes.get('edited_rows', None) or _changes.get('deleted_rows', None):
                
                # if _changes.get('added_rows', None) and 'POST' not in self.methods:
                #     self.st.warning("Adding New Rows are disabled.")
                # elif _changes.get('deleted_rows', None) and 'DELETE' not in self.methods:
                #     self.st.warning("Deleting Rows are disabled.")
                # elif _changes.get('edited_rows', None) and 'PATCH' not in self.methods:
                #     self.st.warning("Editing Rows are disabled.")
                # else:
                if self.st.button("Save changes", type="primary"):
                    _success = False
                    
                    if _changes.get('added_rows', None) and 'POST' in self.methods and insert_from_table:
                        res = self._server_request(self.name_singular, method="POST", data=_changes['added_rows'])
                        if res.status_code == 200:
                            self.st.toast("Added rows", icon="🎉")
                            _success = True
                        else:
                            self.st.error(str(res.json()), icon="🚨" )
                    elif _changes.get('added_rows', None) and 'POST' not in self.methods:
                        self.st.warning("Adding New Rows are disabled.")
                        
                    if _changes.get('deleted_rows', None) and 'DELETE' in self.methods:
                        for i in _changes['deleted_rows']:
                            res = self._server_request(f"{self.name_singular}/{data[i]['id']}", method="DELETE")
                            if res.status_code == 200:
                                self.st.toast("Deleted row", icon="🎉")
                                _success = True
                            else:
                                self.st.toast(str(res.json()), icon="🚨" )
                    elif _changes.get('deleted_rows', None) and 'DELETE' not in self.methods:
                        self.st.warning("Deleting Rows are disabled.")

                    if _changes.get('edited_rows', None) and 'PATCH' in self.methods:
                        _update = []
                        for i, v in _changes['edited_rows'].items():
                            _update.append({
                                "id": data[i].get("id"),
                                **v
                            })
                        if _update:
                            res = self._server_request(self.name_plural, method="PATCH", data=_update)
                            if res.status_code == 200:
                                self.st.toast("Updated rows", icon="🎉")
                                _success = True
                            else:
                                self.st.error(str(res.json()), icon="🚨" )
                    elif _changes.get('edited_rows', None) and 'PATCH' not in self.methods:
                        self.st.warning("Editing Rows are disabled.")

                    if _success:
                        self.st.balloons()
                        sleep(1)
                        self.st.rerun()
                        
                # self.st.write(_changes) # DEBUG
        return self
    
    def get_data(self):
        return self.data_frame
    
    def set_data(self, data):
        self.data_frame = data
        return self
    
    def new_form(self):
        self.st.write("New Form")
        return self
    
    def edit_form(self,
        data: Optional[dict] = None,
        id: Optional[str] = None,
        schema: Optional[dict] = None,
        display_field: Optional[str] = None,
        use_columns: bool = False, 
        use_expander: set =(False, False), 
        # base_key="",
        callback: Optional[callable] = None 
    ):
        \"""
        Produces a form to select an item to edit. Use the schema and ConfigFieldConfig to customize the form.
        
        Args:
            data (Optional[dict], optional): Data to use. Defaults to None.
            id (Optional[str], optional): ID of the item to edit. Defaults to None.
            schema (Optional[dict], optional): Schema to use. Defaults to None.
            display_field (Optional[str], optional): Field to display in the selectbox. Defaults to None.
            use_columns (bool, optional): Use columns to display the form. Defaults to False.
            use_expander (set, optional): Use expander to display the form. Defaults to (False, False).
            callback (Optional[callable], optional): Callback to modify the data before displaying/editing the item. Defaults to None. Returns two arguments of data:dict and action:str (view, update, delete)
        \"""
        if 'POST' not in self.methods: 
            self.st.warning("Adding New Items are disabled.")
            return self
        
        if not data: data = self.data_frame
        
        # with self.st.container():
        self.st.subheader("Edit Item")

        id, form_data, action = process_form_submission()
        # self.st.write((id,form_data,action)) # DEBUG
        if id and form_data and action == 'save':
            if "PATCH" not in self.methods:
                self.st.warning("Editing Items are disabled.")
            else:
                try:
                    if callback:
                        _callback = callback(form_data, "update" )
                        if _callback: form_data = _callback
                        
                    res = self._server_request(self.name_singular + "/" + str(id), method="PATCH", data=form_data)
                    if res.status_code == 200:
                        self.st.toast("Updated item", icon="🎉")
                        self.st.balloons()
                        sleep(1)
                        self.st.rerun()
                    self.st.error("Error saving data")
                except Exception as e:
                    self.st.error(e)
        
        item = self.st.selectbox("Select item", options=data, index=None, format_func=lambda x: x.get(display_field, x.get("id")))
        
        
        if item:
            if callback:
                _callback = callback(item, "view" )
                if _callback: item = _callback
            
            base_key = item.get('id')
            with self.st.form(key=base_key):
                # self.st.json(item)
                if schema:
                    # Need to add values from data to the schema.
                    config_field_schema_to_form_elements(self.st, schema,use_columns=use_columns, use_expander=use_expander, base_key=base_key, values_from_dict=item)
                else:
                    dict_to_form_elements(self.st, item,use_columns=use_columns, use_expander=use_expander, base_key="")
                
                self.st.form_submit_button("Save")
                
        return self
"""