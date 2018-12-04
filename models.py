#!/usr/bin/env python3
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250))
    picture = Column(String(250))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return{
            'name': self.name,
            'id': self.id,
            'email': self.email,
            'picture': self.picture,
        }


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
           'name': self.name,
           'id': self.id,
           'user_id': self.user_id,
        }


class CatalogItem(Base):
    __tablename__ = 'catalog_item'

    title = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
           'title': self.title,
           'description': self.description,
           'id': self.id,
           'user_id': self.user_id,
           'category_id': self.category_id,
        }


class CatalogItemImg(Base):
    __tablename__ = 'image'

    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    uuid_prefix = Column(String(40))
    user_id = Column(Integer, ForeignKey('user.id'))
    catalogItem_id = Column(Integer, ForeignKey('catalog_item.id'))
    user = relationship(User)
    catalogItem = relationship(CatalogItem)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'uuid_prefix': self.uuid_prefix,
            'user_id': self.user_id,
            'catalogItem_id': self.catalogItem_id,
        }


engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)
