from models.base_model import BaseModel

class Location(BaseModel):
    """Represents a location in the application"""
    name = ""
    address = ""
    loc_id = ""
    def __init__(self, *args, **kwargs):
        """Initialize a location"""
        super().__init__(*args, **kwargs)
