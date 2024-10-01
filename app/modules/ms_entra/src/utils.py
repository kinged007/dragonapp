
import requests
from loguru import logger as log

def server_request(endpoint, method="GET", data={}, headers={}, params={}, api_key=None, host=None):
    
    try:
        # print("SERVER REQUEST", endpoint, method, data, headers, params, api_key, host)
        
        endpoint = endpoint
        if host: 
            host = host.strip("/")
            endpoint = f"{host}/{endpoint.strip('/')}"
            
        method = method.upper()
        
        if not headers: headers = {}
        
        if api_key:
            headers.update({
                "Authorization": f"Bearer {api_key}"
            })
        
        if method == "GET":
            res = requests.get(endpoint, headers=headers, params=params)
        elif method == "POST":
            res = requests.post(endpoint, headers=headers, json=data, params=params)
        elif method == "PUT":
            res = requests.put(endpoint, headers=headers, json=data, params=params)
        elif method == "DELETE":
            res = requests.delete(endpoint, headers=headers, json=data, params=params)
        elif method == "PATCH":
            res = requests.patch(endpoint, headers=headers, json=data, params=params)
        else:
            raise Exception("Invalid method")
        return res
    
    except Exception as e:
        log.error(e)
    
    return None


 
    
def dict_diff(d1:dict, d2:dict):
    """
    Produces a dictionary of differences between two dictionaries, with d1 being the source of truth. The returned dictionary will contain the elements where d2 do not match d1.
    Args:
        d1 (dict): The source dictionary
        d2 (dict): The dictionary to compare with
    Returns:
        dict: { d1key: value: Any }
    """
    diff = {}
    for k in d1.keys():
        if k in [
            'id', 
            'appId', 
            'createdDateTime', 
            'deletedDateTime',
            'keyId',
            'endDateTime',
            'startDateTime',
            'createdDateTime',
            'secretText',
            'hint',
            
        ] or k.startswith('@odata'):
            continue
        
        if k not in d2:
            diff[k] = d1[k]
        elif isinstance(d1[k], dict):
            _diff = dict_diff(d1[k], d2[k])
            if _diff: diff[k] = _diff
        elif isinstance(d1[k], list):
            if d1[k] != d2[k]:
                _diff = []
                for i, _d in enumerate(d1[k]):
                    try:
                        if isinstance(_d, dict):
                            _diff.append(dict_diff(_d, d2[k][i]))
                        else:
                            if _d != d2[k][i]:
                                _diff.append(_d)
                    except IndexError:
                        # print(f"IndexError: {k}::{i}")
                        _diff.append(_d)
                        continue
                if _diff: diff[k] = _diff
        elif d1[k] != d2[k]:
            diff[k] = {'source': d1[k], 'result': d2[k] }
    # for k in d2.keys(): # We ignore keys that are not in d1
    #     if k not in d1:
    #         diff[k] = ("key not in d1", d2[k])
    return diff