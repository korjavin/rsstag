import logging
from typing import Optional, List
from pymongo import MongoClient, CursorType, DESCENDING, UpdateMany

class RssTagPosts:
    indexes = ['owner', 'category_id', 'feed_id', 'read', 'tags', 'pid']
    def __init__(self, db: MongoClient) -> None:
        self._db: MongoClient  = db
        self._log = logging.getLogger('posts')

    def prepare(self) -> None:
        for index in self.indexes:
            try:
                self._db.posts.create_index(index)
            except Exception as e:
                self._log.warning('Can`t create index %s. May be already exists. Info: %s', index, e)

    def get_by_category(self, owner: str, only_unread: Optional[bool]=None, category: str='', projection: dict= {}) -> Optional[list]:
        query = {'owner': owner}
        if category:
            query['category_id'] = category
        try:
            if only_unread is not None:
                query['read'] = not only_unread
                sort = [('feed_id', DESCENDING), ('unix_date', DESCENDING)]
            else:
                sort = [('unix_date', DESCENDING)]
            if projection:
                cursor = self._db.posts.find(query, projection=projection).sort(sort)
            else:
                cursor = self._db.posts.find(query).sort(sort)
            result = list(cursor)
        except Exception as e:
            self._log.error('Can`t get posts by category %s, user %s. Info: %s', category, owner, e)
            result = None

        return result

    def get_all(self, owner: str, only_unread: Optional[bool]=None, projection: dict={}) -> Optional[list]:
        query = {'owner': owner}
        try:
            if only_unread is not None:
                query['read'] = not only_unread
            if projection:
                cursor = self._db.posts.find(query, projection=projection)
            else:
                cursor = self._db.posts.find(query)
            result = list(cursor)
        except Exception as e:
            self._log.error('Can`t get posts for user %s. Info: %s', owner, e)
            result = None

        return result

    def get_grouped_stat(self, owner: str, only_unread: Optional[bool]=None) -> Optional[list]:
        query = {'owner': owner}
        if only_unread is not None:
            query['read'] = not only_unread
        try:
            grouped = self._db.posts.aggregate([
                {'$match': query},
                {'$group': {'_id': '$feed_id', 'category_id': {'$first': '$category_id'}, 'count': {'$sum': 1}}}
            ])
            result = list(grouped)
        except Exception as e:
            self._log.error('Can`t get gtouped stat for user %s. Info: %s', owner, e)
            result = None

        return result

    def get_by_tags(self, owner: str, tags: list, only_unread: Optional[bool]=None, projection: dict={}) -> Optional[list]:
        """
        TODO: may be need change condition from 'tags': {'$all': tags} to 'tags': {'$elemMAtch': {'$in': tags}}
        """
        query = {
            'owner': owner,
            'tags': {'$all': tags}
        }
        if only_unread is not None:
            query['read'] = not only_unread
        sort_data = [('feed_id', DESCENDING), ('unix_date', DESCENDING)]
        try:
            if projection:
                cursor = self._db.posts.find(query, projection=projection).sort(sort_data)
            else:
                cursor = self._db.posts.find(query).sort(sort_data)
            result = list(cursor)
        except Exception as e:
            self._log.error('Can`t get posts by tags %s. User %s. Info: %s', tags, owner, e)
            result = None

        return result

    def get_by_bi_grams(self, owner: str, tags: list, only_unread: Optional[bool]=None, projection: dict={}) -> Optional[list]:
        query = {
            'owner': owner,
            'bi_grams': {'$all': tags}
        }
        if only_unread is not None:
            query['read'] = not only_unread
        sort_data = [('feed_id', DESCENDING), ('unix_date', DESCENDING)]
        try:
            if projection:
                cursor = self._db.posts.find(query, projection=projection).sort(sort_data)
            else:
                cursor = self._db.posts.find(query).sort(sort_data)
            result = list(cursor)
        except Exception as e:
            self._log.error('Can`t get posts by tags %s. User %s. Info: %s', tags, owner, e)
            result = None

        return result

    def get_by_feed_id(self, owner: str, feed_id: str, only_unread: Optional[bool]=None, projection: dict= {}) -> Optional[list]:
        query = {
            'owner': owner,
            'feed_id': feed_id
        }
        try:
            if only_unread is not None:
                query['read'] = not only_unread
                sort = [('feed_id', DESCENDING), ('unix_date', DESCENDING)]
            else:
                sort = [('unix_date', DESCENDING)]
            if projection:
                cursor = self._db.posts.find(query, projection=projection).sort(sort)
            else:
                cursor = self._db.posts.find(query).sort(sort)
            result = list(cursor)
        except Exception as e:
            self._log.error('Can`t get posts by category %s, user %s. Info: %s', feed_id, owner, e)
            result = None

        return result

    def get_by_pid(self, owner: str, pid: int, projection: dict={}) -> Optional[dict]:
        query = {
            'owner': owner,
            'pid': pid
        }
        try:
            if projection:
                post = self._db.posts.find_one(query, projection=projection)
            else:
                post = self._db.posts.find_one(query)
            if post:
                result = post
            else:
                result = {}
        except Exception as e:
            self._log.error('Can`t get post by pid %s. User %s. Info: %s', pid, owner, e)
            result = None

        return result


    def get_by_pids(self, owner: str, pids: list, projection: dict = {}) -> Optional[list]:
        query = {
            'owner': owner,
            'pid': {'$in': pids}
        }
        try:
            if projection:
                cursor = self._db.posts.find(query, projection=projection)
            else:
                cursor = self._db.posts.find(query)
            result = list(cursor)
        except Exception as e:
            self._log.error('Can`t get post by pid %s. User %s. Info: %s', pids, owner, e)
            result = None

        return result

    def change_status(self, owner: str, pids: list, readed: bool) -> Optional[bool]:
        query = {
            'owner': owner,
            'pid': {'$in': pids}
        }
        try:
            update_result = self._db.posts.update_many(query, {'$set': {'read': readed}})
            result = (update_result.matched_count > 0)
        except Exception as e:
            self._log.error('Can`t set read status for posts. User %s. Info: %s', owner, e)
            result = None

        return result

    def get_stat(self, owner: str) -> Optional[dict]:
        query = {'$match': {'owner': owner}}
        try:
            result = {'unread': 0, 'read': 0, 'tags': 0}
            cursor = self._db.posts.aggregate([
                query,
                {'$group': {'_id': '$read', 'counter': {'$sum': 1}}}
            ])
            for dt in cursor:
                if dt['_id']:
                    result['read'] = dt['counter']
                else:
                    result['unread'] = dt['counter']
            result["tags"] = self._db.tags.count_documents({'owner': owner})
        except Exception as e:
            self._log.error('Can`t get posts stat. User %s. Info: %s', owner, e)
            result = None

        return result

    def set_clusters(self, owner: str, similars: dict) -> Optional[bool]:
        result = False
        updates = [
            UpdateMany(
                {'owner': owner, 'pid': {'$in': list(ids)}},
                {'$addToSet': {'clusters': cluster}}
            )
            for cluster, ids in similars.items()
        ]

        if updates:
            try:
                self._db.posts.bulk_write(updates)
                result = True
            except Exception as e:
                self._log.error('Can`t set posts clusters. User %s. Info: %s', owner, e)
                result = None

        return result

    def get_by_clusters(self, owner: str, clusters: list, only_unread: Optional[bool]=None, projection: dict={}) -> Optional[list]:
        query = {
            'owner': owner,
            'clusters': {'$exists': True, '$elemMatch': {'$in': clusters}}
        }
        if only_unread is not None:
            query['read'] = not only_unread
        sort_data = [('feed_id', DESCENDING), ('unix_date', DESCENDING)]
        try:
            if projection:
                cursor = self._db.posts.find(query, projection=projection).sort(sort_data)
            else:
                cursor = self._db.posts.find(query).sort(sort_data)
            result = list(cursor)
        except Exception as e:
            self._log.error('Can`t get posts by clusters %s. User %s. Info: %s', clusters, owner, e)
            result = None

        return result

    def get_clusters(self, posts: List[dict]) -> set:
        result = set()
        field = 'clusters'
        for post in posts:
            if (field in post) and post[field]:
                result.update(post[field])

        return result

    def count(self, owner: str) -> Optional[int]:
        try:
            return self._db.posts.count_documents({'owner': owner})
        except Exception as e:
            self._log.error('Can`t count posts. User %s. Info: %s', owner, e)
            return None
