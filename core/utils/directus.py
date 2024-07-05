"""
Base functions to interact with Directus instance.

    @dep directus url and token

"""
import requests
from os import getenv
from core import log

class Directus():
    
    url = ""
    token = ""
    
    def __init__(self):
        
        self.url = getenv("DIRECTUS_URL", "")
        self.token = getenv("DIRECTUS_ACCESS_TOKEN", "")
        if not self.url and not self.token:
            log.error("Directus URL or Access Token not set.")
        # print(self.url, self.token[:10])
        

    def directus_request(self, endpoint: str, method: str = "GET", data: dict = None, params: dict = None) -> requests.Response:
        """
        Make a request to the Directus API.
        """
        if not self.url or not self.token:
            raise Exception("Directus URL or Access Token not set.")
        
        url = f"{self.url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "User-Agent": "CS-API/1.2",
            "Content-Type": "application/json",
        }
        if method == "GET":
            req = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            req = requests.post(url, headers=headers, params=params, json=data)
        elif method == "PATCH":
            req = requests.patch(url, headers=headers, params=params, json=data)
        elif method == "DELETE":
            req = requests.delete(url, headers=headers, params=params )
        else:
            raise Exception(f"Invalid method {method}")
        return req
    
    def get(self, endpoint: str, data: dict = None, params: dict = None) -> requests.Response:
        return self.directus_request(endpoint, method="GET", data=data, params=params)
    
    def post(self, endpoint: str, data: dict = None, params: dict = None) -> requests.Response:
        return self.directus_request(endpoint, method="POST", data=data, params=params)
    
    def patch(self, endpoint: str, data: dict = None, params: dict = None) -> requests.Response:
        return self.directus_request(endpoint, method="PATCH", data=data, params=params)
    
    def delete(self, endpoint: str, data: dict = None, params: dict = None) -> requests.Response:
        return self.directus_request(endpoint, method="DELETE", data=data, params=params)
    
    def comment(self, comment: str, collection: str, item: str) -> requests.Response:
        return self.directus_request(f"activity/comment", method="POST", data={
            "comment": comment,
            "item": item,
            "collection": collection,
        })

    @classmethod
    def user_name(cls, item_data:dict, first_name=True, last_name=True):
        """
        Return a user's name from a Directus item.
        """
        user_obj = None
        if item_data.get("first_name", None):
            # Dealing with user object
            user_obj = item_data
        elif item_data.get("data", None):
            # User object is nested
            if item_data.get("first_name", None):
                user_obj = item_data.get("data")
            elif item_data.get('data',{}).get("directus_users_id", {}).get('first_name', None):
                user_obj = item_data.get('data').get("directus_users_id")
                
        elif item_data.get("directus_users_id", None) and item_data.get("directus_users_id", {}).get("first_name", None):
            # User object is nested
            user_obj = item_data.get("directus_users_id")
        
        if user_obj:
            _fn = user_obj.get("first_name", "") if first_name else ""
            _ln = user_obj.get("last_name", "") if last_name else ""
            _fn = "" if _fn.lower() == "none" else _fn
            _ln = "" if _ln.lower() == "none" else _ln
            
            return f"{_fn} {_ln}".strip()

        return ""

    def asset_url(self, asset_id:str, include_filename:bool=True):
        """
        Return a URL for an asset.
        """
        if asset_id:
            if include_filename:
                asset = self.get(f"files/{asset_id}").json()
                if asset.get("data", None):
                    asset = asset.get("data")
                    return f"{self.url}/assets/{asset_id}/{asset.get('filename_download', '')}"
            return f"{self.url}/assets/{asset_id}"
        return ""
