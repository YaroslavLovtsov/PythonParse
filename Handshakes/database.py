from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models


class Database:
    def __init__(self, db_url):
        engine = create_engine(db_url)
        models.Base.metadata.create_all(bind=engine)
        self.maker = sessionmaker(bind=engine)

    def get_user_data(self, user_name):
        session = self.maker()
        return session.query(models.FriendsList).filter(models.FriendsList.user == user_name).first()

    def create_user_data(self, data):
        session = self.maker()

        db_data = models.FriendsList(**data)
        session.add(db_data)

        try:
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
