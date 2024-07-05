import jwt, os
from pydantic import BaseModel
from typing import Optional
from utils.datetime import datetime, timedelta
from core import log
from enum import Enum
from utils.datetime import utc_now

class JWTAlgorithm(Enum):
    ES384: str = "ES384"
    ES256: str = "ES256"
    ES256K: str = "ES256K"
    HS256: str = "HS256"
    HS384: str = "HS384"
    HS512: str = "HS512"
    RS256: str = "RS256"
    RS384: str = "RS384"
    RS512: str = "RS512"
    EdDSA: str = "EdDSA"

class JWT(BaseModel):
    
    secret_key: str = None
    algo: str = 'HS256'
    default_expires: timedelta = timedelta(minutes=15)
    
    def __init__(self, secret_key=None, algo:JWTAlgorithm =None, default_expire: timedelta = None):
        super().__init__()
        if not secret_key: 
            self.secret_key = os.environ['SECRET_KEY']
        else: self.secret_key = secret_key
        if algo: self.algo = algo
        if default_expire: self.default_expires = default_expire
    
    def create(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = utc_now() + expires_delta
        else:
            expire = utc_now() + self.default_expires
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algo)
        return encoded_jwt

    def verify(self, token):
        try:
            decoded_jwt = jwt.decode(token, self.secret_key, algorithms=[self.algo])
            return decoded_jwt
        except jwt.ExpiredSignatureError:
            raise Exception('Signature has expired')
        except jwt.InvalidTokenError:
            raise Exception('Invalid token')