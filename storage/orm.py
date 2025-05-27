from sqlmodel import SQLModel, Field, create_engine, Relationship
from config import get_settings
from datetime import datetime

settings = get_settings()
engine = create_engine(settings.database_uri)


class BaseORM(SQLModel):
    id: str = Field(..., primary_key=True)
    created_at:  datetime = Field(default_factory=datetime.now)


class AnnotationORM(BaseORM, table=True):
    __tablename__ = 'annotations'
    image_id: str = Field(..., foreign_key='images.id', ondelete='CASCADE')
    category_id: str = Field(..., foreign_key='images.id', ondelete='CASCADE')
    x: float
    y: float
    height: float
    width: float

    image: 'ImageORM' = Relationship(back_populates='annotations')
    category: 'CategoryORM' = Relationship(back_populates='annotations')


class DemoORM(BaseORM, table=True):
    __tablename__ = 'demo'
    url: str


class ImageORM(BaseORM, table=True):
    __tablename__ = 'images'
    project_id: str = Field(..., foreign_key='projects.id', ondelete='CASCADE')
    url: str
    filename: str
    width: float
    height: float

    annotations: list[AnnotationORM] = Relationship(back_populates='image', cascade_delete=True)


class CategoryORM(BaseORM, table=True):
    __tablename__ = 'categories'
    project_id: str = Field(..., foreign_key='projects.id', ondelete='CASCADE')
    name: str
    color: str

    annotations: list[AnnotationORM] = Relationship(back_populates='category', cascade_delete=True)


class ProjectORM(BaseORM, table=True):
    __tablename__ = 'projects'
    name: str = Field(..., unique=True)
    user_id: str = Field(..., foreign_key='users.id', ondelete='CASCADE')

    categories: list[CategoryORM] = Relationship(back_populates='project', cascade_delete=True)
    images: list[ImageORM] = Relationship(back_populates='project', cascade_delete=True)


class UserORM(BaseORM, table=True):
    __tablename__ = 'users'
    username: str = Field(..., unique=True)
    password: str

    projects: list[ProjectORM] = Relationship(back_populates='user', cascade_delete=True)
