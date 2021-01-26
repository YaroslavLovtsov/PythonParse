from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table

Base = declarative_base()

tag_post = Table(
    "tag_post",
    Base.metadata,
    Column('post_id', Integer, ForeignKey('post.id')),
    Column('tag_id', Integer, ForeignKey('tag.id'))
)

comment_post = Table(
    "comment_post",
    Base.metadata,
    Column('post_id', Integer, ForeignKey('post.id')),
    Column('comment_id', Integer, ForeignKey('comment.id'))
)

class Post(Base):
    __tablename__ = 'post'
    id = Column(Integer, autoincrement=True, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, unique=False, nullable=False)
    picture = Column(String, unique=False, nullable=True)
    author_id = Column(Integer, ForeignKey('writer.id'))
    publishing_date = Column(DateTime, unique=False, nullable=False)
    author = relationship("Writer")
    tags = relationship('Tag', secondary=tag_post)
    comments = relationship('Comment', secondary=comment_post)

class Comment(Base):
    __tablename__ = 'comment'
    id = Column(Integer, autoincrement=True, primary_key=True)
    internal_id = Column(Integer, unique=True, nullable=False)
    author_id = Column(Integer, ForeignKey('writer.id'))
    author = relationship("Writer")
    comment_text = Column(String, unique=False, nullable=True)

class Writer(Base):
    __tablename__ = 'writer'
    id = Column(Integer, autoincrement=True, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    name = Column(String, unique=False)
    posts = relationship("Post")


class Tag(Base):
    __tablename__ = 'tag'
    id = Column(Integer, autoincrement=True, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    posts = relationship("Post", secondary=tag_post)