from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta

class ServicePrincipalModel(BaseModel):
    appId: str = None # read-only
    displayName: str = None

    def post_model(self):
        # Create new app
        return self.model_dump(exclude=['id','appId','applicationTemplateId','createdDateTime','deletedDateTime','publisherDomain','uniqueName'],exclude_unset=True,  exclude_none=True)
