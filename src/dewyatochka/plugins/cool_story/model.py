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

    def __get_entity_by_title(self, entity_cls, title: str):
        """ Get cacheable entity instance by title

        :param TagMeta|SourceMeta entity_cls:
        :param str title:
        :return Tag:
        """
        entity = entity_cls(title=title)
        if not entity.stored:
            try:
                entity = self.db_session.query(entity_cls).filter(entity_cls.title == title).one()
            except NoResultFound:
                # Okay, using not stored instance
                pass
        return entity

    def get_tag_by_title(self, title: str):
        """ Get tag instance by title

        :param str title: Tag title
        :return Tag:
        """
        return self.__get_entity_by_title(Tag, title)

    def get_source_by_title(self, title: str):
        """ Get source instance by title

        :param str title: Source title
        :return Tag:
        """
        return self.__get_entity_by_title(Source, title)

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
            tag = self.get_tag_by_title(tag_title)
            # Increment counter as new link story + tag has been created
            tag.count += 1
            post_tags.append(tag)

        source = self.get_source_by_title(source_title)

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

    def get_random_post(self, source=None):
        """ Get random post

        :param str source: Source title
        :return Post:
        """
        if source:
            max_ext_id = self.get_last_indexed_post(source).ext_id
            if not max_ext_id:
                raise RuntimeError('No stories found for source %s' % source)
            filters = [Post.ext_id > random.randrange(0, max_ext_id),
                       Post.source == self.get_source_by_title(source)]
            order_by = Post.ext_id
        else:
            filters = [Post.id > random.randrange(0, self.last_post.id)]
            order_by = Post.id

        post = self.db_session.query(Post).filter(*filters).order_by(order_by).first()
        if not post:
            raise RuntimeError('Failed to get random post by filters %s' % filters)

        return post

    def get_last_indexed_post(self, source):
        """ Get the last post indexed (highest external id)

        :param str source: Source title
        :return:
        """
        post = self.db_session \
            .query(Post) \
            .filter(Post.source == self.get_source_by_title(source)) \
            .order_by(desc(Post.ext_id)) \
            .first()

        return post or Post()


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
