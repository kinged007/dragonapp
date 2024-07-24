

def merge_dicts(d1, d2):
    for key in d2:
        if key in d1 and isinstance(d1[key], dict) and isinstance(d2[key], dict):
            merge_dicts(d1[key], d2[key])
        else:
            d1[key] = d2[key]
            
            
def filter_dict(data, filter_substrings, exclude=True):
    if isinstance(filter_substrings, str):
        filter_substrings = [filter_substrings]

    new_dict = {}
    for key, value in data.items():
        if any(substring in key for substring in filter_substrings):
            match = True
        else:
            match = False
            
            
        if (exclude and not match) or (not exclude and match):
            if isinstance(value, dict):
                new_dict[key] = filter_dict(value, filter_substrings, exclude)
            else:
                new_dict[key] = value
        elif not exclude and isinstance(value, dict):
            new_dict[key] = filter_dict(value, filter_substrings, exclude)
            
    return new_dict

def dict_walk(data, func, *args, **kwargs):
    for key, value in data.items():
        if isinstance(value, dict):
            dict_walk(value, func, *args, **kwargs)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    dict_walk(item, func, *args, **kwargs)
                else:
                    value[i] = func(i, item, *args, **kwargs)
        else:
            data[key] = func(key, value, *args, **kwargs)
    return data