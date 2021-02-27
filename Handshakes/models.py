from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Text

Base = declarative_base()

class FriendsList(Base):
    __tablename__ = 'friends_list'
    id = Column(Integer, autoincrement=True, primary_key=True)
    user = Column(String, unique=True, nullable=False)
    from_end = Column(Boolean, unique=False, nullable=False)
    chain = Column(Text, unique=True, nullable=False)


