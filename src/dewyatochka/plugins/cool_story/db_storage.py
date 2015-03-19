# -*- coding: UTF-8

""" Local SQLIte storage

Classes
=======
    Storage -- Storage with cool stories
    Tag     -- Story tag object
    Post    -- Story post
"""

__all__ = ['Storage', 'Post', 'Tag']

import random

from sqlalchemy import Column, Table, Integer, String, UniqueConstraint, Index, Text, ForeignKey, desc
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from dewyatochka.core.data.database import ObjectMeta, StoreableObject, CacheableObject, SQLIteStorage


class Storage(SQLIteStorage):
    """ Storage with cool stories """

    # Default path to db file
    __DEFAULT_DB_PATH = '/var/lib/dewyatochka/cool_story.db'

    def __init__(self, file=None):
        """ Init sqlite storage

        :param str file:
        """
        super().__init__(file or self.__DEFAULT_DB_PATH)
        self.__last_post = None

    def add_post(self, source_title, ext_id: int, title: str, text: str, tags=frozenset(), commit=True):
        """ Add a single story and return inserted post instance

        :param str source_title: Story site name
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

        source = Source(title=source_title)
        if not source.stored:
            try:
                source = self.db_session.query(Source).filter(Source.title == source_title).one()
            except NoResultFound:
                pass

        # Save story with tags
        post = Post(source=source, ext_id=ext_id, title=title, text=text, tags=post_tags)
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


class Tag(CacheableObject, metaclass=TagMeta):
    """ tag object """

    # Unique key (field name)
    _key = 'title'

    # noinspection PyShadowingBuiltins
    def __init__(self, id=None, title=None, count=0):
        """ Init object

        :param int id:
        :param str title:
        :param int count:
        """
        super().__init__(id=id, title=title, count=count)


class SourceMeta(ObjectMeta):
    """ Sources metadata """

    @property
    def _table(cls) -> Table:
        """ Get table associated with metadata

        :param cls:
        :return Table:
        """
        return Table('sources', Storage.metadata,
                     Column('id', Integer, primary_key=True),
                     Column('title', String(255), index=True),
                     UniqueConstraint('title'))


class Source(CacheableObject, metaclass=SourceMeta):
    """ Story source """

    # Unique key (field name)
    _key = 'title'

    # noinspection PyShadowingBuiltins
    def __init__(self, id=None, title=None):
        """ Init object

        :param int id:
        :param str title:
        """
        super().__init__(id=id, title=title)


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
                     Column('source_id', Integer, ForeignKey('sources.id')),
                     Column('ext_id', Integer),
                     Column('title', String(255)),
                     Column('text', Text),
                     Index('ix_ext_id', 'source_id', 'ext_id', unique=True))

    @staticmethod
    def get_tags_assoc_table() -> Table:
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
        return {'tags': relationship(Tag, secondary=cls.get_tags_assoc_table()),
                'source': relationship(Source)}


class Post(StoreableObject, metaclass=PostMeta):
    """ Story post """

    # noinspection PyShadowingBuiltins
    def __init__(self, id=None, source=None, ext_id=None, title=None, text=None, tags=None):
        """ Init object

        :param int id:
        :param Source source:
        :param int ext_id:
        :param str title:
        :param str text:
        :param list tags:
        """
        super().__init__(
            id=id,
            source=source,
            ext_id=ext_id,
            title=title,
            text=text,
            tags=tags or []
        )
