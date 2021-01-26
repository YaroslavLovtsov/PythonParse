
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models
from urllib.parse import urljoin

class Database:
    def __init__(self, db_url):
        engine = create_engine(db_url)
        models.Base.metadata.create_all(bind=engine)
        self.maker = sessionmaker(bind=engine)

    def get_or_create(self, session, model, check_field, **data):
        if check_field == 'internal_id':
            db_data = session.query(model).filter(model.internal_id == data[check_field]).first()
        else:
            db_data = session.query(model).filter(model.url == data[check_field]).first()

        if not db_data:
            db_data = model(**data)
        return db_data

    def prepare_comment(self, session, **data):
        user_data = data['user']
        comment_author_data = {
            'url': urljoin('https://geekbrains.ru/users/', str(user_data['id'])),
            'name': user_data['full_name']
        }
        comment_writer = self.get_or_create(session, models.Writer, "url", **comment_author_data)
        comment_data = {
            'internal_id': data['id'],
            'author': comment_writer,
            'comment_text': data['html']
        }
        return self.get_or_create(session, models.Comment, "internal_id", **comment_data)

    def create_post(self, data):
        session = self.maker()
        tags = map(
            lambda tag_data: self.get_or_create(session, models.Tag, "url", **tag_data), data["tags"]
        )

        comments = map(lambda comment_data: self.prepare_comment(session, **comment_data), data["comments"])

        writer = self.get_or_create(session, models.Writer, "url", **data["author"])
        post = self.get_or_create(session, models.Post, "url", **data["post_data"], author=writer)
        post.tags.extend(tags)
        post.comments.extend(comments)

        session.add(post)

        try:
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()


