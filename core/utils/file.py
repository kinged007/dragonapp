import os

# TODO - Implement file storage provider

# os.environ['FILE_STORAGE_PROVIDER']
# os.environ['FILE_STORAGE_PROVIDER_KEY']
# os.environ['FILE_STORAGE_PROVIDER_SECRET']
# os.environ['FILE_STORAGE_PROVIDER_BUCKET']
# os.environ['FILE_STORAGE_PROVIDER_REGION']
# os.environ['FILE_STORAGE_PROVIDER_ENDPOINT']

os.makedirs(os.path.join("data", os.environ['FILE_STORAGE_PROVIDER_BUCKET']), exist_ok=True)

async def find_file(name:str, bucket:str = ''):
    
    # Get settings of where files are being hosted
    location = os.environ['FILE_STORAGE_PROVIDER']

    # Check if file exists in bucket
    if location == 'local':
        # Check if file exists in local directory
        path = os.path.join("data", bucket, name)
        if os.path.exists(path):
            return path
        
    # If file exists, return file path
    
    pass

    
async def save_file(name:str, data:str, bucket:str = '', overwrite:bool = False):
    
    # Get settings of where files are being hosted
    location = os.environ['FILE_STORAGE_PROVIDER']
 
    # Check if file exists in bucket
    if location == 'local':
        # Check if file exists in local directory
        path = os.path.join("data", bucket, name)
        if os.path.exists(path) and not overwrite:
            return False
        else:
            with open(path, "w") as f:
                f.write(data)
        
            # return true on success
            return True
    
    return False