"""
This utility builds forms from a Pydantic model_json_schema() output.
"""

# TODO Create a schema parser, and output a schema that can be used to build forms.

from nicegui import ui
from typing import Any, List, Dict, Tuple, Union, Optional, Type
import re
from contextlib import contextmanager

from core import log, print
from core.utils.string import to_snake_case
from core.utils.frontend import ui_helper
from core.utils.database import Database

class FormBuilder:
    
    schema = None
    current_values = None
    required = []
    submit_callback = None
    submit_value = "Save"
    submit_kwargs: dict = {}
    
    # Temp 
    get_select_options_last_type = None
    get_select_options_last_format = None
    
    label_classes = 'w-60 col-12'
    input_classes = 'w-60 col-12 caret-slate-500 outlined'
    ui_container_kwargs = {}
    container_kwargs = {"value": True}
    form_container = None
    
    # Database refs
    _database_ref_items = {}

    def __init__(self, schema:dict, current_values:dict = {}, submit_callback: callable = None, **submit_kwargs ) -> None:
        self.schema = schema
        self.required = schema.get('required', [])
        self.current_values = current_values
        self.submit_value = "Save"
        self.submit_callback = submit_callback
        self.clear_on_submit = False
        self.ui_container = ui.row
        self.submit_kwargs = submit_kwargs
        self.container = ui.expansion
        print("FORM BUILDER SCHEMA", schema, "FORM BUILDER CURRENT VALUES", current_values)
        
    
    @contextmanager
    def yield_container(self, key:str, property:dict, right_side:callable = None, icon="list_alt"):
        """ Creates a container for the form element """
        title = key or property.get('title', None) 
        try:
            _container = self.container(to_snake_case(title),icon=icon, **self.container_kwargs)
        except:
            _container = self.container(icon=icon, **self.container_kwargs)
        
        # TODO fix outline/border not appearing!?
        with _container.props("bordered outlined").classes('full-width block border border-gray-200 outlined') as container:
            # label = ui.label(to_snake_case(title)).classes('text-xl')
            with ui.row().classes('full-width block'):
                if self.is_required(key, property): #key in self.required:
                    ui.label('* Required').classes('text-red-500')
                if 'description' in property: # TODO put this help text in a better place
                    ui.label(property['description']).classes('text-gray-500 text-caption')
                    # label.tooltip(property['description'])
                ui.space()
                if right_side:
                    right_side()
            
            ui.separator()    
            yield
            
            if property.get('hidden', False):
                container.set_visibility(False)
                
        return container
    
    def create_label(self, key:str, property:dict = {}):
        """ Creates the label for the form element """
        title = property.get('title', None) or key
        with ui.column().classes('full-width block'):
            label = ui.label(to_snake_case(title)).classes(self.label_classes)
            if self.is_required(key, property): #key in self.required:
                ui.label(' *').classes('text-red-500')
            if 'description' in property: # TODO put this help text in a better place
                ui.label(property['description']).classes('text-gray-500 text-caption')
                label.tooltip(property['description'])
        return 
    
    def get_current_value(self, key:str, property:dict = {}):
        """ Returns the value for the form element """
        _keys = key.split('.')
        default_value = property.get('default', None)
        values = self.current_values
        # print("[magenta]GET CURRENT VALUE: ", key, "default value=", default_value) 
        for i, k in enumerate(_keys):
            _index = k.split('[')[-1].split(']')[0] if '[' in k else None
            k = k.split('[')[0]
            # print("[bold magenta]GETTING", k, _index, values) 
            if values is not None and k in values:
                values = values.get(k, {})
            elif values is None:
                self.set_nested_item(_keys, self.current_values, default_value)  # Set the default value
                values = default_value
                break
            else: 
                log.debug(f"Key not found: {k} in {values}")
                self.set_nested_item(_keys, self.current_values, default_value)  # Set the default value
                values = default_value
                break

            if _index is not None and isinstance(values, list) and int(_index) < len(values):
                values = values[int(_index)]
            elif _index is not None and isinstance(values, list):
                log.debug(f"Index out of range {key} {_index}")
                self.set_nested_item(_keys[i:], self.current_values, default_value)  # Set the default value
                values = default_value
                break

        return values
    
    def set_nested_item(self, keys, current_values, value):
        log.debug(f"Setting Nested Item: {keys}: {value} in {len(current_values)}")
        key = keys.pop(0)
        if '[' in key:
            key, index = key[:-1].split('[')
            index = int(index)
            if len(keys) == 0:
                # We're at the end of the keys, set the value
                while len(current_values[key]) <= index:
                    # Extend the list if necessary
                    current_values[key].append(None)
                current_values[key][index] = value
            else:
                # We're not at the end of the keys, recurse
                while len(current_values[key]) <= index:
                    # Extend the list if necessary
                    current_values[key].append({})
                if current_values[key][index] is None:
                    current_values[key][index] = {}
                self.set_nested_item(keys, current_values[key][index], value)
        else:
            if len(keys) == 0:
                # We're at the end of the keys, set the value
                # print("SET VALUE", key, value, current_values)
                current_values[key] = value
            else:
                # We're not at the end of the keys, recurse
                if key not in current_values:
                    # Create a new dictionary if necessary
                    current_values[key] = {}
                self.set_nested_item(keys, current_values[key], value)
                
    def _remove(self, event:object, card:ui.card = None, container:object = None ):
        """
        Helper method to remove an item from an array.
        """
        # print(vars(event.sender))
        # print(vars(card))
        
        def remove_nested_item( keys, current_values):
            key = keys.pop(0)
            if '[' in key:
                key, index = key[:-1].split('[')
                index = int(index)
                if len(keys) == 0 and index <= len(current_values[key]):
                    # del current_values[key][index]
                    current_values[key][index] = None
                else:
                    remove_nested_item(keys, current_values[key][index])
            else:
                if len(keys) == 0 and index <= len(current_values[key]):
                    # del current_values[key]
                    current_values[key][index] = None
                else:
                    remove_nested_item(keys, current_values[key])
                    
        # print(event.sender._classes)
        _key = [x for x in event.sender._classes if x.startswith('_remove_key=')]
        if _key:
            _key = _key[0].split('=')[1]
            _keys = _key.split('.')
            
            remove_nested_item(_keys, self.current_values)
            
            # _card_ids = [x for x in event.sender._classes if x.startswith('_remove_id=')]
            if container and card:
                # card.clear()
                # _card_id = _card_ids[0].split('=')[1]
                # print("DETELETING", _card_id)
                container.remove(card)
                
                # card.remove(card)
            
            # print("CURRENT VALUES", self.current_values)

    def _update_key(self, key:str, value:str):
        """
        Update a key in the current_values dict.
        """
        key = key.split('.')
        # format: key1.key2[list index].key3
        # print("UPDATE KEY MANUAL", key, value)
        
        if len(key) > 0:
            
            # print("CURRENT VALUES", self.current_values)
            self.set_nested_item(key, self.current_values, value)
            print("UPDATED VALUES", self.current_values)
            
            return

    def _update_event(self, event:object):
        """ Returns the update function for the form element """
        # print("UPDATE", event)
        # print(event.sender.__dict__)
        # print(event.sender._classes)
        log.debug(f"UPDATE EVENT: {vars(event.sender)}")
        
        _key = [x for x in event.sender._classes if x.startswith('_input_key=')]
        try:
            _value = event.value
        except AttributeError:
            # no attribute 'value'
            try:
                # For JSON editor
                _value = event.content
                if isinstance(_value, dict) and 'json' in _value:
                    _value = _value.get('json', {})
            except Exception as e:
                # not sure what else to do
                log.error(e)
                return
            
        if _key:
            _key = _key[0].split('=')[1]
            _kk = _key.split('.')
            # format: key1.key2[list index].key3
            print("UPDATE KEY EVENT", _kk, _value)
            
            if len(_kk) > 0:
                
                # print("CURRENT VALUES", self.current_values)
                self.set_nested_item(_kk, self.current_values, _value)
                print("UPDATED VALUES", self.current_values)
                
                return
                
                
            #     _v = self.current_values
            #     for i, k in enumerate(_kk):
            #         _index = k.split('[')[-1].split(']')[0] if '[' in k else None
            #         k = k.split('[')[0]
            #         print("UPDATE", i, k, _index, _v)
                    
            #         if k in _v:
            #             # key exists already 
            #             # check if list value
            #             if (isinstance(_v, list) and [_index] is not None):
                            
            #                 # Check if index is in range. if not, append a new item
            #                 # Append the correct type of item.
            #                 # if its NOT the last key, then we can assume the value is a dict.
            #                 try:
            #                     if i == len(_kk)-1:
            #                         _v[int(_index)] = event.value
            #                     else:
            #                         _v = _v[int(_index)].get(k, {})
            #                 except:
            #                     if i == len(_kk)-1:
            #                         _v.append(event.value)
            #                     else:
            #                         _v.append({k: {}})
                            
            #             elif isinstance(_v, dict):
            #                 _v = _v.get(k, {})
            #             else:
            #                 _v = _v.get(k, {})
            #         else:
            #             # key does not exist
            #             print("KEY DOES NOT EXIST", k, _v)
            #             # check if list value
            #             if (isinstance(_v, list) and [_index] is not None):
            #                 # Check if index is in range
            #                 # if not, append a new item
            #                 # Append the correct type of item.
            #                 # if its NOT the last key, then we can assume the value is a dict.
            #                 try:
            #                     if i == len(_kk)-1:
            #                         _v[int(_index)] = event.value
            #                     else:
            #                         _v = _v[int(_index)].get(k, {})
            #                 except:
            #                     if i == len(_kk)-1:
            #                         _v.append(event.value)
            #                     else:
            #                         _v.append({k: {}})
            #             elif isinstance(_v, dict):
            #                 _v[k] = {}
            #             else:
            #                 _v[k] = {}
                            
                    
                    
            #         # # if i == 0:
            #         # #     _v = _v.get(k, {})
            #         # #     if _index and isinstance(_v, list):
            #         # #         if int(_index) < len(_v):
            #         # #             _v = _v[int(_index)]
            #         # #         else:
            #         # #             _v.append(event.value)
            #         # #     continue
            #         # if isinstance(_v, list) and _index is not None:
            #         #     # Check if index is in range
            #         #     if _index and int(_index) < len(_v):
            #         #         _v = _v[int(_index)].get(k, {})
            #         #     # else:
            #         #     #     log.debug(f"Index out of range {_key} {_index}")
            #         #     #     break
            #         # elif isinstance(_v, dict):
            #         #     _v = _v.get(k, {})
            #         # # else:
            #         #     # _v = _v.get(k, {})
                        
            #         # if _index:
            #         #     _v = _v[int(_index)].get(k, {})
            #         # else:
            #         #     _v = _v.get(k, {})
                        
            #     # update values
            #     # _v[_kk[-1]] = event.value
            #     self.current_values[_kk[0]] = _v
            # # else:
            # #     self.current_values.update({_kk[0]: event.value})
            # print(self.current_values[_kk[0]])

    def _input_classes(self, key:str = None):
        """ Returns the classes for the form element """
        if key:
            return self.input_classes + f' _input_key={key}'
        return self.input_classes
    
    def _get_example(self, property:dict, type:str = None):
        """ Returns the example value for the form element """
        example = property.get('default', None)
        if not example and 'example' in property:
            example = property.get('example', None)
        if example and type:
            if type in ['str','string']:
                example = example[0] if isinstance(example, list) else example
                example = str(example)
            if type in ['list','array']:
                example = example if isinstance(example, list) else [example]
            if type in ['int','integer']:
                example = int(example)
            if type in ['float','number']:
                example = float(example)
            if type in ['bool','boolean']:
                example = bool(example)
            if type in ['dict','object']:
                example = example if isinstance(example, dict) else {}
        return example
    
    def submit_form(self, event:object):
        """ 
        Submits the form to the provided callback function. Use this callback to merge the submitted data into the pydantic model.
        If there is an error, raise the exception which will be displayed on the frontend.
        
        Returns:
            dict: The current values of the form.
        
        """
        def _prepare_data_for_submission(d):
            _out = {}
            if isinstance(d, dict):
                return {k: _prepare_data_for_submission(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [_prepare_data_for_submission(v) for v in d if v is not None]
            else:
                # TODO Check for password fields and hash the fields if property.password_visible = False .
                return d
                # pass
            
        if self.submit_callback:
            try:
                self.current_values = _prepare_data_for_submission(self.current_values)
                log.debug("Saving Form" + str(self.current_values))
                print(self.current_values)
                res = self.submit_callback(self.current_values, **self.submit_kwargs)
                if res == True:
                    ui.notification('Form saved!', position='bottom', type='positive', icon='done', timeout=2, close_button=False)
                    # TODO clear form if required. - not clearing DB reference fields! 
                    if self.clear_on_submit:
                        self.current_values = {}
                        self.form_container.update()
                else:
                    raise Exception(str(res))
            except Exception as e:
                ui.notification('Error: '+str(e), position='bottom', type='negative', icon='error', timeout=30, close_button=True)
    
    def build(self, callback:callable = None):
        # Catch form submission
        
        # print("SCHEMA", self.schema )
        # print("CURRENT VALUES", self.current_values )
        # Start form
        self.build_main_form(callback=callback)
            
        # End form
        # Submit button
        self.submit_button()
    
    def build_main_form(self, skip_keys:List[str] = ['id','_id'], callback:callable = None):
        with self.ui_container(**self.ui_container_kwargs) as self.form_container:
            for key, property in self.schema['properties'].items():
                if key.startswith('_') or key in skip_keys: continue
                try:
                    key, property = callback(key, property) if callback else (key, property)
                except Exception as e:
                    log.error(e)
                
                if key and property:
                    self.create_form_element(key, property)
    
    def submit_button(self, value:str = None, classes="bg-positive text-white") -> ui.button:
        _v = value if value else self.submit_value
        if _v:
            return ui.button(_v, on_click=self.submit_form).classes(classes)
    
    def create_form_element(self, key:str, property:dict, format:str = None, value:Any = None):
        
        # Reset variables
        _require_db_query = False
        # print(key,property,format) if key == 'sample_model_list' else None
        
        # Determine value type
        # type, format, ref = self._determine_type(key, property)
        _key = key
        parent_key = key.split('.')[0]
        last_key = key.split('.')[-1]
        last_index = last_key.split('[')[-1].split(']')[0] if '[' in last_key else None
        last_key = last_key.split('[')[0]
        
        log.debug(f"Creating Form Element for: {key} {property}")
        
        element_type = property.get('type')
        label = property.get('title', to_snake_case(last_key))
        value = value if value else self.get_current_value(_key, property)
        
        if not element_type and value:
            # Try from value.
            element_type = type(value).__name__
            
        if not element_type and 'example' in property:
            # Try from example.
            element_type = type(property['example']).__name__
        
        if not element_type and 'default' in property:
            # Try from default.
            _p = property.get('default', None)
            element_type = type(_p).__name__ if _p else None
        
        if property.get('collection_name', None):
            element_type = "database_ref"
            
        # NOTE: anyOf = Optional, allOf = Required
        log.debug(f"Getting Select Options for {key}")
        options = self.get_select_options(last_key, property)
        
        self.create_element(_key, property, element_type=element_type, options=options, value=value, format=format)
        
    def create_element(self, key:str, property:dict, element_type:str = None, options:list = None, format:str = None, index:int=0, value:Any = None):
        """
        Creates a form element from a simple property and other parameters.
        for best effect, property dict should contain the following keys:
            type
            format
            title
            description
            
        """
        last_key = key.split('.')[-1]
        last_key = last_key.split('[')[0]
        label = property.get('title', to_snake_case(last_key))

        if not element_type and self.get_select_options_last_type:
            element_type = self.get_select_options_last_type
        
        # if 'sample_model_list' == key:
        #     print(key, element_type, value, options)

        element_type = str(element_type) if element_type else None
        element_type = "string" if element_type == "str" else element_type
        element_type = "integer" if element_type == "int" else element_type
        element_type = "number" if element_type == "float" else element_type
        element_type = "boolean" if element_type == "bool" else element_type
        element_type = "object" if element_type == "dict" else element_type
        element_type = "array" if element_type == "list" else element_type
        
        is_multiselect = True if element_type == 'array' and options else False
        is_hidden = True if property.get('hidden', False) else False
        
        # NOTE: If element_type == object/dict/database_object, then we need to create a subform
        # If no schema, nor value, nor example, then we can't do anything! 
        
        required = self.is_required(last_key, property) # not needed here, not used. DEBUG only
        _format = property.get('format', None) if not format else format
        
        if not format and self.get_select_options_last_format:
            format = self.get_select_options_last_format
        
        # if not element_type == 'object': return
        # if not element_type and not options:   property)
        element = None
        log.debug(f"... Creating Element for {key}: {element_type} value={value}")
        log.debug(f"Element Meta {key}: type={element_type} options={options} multiselect={is_multiselect} required={required} format={_format} hidden={is_hidden}")
        
        # TODO implement format
        if element_type == 'string' and not options:
            element = self._create_string_element(key, property, label, value, options, is_multiselect, last_key, _format)
        elif element_type == 'string' and options or \
            element_type == 'array' and options:
            element = self.create_ui(ui.select, key, property,
                multiple=is_multiselect, 
                options=options,
                clearable=self.is_clearable(last_key, property), 
                with_input=True,
                # new_value_mode='add', # TODO how can we implement this?
                value = value,
                props=['use-chips']
            )

        elif element_type == 'integer':
            element = self.create_ui(ui.number, key, property,
                step=property.get('multipleOf', 1),
                min=property.get('exclusiveMinimum', None),
                max=property.get('exclusiveMaximum', None),
                placeholder=self._get_example(property, element_type),
                value = value,
            )
        elif element_type == 'number':
            element = self.create_ui(ui.number, key, property,
                step=property.get('multipleOf', 0.1),
                precision=property.get('decimal_places', 2),
                min=property.get('exclusiveMinimum', None),
                max=property.get('exclusiveMaximum', None),
                placeholder=self._get_example(property, element_type),
                value = value,
            )
        elif element_type == 'boolean':
            element = self.create_ui(ui.switch, key, property,
                text=label,
                value = value,
            )
        elif element_type == 'object':
            # self.create_object(key, property)
            # print("[red]GET OBJECT PROPERTIES", key, property)
            log.debug(f"Creating Object Sub element with key: '{key}' {property}")
            match element_type:
                case 'object':
                    _icon = "account_tree"
                case 'database_ref':
                    _icon = "hub"
                case _:
                    _icon = "list_alt"
                    
            with self.yield_container(last_key, property, icon=_icon):
                
                sub_format = property.get('format', None)
                sub_schema = self.get_object_schema(last_key, property)
                
                log.debug(sub_format)
                log.debug(sub_schema)
                # log.debug(self.get_object_properties_last_format)
                # log.debug(self.get_object_properties_last_type)
                log.debug(self.get_current_value(key, property))
                # self.create_label(key, property)
                
                if sub_format == "json":
                    # If object is a json string
                    # self._create_string_element(key, property, 
                    #     label,
                    #     value = self._get_example(property, element_type),
                    #     format=sub_format
                    # )

                    self.create_ui(
                        key=key, 
                        property=property, 
                        show_label=False,
                        # props=['col-6','fit','full-width'],
                        classes='col-6 fit full-width block',
                        ui_element = ui.json_editor,
                        properties={'content': {'json': value}},
                    )
                    
                # If object is a pydantic basemodel
                elif sub_schema.get('properties', {}):
                    for child_key, sub_properties in sub_schema.get('properties', {}).items():
                        if child_key.startswith('_') or child_key in ['id','_id']: continue
                        # Indent the save dict with key
                        sub_key = f"{key}.{child_key}"
                        log.debug(f"Creating Object Sub element with key: {sub_key}")
                        self.create_form_element(sub_key, sub_properties, format=sub_format)
                
                # else if object is a dict
                elif any(x in property for x in ['example','default']):
                    # If we have an example, we can create an empty form with the example values
                    _schema = property.get('example', property.get('default', {}))
                    for child_key, value in _schema.items():
                        if child_key.startswith('_') or child_key in ['id','_id']: continue
                        # Indent the save dict with key
                        sub_key = f"{key}.{child_key}"
                        log.debug(f"Creating Object Sub element with key: {sub_key}")
                        sub_properties = {
                            'type': type(value).__name__,
                            'title': to_snake_case(child_key),
                            'description': None,
                            'format': None,
                        }
                        self.create_element(sub_key, sub_properties, format=sub_format, value=value)
                        # TODO implement this
                
                else:
                    ui_helper.alert_warning("No properties found.")
                    
                    
                    
        elif element_type == 'array' and not options:
            # Potentially an array of objects, from $defs
            # print("[red]GET ARRAY PROPERTIES", key, property)
            
            def _array_create_card(key, property, container):
                
                log.debug(f"Creating Array Sub element with key: '{key}' {property}")
                sub_schema = self.get_object_schema(last_key, property) 
                log.debug(f"Sub Format: {sub_format}")
                # log.debug(sub_schema)
                # log.debug(key)
                # log.debug(self.get_select_options(last_key, property))
                # log.debug(self.get_object_properties_last_format)
                # log.debug(self.get_object_properties_last_type)
                # log.debug(key)
                # log.debug(self.get_current_value(key, property))
                
                with ui.card().classes('full-width') as card:
                    with ui.column(): # TODO allow for customisation of this row/column/other
                        # if has properties (ie. is a pydantic object)
                        if sub_schema.get('properties', {}):
                            for child_key, sub_properties in sub_schema.get('properties', {}).items():
                                if child_key.startswith('_') or child_key in ['id','_id']: continue
                                # Indent the save dict with key
                                sub_key = f"{key}.{child_key}"
                                # print("CREATE CARD SUB KEY", sub_key, sub_properties)
                                self.create_form_element(sub_key, sub_properties, format=sub_format)

                        # else, if something else...
                        # What are our options? str, int, float, bool... ?
                        else:
                            if self.get_object_properties_last_type == 'string':
                                # print("CREATE CARD NO PROPERTIES", key, sub_schema, sub_format)
                                self._create_string_element(key, property, label, value, options, is_multiselect, last_key, self.get_object_properties_last_format)
                            else:
                                log.error("TODO - Implement other array types")
                                ui_helper.alert_warning("No properties found. " + str(self.get_object_properties_last_type))

                        ui.space()

                        ui.button(
                            icon="delete", 
                            on_click=lambda event, card=card: self._remove(event, card, container) 
                        ).classes('bg-negative text-white'
                        ).classes('_remove_key='+key)
                        
            def _array_add_card():
                values = self.get_current_value(key, property)
                if values == None: 
                    values = []
                    self.set_nested_item(key.split('.'), self.current_values, values)
                # print("ADD CARD VALUES", values)
                new_base_key = f"{key}[{len(values)}]"
                # print("ADD CARD", new_base_key, property)
                # self.set_nested_item(new_base_key.split('.'), self.current_values, self.get_current_value(key, property) )
                _array_create_card(new_base_key, property, container)
                # values.append(None)  # Add an empty value to the list # BUG Works for array of str, but not array of obj
                # self._update_key(key=key, value=self.get_current_value(key, property))
                # print("CURRENT VALUES", self.current_values)

            def _array_right_side():
                # ui.button(icon="add", on_click=lambda: container.clear ).classes('bg-positive text-white')
                ui.button(icon="add", on_click=_array_add_card).classes('bg-positive text-white')
                
            # container

            # self.create_label(last_key, property)
            values = self.get_current_value(key, property) # List of objects/values :+1:
            sub_format = property.get('format', None)
            sub_schema = self.get_object_schema(last_key, property)
            sub_type = sub_schema.get('type', None)
            
            log.debug(f"Array Sub Type|Schema: {sub_type} {sub_schema}")
            
            print("Author Array SUB TYPE: " + str(sub_type)) if last_key == 'authors' else None
            print(sub_schema)
            
            if not values: values = [] # TODO Add a button to add a new item
            
                
            if sub_type == 'database_ref' and sub_schema.get('collection_name', None):
            
                self.database_ref_element(key, sub_schema, values, element_type) # array 

            else: 
                
                with self.yield_container(last_key, property, right_side = _array_right_side ) as main_container:
                    
                    with ui.column().classes('full-width') as container:
                        
                        for i, value in enumerate(values):
                            
                            base_key = f"{key}[{i}]"
                            _array_create_card(base_key, property, container)
                    
                    
                            
            
        elif element_type == 'database_ref' and property.get('collection_name', None):
            
            print("DATABASE OBJECT", key, property, options)
                        
            values = self.get_current_value(key, property) # List of objects/values :+1:
            
            # self.create_label(last_key, property)
                
            self.database_ref_element(key, property, values, element_type) # database_ref 
            
        else:
            # print(f"[bold red]NO TYPE FOUND FOR {key}[/bold red]", element_type, label, value, options)
            print(f"create_form_element: [bold magenta]{key}", property.get('type'), f"[cyan]{element_type}", label, "[yellow]VALUE",str(value)[:20],"...", "[yellow]OPTIONS", str(options), "is_multiselect=", is_multiselect, "required=", required, "format=", _format)
            ui_helper.alert_danger(f"Form Element for '{key}' could not be rendered.")
        
        
        # Post processing
        if element:
            
            if property.get("hidden", False) or is_hidden:
                element.set_visibility(False)
            
            
        # Headers, dividers and notice boxes

    def database_ref_element(self, key:str, property:dict, values:List[Union[str,dict]], element_type:str):
        """
        Creates a database reference element.
        
        1. Creates fields for search/select, add, remove, and edit.
        2. Displayed card contains dict of ID, and display fields defined by the model (display_fields). If no fields, then first 3 except from id is displayed.
        3. Search field is a text field with a search button. On search, a list of results is displayed. Uses display_field (from model Settings) to show results.
        4. Add field is a button that opens a new card with the fields defined by the model.
        5. Remove field is a button that removes the card.
        6. Edit field is a button that opens a new card with the fields defined by the model. (Not urgent)
        
        """
        print("[red bold]DATABASE REF ELEMENT", key, property, values)
        
                
        def _database_ref_fetch(search:str = None):
            # Fetches items from DB if search is provided, or first 1000
            # TODO Add a rate limit!
            nonlocal display_fields
            
            _data = {}
            if key not in self._database_ref_items:
                self._database_ref_items[key] = {}
            print(f"self._database_ref_items.{key}....", self._database_ref_items[key])
            if self._database_ref_items[key]:
                if not display_fields:
                    _f = ["{"+k+"}" for k in self._database_ref_items[key][0].keys() if isinstance(self._database_ref_items[key][0], dict) and k not in ['_id','id','created_on','updated_on','created_by','updated_by']]
                    if _f: display_fields = " - ".join(_f[:2])
                if not display_fields:
                    raise Exception("No display fields found for database reference.")
                for d in self._database_ref_items[key].values():
                    if not d.get('_id'): continue
                    _display = display_fields.format(**{k: str(v) if v else "" for k, v in d.items() })
                    _data.update({d.get('_id'): _display})
                if _data:
                    return _data
            # TODO add cacheing and update list when searching.
            
            db = Database.get_collection(property.get('collection_name', None))
            if db:
                if search:
                    db_items = list(db.find(search))
                else:
                    db_items = list(db.find({}))
                if db_items:
                    log.warning('Getting new database reference items')
                    if not display_fields:
                        _f = ["{"+k+"}" for k in db_items[0].keys() if k not in ['_id','id','created_on','updated_on','created_by','updated_by']]
                        if _f: display_fields = " - ".join(_f[:2])
                    if not display_fields:
                        raise Exception("No display fields found for database reference.")
                    for d in db_items:
                        if not d.get('_id'): continue
                        _display = display_fields.format(**{k: str(v) if v else "" for k, v in d.items() })
                        _data.update({d.get('_id'): _display})
                        self._database_ref_items[key][d.get('_id')] = d
                # Sort alphabetically
                
            return _data
            
        # Search method for database_ref
        def _database_ref_search(event:object):
            with ui.row().classes("full-width"):
                
                db_items = _database_ref_fetch()
                print("#"*30, db_items)
                
                _search = ui.select(
                    # options = {
                    #     "1": "One",
                    #     "2": "Two",
                    #     "3": "Three",
                    # },
                    options = db_items,
                    # on_change=self._update_event, 
                    label = "Search",
                    value = None, # the initial value
                    with_input = True,
                    # new_value_mode = callable, # allows for new user inputs
                    multiple = None, #	whether to allow multiple selections
                    # clearable = None, #	whether to add a button to clear the selection
                    # validation = None, #	dictionary of validation rules or a callable that returns an optional error message
                    # key_generator = None, #	a callback or iterator to generate a dictionary key for new values
                ).classes(
                    self._input_classes(key)+''
                
                ).props(
                    # use-chips = True, #	whether to use chips for multiple selections
                )
                # TODO add a callback on letters typed to search the database
                # TODO If element_type != 'array', only allow ONE value in 'values'. 
                ui.button("Add", on_click=lambda: _database_ref_add_item( _search.value)).classes('bg-positive text-white')
            
                        
                                
        def _database_ref_add_item( _id:str):
            nonlocal display_fields, values
            print("ITEM ID"*30, _id)
            # _id = item.value
            if _id:
                print(key, self._database_ref_items )
                if not _id in self._database_ref_items[key]:
                    ui.notification(f"Item {_id} not found", position='bottom', type='negative', icon='error', timeout=2, close_button=True)
                    return
                # Add the item to the list
                ui.notification(f"Adding {_id}", position='bottom', type='positive', icon='done', timeout=2, close_button=True)
                values.append(self._database_ref_items[key][_id])
                _display = display_fields.format(**{k: str(v) if v else "" for k, v in self._database_ref_items[key][_id].items() })
                self.set_nested_item(key.split('.'), self.current_values, values) # TODO Model may only allow ONE item - validate!
                property.update({"disable":True}) # Disable editing of the field
                with ui.card().classes('full-width') as card:
                    with ui.column(): # TODO allow for customisation of this row/column/other
                        
                        self._create_string_element(key, property, value=_display)

                        ui.space()

                        ui.button(
                            icon="delete", 
                            on_click=lambda event, card=card: self._remove(event, card, container) 
                        ).classes('bg-negative text-white'
                        ).classes('_remove_key='+key)

                # If success
                # item.value = None
                
        def _database_ref_add_existing_item( _id:str):
            nonlocal display_fields, values
            # _id = item.value
            if _id:
                if not _id in self._database_ref_items[key]:
                    ui.notification(f"Item {_id} not found", position='bottom', type='negative', icon='error', timeout=2, close_button=True)
                    return
                # Add the item to the list
                _display = display_fields.format(**{k: str(v) if v else "" for k, v in self._database_ref_items[key][_id].items() })
                property.update({"disable":True}) # Disable editing of the field
                with ui.card().classes('full-width') as card:
                    with ui.column(): # TODO allow for customisation of this row/column/other
                        
                        self._create_string_element(key, property, value=_display)

                        ui.space()

                        ui.button(
                            icon="delete", 
                            on_click=lambda event, card=card: self._remove(event, card, container) 
                        ).classes('bg-negative text-white'
                        ).classes('_remove_key='+key)
   
        
        # Container add button
        def _database_ref_right_side():
            # ui.button(icon="add", on_click=_database_ref_add_card).classes('bg-positive text-white')
            # ui.button(icon="add", on_click=lambda: ui.notification("Adding new item")).classes('bg-positive text-white')
            # TODO add button is dependent on model option 'allow_new' - requires user permission too
            pass

        display_fields = property.get('display_field','') # Use curly brackets to place variables. eg. {name} - {description}
        last_key = key.split('.')[-1]
        last_key = last_key.split('[')[0]
        values = self.get_current_value(key, property) or []

        with self.yield_container(last_key, property, right_side = _database_ref_right_side ):
            
            ui.label("Datanase Ref: Search").classes('text-gray-500 text-caption')
            _database_ref_search(None)
            
            ui.label("Datanase Ref: Referenced Items").classes('text-gray-500 text-caption')
            
            with ui.column().classes('full-width') as container:

                # TODO if key is an array, then we need to iterate over the values, else if single value, then just one value and not array.
                log.warning(f"DATABASE REF VALUES: {key} {property}")
                for i, value in enumerate(values): 
                                
                    base_key = f"{key}[{i}]"
                    # _database_ref_add_item(base_key, property, container)
                    _database_ref_add_existing_item(value.get('_id', value.get('id', None)))
                    log.warning(f"DATABASE REF ITEM: {base_key} {value}")
                    print("ADDING EXISTING VALUE", i, base_key, value)
        
    def is_clearable(self, key:str, property:dict) -> bool:
        """
        If the field is required, then it is not clearable. Literaly returns the opposite of is_required()
        """
        return not self.is_required(key, property)
        
    def is_required(self, key:str, property:dict) -> bool:
        # Default to TRUE 
        _req = True
        if 'anyOf' in property:
            _req = False
        return _req
    
        # _req = key in self.required
        # if 'allOf' in property:
        #     return True
        # return _req
            
    def get_select_options(self, key:str, property:dict):
        self.get_select_options_last_format = None
        self.get_select_options_last_type = None
        # NOTE: anyOf = Optional, allOf = Required
        out = self._get_select_options(key, property)
        print("GET SELECT OPTIONS", key, self.get_select_options_last_type,self.get_select_options_last_format )
        return out
        
    def _get_select_options(self, key:str, property:dict):
        options = []        
        
        # check if there is anything else, type and format
        # Moved to top to prevent overwriting child values with parent value, since it is processed afterwards
        if 'format' in property:
            if property['format'] and property['format'] != "null" and not self.get_select_options_last_format:
                self.get_select_options_last_format = property['format']
        if 'type' in property:
            if property['type'] and property['type'] != "null" and not self.get_select_options_last_type:
                self.get_select_options_last_type = property['type']
                
        if isinstance(property, list):
            for _p in property:
                _options = self._get_select_options(key, _p)
                if _options:
                    options.extend(_options)
            return options
        
        if '$ref' in property:
            # Get the reference
            _ref = property['$ref'].split('/')[-1]
            ref = self.schema.get('$defs', {}).get(_ref, {})
            # print("REF", key, _ref, ref)
            _options = self._get_select_options(key, ref)
            if _options:
                options.extend(_options)
            # print(options)
                
        # Get Nested values
        if 'anyOf' in property:
            _options = self._get_select_options(key, property['anyOf'])
            if _options:
                options.extend(_options)
        if 'allOf' in property:
            _options = self._get_select_options(key, property['allOf'])
            if _options:
                options.extend(_options)
        if 'items' in property:
            _options = self._get_select_options(key, property['items'])
            if _options:
                options.extend(_options)
        
        # Check for enum or const
        if 'enum' in property:
            options.extend(property['enum'])
        if 'const' in property:
            options.extend(property['const'] if isinstance(property['const'], list) else [property['const']])
            
            
        return options

    def get_object_schema(self, key:str, property:dict):
        """
        Obtains the object properties from the $deps field, or dict field.
        If no JSON schema is found, then it will attempt to build a schema based on the values retrieved.
        
        Returns:
            dict: a dict of properties to run create_form_element() on.
        """
        self.get_object_properties_last_format = None
        self.get_object_properties_last_type = None
        # NOTE: anyOf = Optional, allOf = Required
        schema = self._get_object_properties(key, property)
        if not schema:
            # Build a schema from the values
            schema = {
                'properties': {},                
            }
            # if self.get_object_properties_last_type:
            #     schema['properties']['type'] = self.get_object_properties_last_type
            # if self.get_object_properties_last_format:
            #     schema['properties']['format'] = self.get_object_properties_last_format
                
        return schema

    def _get_object_properties(self, key:str, property:dict):
        options = {}
        
        # check if there is anything else, type and format
        # Moved to top to prevent overwriting child values with parent value, since it is processed afterwards
        if 'format' in property:
            if property['format'] and property['format'] != "null":
                self.get_object_properties_last_format = property['format']
        if 'type' in property:
            if property['type'] and property['type'] != "null":
                self.get_object_properties_last_type = property['type']
        
        if isinstance(property, list):
            for _p in property:
                _options = self._get_object_properties(key, _p)
                if _options:
                    # print("LIST", key, _options)
                    options.update(_options)
            return options
        
        if '$ref' in property:
            # Get the reference
            _ref = property['$ref'].split('/')[-1]
            ref = self.schema.get('$defs', {}).get(_ref, {})
            # print("REF", key, _ref, ref)
            _options = self._get_object_properties(key, ref)
            options = ref
            # if _options:
            #     options.extend(_options)
            # print(options)
                
        # Get Nested values
        if 'anyOf' in property:
            _options = self._get_object_properties(key, property['anyOf'])
            if _options:
                options.update(_options)
        if 'allOf' in property:
            _options = self._get_object_properties(key, property['allOf'])
            if _options:
                options.update(_options)
        if 'items' in property:
            _options = self._get_object_properties(key, property['items'])
            if _options:
                options.update(_options)
        
        # Check for enum or const
        # if 'enum' in property:
        #     options.extend(property['enum'])
        # if 'const' in property:
        #     options.extend(property['const'] if isinstance(property['const'], list) else [property['const']])
            
            
        return options
    
    def create_ui(self, ui_element:callable, key:str, property:dict, props:list = [], show_label:bool = True, **kwargs):
        
        with self.ui_container(**self.ui_container_kwargs).classes('full-width') as container:
            
            if show_label:
                self.create_label(key.split('.')[-1], property)
                
            _classes = kwargs.pop('classes', '')
            
            ui_element(
                # value=self.get_current_value(key,property),  # applied via kwargs
                on_change=self._update_event, 
                **kwargs
            ).classes(self._input_classes(key)+' '+_classes).props(' '.join([
                    'disable readonly' if property.get('disable', False) or property.get('readOnly',False) else '',
                    *props
                ]
            ))
        
        # Post processing
        if container:
            
            if property.get("hidden", False):
                container.set_visibility(False)
            
        return container

    def _create_string_element(self, key:str, property:dict, label:str = None, value:Any = None, options:List[str] = [], is_multiselect:bool = False, last_key:str = "", format:str = ""):
        # switch formats
        _val = value if value else self.get_current_value(key,property)
        log.debug(f"Creating String Element for {key} {property} with value: {_val}")
        _args = {
            "ui_element": ui.input,
            "placeholder": self._get_example(property, "string"),
            "value": _val if isinstance(_val, str) else None, # Get default value
        }
        _props = []
        
        if format == 'password' or 'writeOnly' in property:
            _args['password'] = True
            _args['password_toggle_button'] = property.get('password_visible', False) 
        elif format == 'email':
            _args['validation'] = lambda value:re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", value) is not None 
        elif format == 'color':
            _args['ui_element'] = ui.color_input # ui.color_picker
            _args['preview'] = True
        elif format == 'link':
            _args['ui_element'] = ui.link
            _args['target'] = value
            _args['text'] = value
            _args['new_tab'] = property.get('new_tab',True)
        elif format == 'cron':
            pass # TODO, implement CRON input field
        elif format == "json":
            _args['ui_element'] = ui.json_editor
            _args['properties'] = {'content': {'json': value}}
            _args.pop('value', None)
            _args.pop('placeholder', None)
        elif format == 'markdown':
            _args['ui_element'] = ui.markdown
            _args['content'] = value # TODO Drop VALUE param in create_ui()
        elif format == 'mermaid':
            _args['ui_element'] = ui.mermaid
            _args['content'] = value # TODO Drop VALUE param in create_ui()
        elif format == 'html':
            _args['ui_element'] = ui.html
            _args['content'] = value  # TODO Drop VALUE param in create_ui()
            
        elif format == 'textarea':
            _args['ui_element'] = ui.textarea
            
        elif format == 'chat_message':
            _args['ui_element'] = ui.chat_message
            _args['text'] = value  # TODO Drop VALUE param in create_ui()
            # _args['text'] = property.get('text', None)
            _args['name'] = property.get('name', None)
            _args['label'] = property.get('label', None)
            _args['stamp'] = property.get('stamp', None)
            _args['avatar'] = property.get('avatar', None)
            _args['sent'] = property.get('sent', False)
            _args['text_html'] = property.get('text_html', False)
        elif format == 'date':
            # _args['ui_element'] = ui.date
            # _args['mask'] = property.get('mask', "YYYY-MM-DD")
            _props = ['type=date']
            _args.pop('placeholder', None)
        elif format == 'time':
            # _args['ui_element'] = ui.time
            # _args['mask'] = property.get('mask', "HH:mm")
            _props = ['type=time']
            _args.pop('placeholder', None)
        elif format == 'date-time':
            # Should have ui.date and ui.time ?
            # _args['ui_element'] = ui.datetime
            _props = ['type=datetime=local']
            # ui.label()
            pass
        else:
            log.debug(f"Unknown format '{format}' for {last_key}")
            
        return self.create_ui(
            key=key, 
            property=property, 
            props=_props,
            **_args
        )
        

"""
example schema:


{
    '$defs': {
        'Color': {'enum': ['red', 'green', 'blue'], 'title': 'Color', 'type': 'string'},
        'Model': {
            'properties': {
                'sample': {'default': 'a sample', 'title': 'Sample', 'type': 'string'},
                'sample2': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'default': None, 'title': 'Sample2'}
            },
            'title': 'Model',
            'type': 'object'
        }
    },
    'properties': {
        'MODULE_NAME': {'default': 'test', 'title': 'Module Name', 'type': 'string'},
        'MODULE_VERSION': {'default': 0.1, 'title': 'Module Version', 'type': 'number'},
        'MODULE_VERSION_INT': {'default': 1, 'title': 'Module Version Int', 'type': 'integer'},
        'MODULE_DESCRIPTION': {'default': 'Test Module', 'title': 'Module Description', 'type': 'string'},
        'MODULE_AUTHOR': {'default': 'Test Author', 'title': 'Module Author', 'type': 'string'},
        'MODULE_AUTHOR_EMAIL': {
            'default': 'john@gmail.com',
            'description': 'The email address of the module author.',
            'example': 'email@example.com',
            'format': 'email',
            'maxLength': 254,
            'minLength': 3,
            'title': 'Module Author Email',
            'type': 'string'
        },
        'MY_DICT': {'default': {}, 'description': 'A dictionary field', 'title': 'My Dict', 'type': 'object'},
        'schedule2': {'default': '*/11 * * * *', 'description': 'Cron schedule for the module', 'example': '*/15 * * * *', 'format': 'cron', 'title': 'Schedule2', 'type': 'string'},
        'multiple_colors': {
            'default': ['red', 'green'],
            'description': 'A list of colors',
            'example': ['red', 'green'],
            'items': {'$ref': '#/$defs/Color'},
            'title': 'Multiple Colors',
            'type': 'array'
        },
        'one_color': {'allOf': [{'$ref': '#/$defs/Color'}], 'default': 'red', 'description': 'One color', 'example': 'red'},
        'one_color2': {'anyOf': [{'$ref': '#/$defs/Color'}, {'type': 'null'}], 'default': 'red', 'description': 'One color', 'example': 'red'},
        'one_color3': {'allOf': [{'$ref': '#/$defs/Color'}], 'default': 'red', 'description': 'One color', 'example': 'red'},
        'literal_color': {'default': 'green', 'description': 'One color', 'enum': ['red', 'green', 'blue'], 'example': 'red', 'title': 'Literal Color', 'type': 'string'},
        'sample_model': {'anyOf': [{'$ref': '#/$defs/Model'}, {'type': 'null'}], 'default': {'sample': 'a sample', 'sample2': None}, 'description': 'A sample model'},
        'password': {'anyOf': [{'format': 'password', 'type': 'string', 'writeOnly': True}, {'type': 'null'}], 'description': 'A secret password', 'title': 'Password'}
    },
    'required': ['password'],
    'title': 'Test',
    'type': 'object'
}

"""