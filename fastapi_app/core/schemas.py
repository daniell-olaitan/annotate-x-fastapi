from pydantic import BaseModel


class UserSchema(BaseModel):
    username: str
    password: str

    model_config = {'extra': 'forbid'}


class OutputJSON(BaseModel):
    status: str = 'success'
    data: dict | list = {}


class CategorySchema(BaseModel):
    id: str
    name: str
    color: str


class AnnotationSchema(BaseModel):
    x: float
    y: float
    height: float
    width: float
    id: str
    category: CategorySchema
