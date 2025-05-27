from pydantic import BaseModel


class UserSchema(BaseModel):
    username: str
    password: str

    model_config = {'extra': 'forbid'}


class OutputJSON(BaseModel):
    status: str = 'success'
    data: dict = {}
