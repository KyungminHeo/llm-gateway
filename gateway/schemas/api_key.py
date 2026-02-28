from pydantic import BaseModel
from datetime import datetime

class ApiKeyCreate(BaseModel):
    name: str

class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key: str
    is_active: bool
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }
