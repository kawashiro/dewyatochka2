# -*- coding: UTF-8

""" zadolba.li local sqlite storage

Classes
=======
    Storage -- Storage with cool stories
    Tag     -- Story tag object
    Post    -- zadolba.li post
"""

__all__ = ['Storage', 'Post', 'Tag']

import os
import random

from sqlalchemy import create_engine, Column, Table, Integer, String, UniqueConstraint, Text, ForeignKey, desc
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.orm.exc import NoResultFound

from dewyatochka.core.utils.data import ObjectMeta, StorageMeta


class Storage(metaclass=StorageMeta):
    """ Storage with cool stories """

    # Default path to db file
    _DEFAULT_DB_PATH = '/var/lib/dewyatochka/zadolba_li.db'

    def __init__(self, file=None):
        """ Init sqlite storage

        :param str file:
        """
        self.__file = os.path.realpath(file)
        self.__db_session = None
        self.__last_post = None

    @property
    def db_session(self) -> Session:
        """ Get DB session

        :return Session:
        """
        if self.__db_session is None:
            self.__db_session = sessionmaker(
                bind=create_engine('sqlite:///%s' % (self.__file or self._DEFAULT_DB_PATH))
            )()

        return self.__db_session

    @property
    def path(self) -> str:
        """ Get path to db

        :return str:
        """
        return self.__file

    def recreate(self):
        """ Recreate engine

        :return None:
        """
        self.db_session.close()

        if os.path.isfile(self.path):
            os.unlink(self.path)

        # noinspection PyUnresolvedReferences
        self.__class__.metadata.create_all(bind=self.db_session.get_bind())

    def add_post(self, ext_id: int, title: str, text: str, tags=frozenset(), commit=True):
        """ Add a single story and return inserted post instance

        :param int ext_id: Story site ID
        :param str title: Story title
        :param str text:  Story full text
        :param set tags: Story tags set / frozenset
        :param bool commit: Commit changes or not
        :return Post:
        """
        post_tags = []
        for tag_title in tags:
            tag = Tag(title=tag_title)
            if not tag.stored:
                try:
                    tag = self.db_session.query(Tag).filter(Tag.title == tag_title).one()
                except NoResultFound:
                    # Okay, using not stored instance
                    pass
            # Increment counter as new link story + tag has been created
            tag.count += 1
            post_tags.append(tag)

        # Save story with tags
        post = Post(ext_id=ext_id, title=title, text=text, tags=post_tags)
        self.db_session.add(post)
        self.__last_post = post
        if commit:
            self.db_session.commit()

        return post

    @property
    def last_post(self):
        """ Get last post. Raise runtime error is storage is empty

        :return Post:
        """
        if self.__last_post is None:
            try:
                self.__last_post = self.db_session.query(Post).order_by(desc(Post.id)).first()
            except NoResultFound:
                raise RuntimeError('Storage is empty')

        return self.__last_post

    @property
    def random_post(self):
        """ Get random post

        :return Post:
        """
        post_id = random.randrange(0, self.last_post.id)
        return self.last_post if post_id == self.last_post.id \
            else self.db_session.query(Post).filter(Post.id > post_id).first()

    def __enter__(self):
        """ __enter__()

        :return Storage:
        """
        return self

    def __exit__(self, *_) -> bool:
        """ Close session on exit

        :param tuple _:
        :return bool:
        """
        self.db_session.close()
        return False


class TagMeta(ObjectMeta):
    """ Tags metaclass """

    @property
    def _table(cls) -> Table:
        """ Get table associated with metadata

        :param cls:
        :return Table:
        """
        return Table('tags', Storage.metadata,
                     Column('id', Integer, primary_key=True),
                     Column('title', String(255), index=True),
                     Column('count', Integer, nullable=False, default=0, index=True),
                     UniqueConstraint('title'))


class Tag(metaclass=TagMeta):
    """ tag object """

    # Cached tags by title
    _tags_cache = {}

    # noinspection PyShadowingBuiltins
    def __init__(self, id=None, title=None, count=0):
        """ Init object

        :param int id:
        :param str title:
        :param int count:
        """
        if title is not None and title not in self._tags_cache:
            # Do not re-init object if it is a cached instance
            self.id, self.title, self.count = id, title, count
            self._tags_cache[title] = self

    @property
    def stored(self) -> bool:
        """ Is flag stored in db

        :return bool:
        """
        return self.id is not None

    # noinspection PyShadowingBuiltins
    def __new__(cls, id=None, title=None, count=0):
        """ Get cached tag instance instead of creating a new one

        :param int id:
        :param str title:
        :param int count:
        """
        if title is not None and title in cls._tags_cache:
            return cls._tags_cache[title]

        return super().__new__(cls)


class PostMeta(ObjectMeta):
    """ Posts metaclass """

    @property
    def _table(cls) -> Table:
        """ Get table associated with metadata

        :param cls:
        :return Table:
        """
        return Table('posts', Storage.metadata,
                     Column('id', Integer, primary_key=True),
                     Column('ext_id', Integer),
                     Column('title', String(255)),
                     Column('text', Text))

    @staticmethod
    def get_assoc_table() -> Table:
        """ Get posts 2 tags association table

        :return Table:
        """
        return Table('posts_tags', Storage.metadata,
                     Column('post_id', Integer, ForeignKey('posts.id')),
                     Column('tag_id', Integer, ForeignKey('tags.id')))

    @property
    def _mapping_properties(cls) -> dict:
        """ Get object mapping properties

        :return dict:
        """
        return {'tags': relationship(Tag, secondary=cls.get_assoc_table(), backref='posts')}


class Post(metaclass=PostMeta):
    """ zadolba.li post """

    # noinspection PyShadowingBuiltins
    def __init__(self, id=None, ext_id=None, title=None, text=None, tags=None):
        """ Init object

        :param int id:
        :param int ext_id:
        :param str title:
        :param str text:
        :param list tags:
        """
        self.id, self.ext_id, self.title, self.text, self.tags = id, ext_id, title, text, tags or []
