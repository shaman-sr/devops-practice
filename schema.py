from pydantic import BaseModel

class Hero(BaseModel):
    name: str
    secret_name: str
    age: int | None
    