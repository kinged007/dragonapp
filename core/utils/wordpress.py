from typing import Union, List
import requests
from requests.auth import HTTPBasicAuth
from models.utils import strip_html_tags

class Wordpress:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.auth = HTTPBasicAuth(username, password)

    def authenticate(self):
        # This method is just a placeholder to indicate where authentication would be handled.
        # Actual authentication will occur with each request using the HTTPBasicAuth.
        pass

    def get_posts(self, search:str = None):
        _params = {"search": search} if search else {}
        response = requests.get(f"{self.base_url}/wp-json/wp/v2/posts", auth=self.auth, params=_params)
        return response.json()
    
    def get_post(self, post_id:str = None):
        response = requests.get(f"{self.base_url}/wp-json/wp/v2/posts/{post_id}", auth=self.auth)
        return response.json()

    def _create_post(self, data):
        response = requests.post(f"{self.base_url}/wp-json/wp/v2/posts", auth=self.auth, json=data)
        return response.json()
    
    def _update_post(self, post_id, data):
        response = requests.post(f"{self.base_url}/wp-json/wp/v2/posts/{post_id}", auth=self.auth, json=data)
        return response.json()

    def get_categories(self):
        response = requests.get(f"{self.base_url}/wp-json/wp/v2/categories", auth=self.auth, params={"_fields": "id,slug,name"})
        return response.json()

    def create_category(self, data):
        response = requests.post(f"{self.base_url}/wp-json/wp/v2/categories", auth=self.auth, json=data)
        return response.json()

    def get_tags(self):
        response = requests.get(f"{self.base_url}/wp-json/wp/v2/tags", auth=self.auth, params={"_fields": "id,slug,name"})
        return response.json()

    def create_tag(self, data):
        response = requests.post(f"{self.base_url}/wp-json/wp/v2/tags", auth=self.auth, json=data)
        return response.json()

    def get_media(self):
        response = requests.get(f"{self.base_url}/wp-json/wp/v2/media", auth=self.auth)
        return response.json()

    def upload_media(self, file, data):
        headers = {'Content-Disposition': f"attachment; filename={file.name}"}
        response = requests.post(f"{self.base_url}/wp-json/wp/v2/media", auth=self.auth, headers=headers, files={'file': file}, data=data)
        return response.json()

    # def get_users(self):
    #     response = requests.get(f"{self.base_url}/wp-json/wp/v2/users", auth=self.auth)
    #     return response.json()

    # def create_user(self, data):
    #     response = requests.post(f"{self.base_url}/wp-json/wp/v2/users", auth=self.auth, json=data)
    #     return response.json()
    
    def _find_in_list_of_dicts(self, list_of_dicts, key, value):
        return [d for d in list_of_dicts if d.get(key) == value]
    
    def _wp_ensure_tag_or_cat_exists(self, items, type ):
        
        final_items = []
        
        if type not in ['categories', 'tags']: raise Exception("Invalid type")
        
        if items:
            wp_items = self.get_categories() if type =='categories' else self.get_tags()
            # wp_categories = {cat.get('id'):cat.get('slug') for cat in wp_categories}
            for cat in items:
                new_item = {}
                if isinstance(cat, int):
                    if len(self._find_in_list_of_dicts(wp_items, 'id', cat)) > 0: 
                        final_items.append(cat)
                    continue # Cant add new categories from just an ID
                if isinstance(cat, str):
                    match = self._find_in_list_of_dicts(wp_items, 'slug', cat)
                    if not match: match = self._find_in_list_of_dicts(wp_items, 'name', cat)
                    if len(match) > 0: 
                        final_items.append(match[0].get('id'))
                        continue
                    new_item = {
                        "name": cat,
                    }
                if isinstance(cat, dict):
                    match = self._find_in_list_of_dicts(wp_items, 'id', cat.get('id'))
                    if not match: match = self._find_in_list_of_dicts(wp_items, 'slug', cat.get('slug'))
                    if not match: match = self._find_in_list_of_dicts(wp_items, 'name', cat.get('name'))
                    if len(match) > 0:
                        final_items.append(match[0].get('id'))
                        continue
                    new_item = {
                        "name": cat.get('name', None),
                        "slug": cat.get('slug', None),
                        "description": cat.get('description', None),
                    }
                # Category not found, create it
                new_item["parent"] = 0 
                add_new_item = self.create_category(new_item) if type == 'categories' else self.create_tag(new_item)
                if add_new_item and add_new_item.get('id', None):
                    final_items.append(add_new_item.get('id'))
                    wp_items.append(add_new_item)
                    continue
                    
        return final_items


    def prepare_categories(self, categories: List[Union[int, str, dict]] = None):
        """
        Asserts category ID's and they exist in wordpress.
        """
        return self._wp_ensure_tag_or_cat_exists(categories, 'categories')
        
    def prepare_tags(self, tags: List[Union[int, str, dict]] = None):
        """
        Asserts tag ID's and they exist in wordpress.
        """
        return self._wp_ensure_tag_or_cat_exists(tags, 'tags')
        
    def update_post( self,
        post_id: int,
        title: str = None,
        content: str= None,
        author: int = None,
        # status: str = None, # dont change status. it should be published already
        categories: List[Union[int, str, dict]] = None, # Accepts category ID's or slugs
        tags: List[Union[int, str]] = None, # Accepts tag ID's or slugs
        featured_media: int = None,  # Accepts media ID or dict with media details
        excerpt: str = None,
        slug:str = None,
        format:str = None,
    ):
        """
        Updates a post if it exists.
        """
        # from rich import print
        
        if not post_id: raise Exception("Post ID is required")
        
        # Get the original post
        original_post = self.get_post(post_id)
        
        if original_post and original_post.get('id', None):
            
            if categories and not isinstance(categories[0], int):
                # Get category ID's from slugs
                categories = self.prepare_categories(categories)
                
            if tags and not isinstance(tags[0], int):
                # Get tag ID's from slugs
                tags = self.prepare_tags(tags)

            # print(original_post)
            print("Original Post: " + str(original_post.get('id')))

            # Compare
            to_update = {}
            
            for key in ['title', 'content', 'author', 'categories', 'tags', 'featured_media', 'excerpt', 'slug', 'format']:
                if locals().get(key):
                    _source_post = strip_html_tags(locals().get(key).strip()) if isinstance(locals().get(key), str) else locals().get(key)
                    if isinstance(original_post.get(key), dict):
                        _published_post = strip_html_tags(original_post.get(key).get('rendered', '').strip())
                    elif isinstance(original_post.get(key), str):
                        _published_post = strip_html_tags(original_post.get(key).strip())
                    else:
                        _published_post = original_post.get(key)
                    # print(_source_post, " <> ", _published_post)
                    if _published_post != _source_post:
                        print("\n\n[red]NOT MATCHING[/red]", key, "(length)" , len(_published_post), " <> ", len(_source_post)  )
                        print('[yellow]'+str(_published_post))
                        print('[blue]' + str(_source_post))
                        to_update[key] = locals().get(key)
                        
                    # original_post[key] = locals().get(key)
            if to_update:
                print("Changes Found - Updating post")
                # print(to_update)
                published_post = self._update_post(post_id, to_update)
                # print(published_post)
                return published_post
            else:
                print("No changes found")
                return original_post
        
        raise Exception(f"Post '{post_id}' not found")
        # return {"error": f"Post '{post_id}' not found"}


    def publish_post( self,
        title: str,
        content: str,
        author: int = None,
        status: str = "draft",
        categories: list = Union[int, str], # Accepts category ID's or slugs, assumes correct ID's
        tags: list = Union[int, str], # Accepts tag ID's or slugs, assumes correct ID's
        featured_media: int = None,  # Accepts media ID or dict with media details, assumes correct ID
        excerpt: str = None,
        slug:str = None,
        format:str = "standard",
    ):
        
        if not title or not content: raise Exception("Title and Content are required")

        if not slug: slug = title.lower().replace(" ","-")
        if not status: status = "draft"

        if categories and not isinstance(categories[0], int):
            # Get category ID's from slugs
            categories = self.prepare_categories(categories)
            
        if tags and not isinstance(tags[0], int):
            # Get tag ID's from slugs
            tags = self.prepare_tags(tags)
        
        # Convert content to wordpress blocks
        # content = html_to_wordpress_blocks(content)
        
        # Publish post
        publish_post = {
            "title": title,
            "slug": slug,
            "content": content,
            "status": status,
            "categories": categories,
            "tags": tags,
            "featured_media": featured_media,
            "excerpt": excerpt,
            "author": author,
            "format": format,
        }
        
        # if Successful, increment publish_count
        published_post = self._create_post(publish_post)
        
        return published_post
    
    