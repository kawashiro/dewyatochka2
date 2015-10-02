# -*- coding: UTF-8

""" Local SQLIte storage

Classes
=======
    Storage       -- Storage with cool stories
    Tag           -- Story tag object
    TagMeta       -- Tags metaclass
    Post          -- Story post
    PostMeta      -- Posts metaclass
    Source        -- Story source
    SourceMeta    -- Sources metadata
"""

import random

from sqlalchemy import Column, Table, Integer, String, UniqueConstraint, Index, Text, ForeignKey, desc
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from dewyatochka.core.data.database import *

__all__ = ['Storage', 'Post', 'Tag', 'Source', 'PostMeta', 'TagMeta', 'SourceMeta']


class Storage(SQLIteStorage):
    """ Storage with cool stories """

    # Default path to db file
    _DEFAULT_DB_PATH = '/var/lib/dewyatochka/cool_story.db'

    def __init__(self):
        """ Init sqlite storage """
        super().__init__()
        self.__tags_cache_warmed = False

    @readable_query
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

    @writable_query
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
        if commit:
            self.db_session.commit()

        return post

    @readable_query
    def get_random_post_by(self, *expressions):
        """ Get random post by filters expression(s)

        :param tuple expressions: SQL expressions
        :return Post:
        """
        posts_ids_query = self.db_session.query(Post.id).filter(*expressions)

        try:
            posts_ids, = zip(*posts_ids_query.all())
        except ValueError:
            raise RuntimeError('No posts found')

        return self.db_session.query(Post).filter(Post.id == random.choice(posts_ids)).first()

    def get_random_post_by_source(self, source: str):
        """ Get random post by source title

        :param str source: Source title
        :return Post:
        """
        return self.get_random_post_by(Post.source == self.get_source_by_title(source))

    def get_random_post_by_tag(self, tag_title: str):
        """ Get random post by tag title

        :param str tag_title: Tag title
        :return Post:
        """
        return self.get_random_post_by(Post.tags.contains(self.get_tag_by_title(tag_title)))

    @readable_query
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

    @property
    @readable_query
    def tags(self) -> dict:
        """ Get all tags dict

        :return dict:
        """
        if not self.__tags_cache_warmed:
            self.db_session.query(Tag).all()
            self.__tags_cache_warmed = True
        return Tag.get_cached()


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
