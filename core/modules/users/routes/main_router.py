from fastapi import APIRouter

from core import Module

router = APIRouter()

@router.get("/test")
async def test():
    
    config = Module.by_name(__name__)
    # config = Config.module("users")
    print(config)
    # if config.get('is_active', False) == False:
    #     return {"message": "Module is not active"}
    
    return {"message": "Hello World"}