""" Persistent counter to keep track of data across requests """

import tiktoken
encoding = tiktoken.get_encoding("cl100k_base") # gpt-4, gpt-3.5-turbo, text-embedding-ada-002

from core.schemas.singleton import SingletonMeta

class Count(metaclass=SingletonMeta):

    def __init__(self):
        self.count = 0
        self.data = {'tags': {}}

    def increment(self, key=None, value=1, tag=None, silent_count = True): # Silent count ignores the count for the tag
        if not key:
            self.count += value
        else: 
            new_key = f"{key}:{tag}" if tag else key
            if new_key not in self.data:
                self.data[new_key] = 0
            self.data[new_key] += value
            if tag and not silent_count: 
                if tag not in self.data['tags']: 
                    self.data['tags'][tag] = 0
                self.data['tags'][tag] += 1

    def get_count(self, key=None, tag=None):
        if not key and not tag:
            return self.count
        elif not key and tag:
            return self.data['tags'][tag] if tag in self.data['tags'] else 0
        else:
            new_key = f"{key}:{tag}" if tag else key
            if new_key not in self.data:
                return 0
            return self.data[new_key]
    
    def get_data(self, tag=None):
        if tag:
            return {k:v for k,v in self.data.items() if tag in k}
        return self.data
    
    def reset(self):
        self.count = 0
        self.data = {'tags': {}}
        
    def __str__(self):
        return f"Counter(count={self.count}, data={self.data})"
    
    def tokens(self, text: str):
        # Tokenize the text using the tokenizer
        return len(encoding.encode(text))

        
    