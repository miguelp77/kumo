# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import current_app
from google.cloud import datastore


builtin_list = list


def init_app(app):
    pass


def get_client():
    return datastore.Client(current_app.config['PROJECT_ID'])


def from_datastore(entity):
    """Translates Datastore results into the format expected by the
    application.

    Datastore typically returns:
        [Entity{key: (kind, id), prop: val, ...}]

    This returns:
        {id: id, prop: val, ...}
    """
    if not entity:
        return None
    if isinstance(entity, builtin_list):
        entity = entity.pop()

    entity['id'] = entity.key.id
    return entity


# def list(limit=10, cursor=None):
#     ds = get_client()
#     query = ds.query(kind='Book', order=['title'])
#     it = query.fetch(limit=limit, start_cursor=cursor)
#     entities, more_results, cursor = it.next_page()
#     entities = builtin_list(map(from_datastore, entities))
#     return entities, cursor.decode('utf-8') if len(entities) == limit else None

# def list(limit=10, kind='Book', cursor=None):
#     ds = get_client()
#     query = ds.query(kind=kind, order=['title'])
#     it = query.fetch(limit=limit, start_cursor=cursor)
#     entities, more_results, cursor = it.next_page()
#     entities = builtin_list(map(from_datastore, entities))
#     return entities, cursor.decode('utf-8') if len(entities) == limit else None
#
#
# def list_by_user(user_id, kind='Book', limit=10, cursor=None):
#     ds = get_client()
#     query = ds.query(
#         kind=kind,
#         filters=[
#             ('createdById', '=', user_id)
#         ]
#     )
#     it = query.fetch(limit=limit, start_cursor=cursor)
#     entities, more_results, cursor = it.next_page()
#     entities = builtin_list(map(from_datastore, entities))
#     return entities, cursor.decode('utf-8') if len(entities) == limit else None

def list(limit=10,  kind='Audio',cursor=None):
    ds = get_client()

    query = ds.query(kind='Audio', order=['title'])
    query_iterator = query.fetch(limit=limit, start_cursor=cursor)
    page = next(query_iterator.pages)

    entities = builtin_list(map(from_datastore, page))
    next_cursor = (
        query_iterator.next_page_token.decode('utf-8')
        if query_iterator.next_page_token else None)

    return entities, next_cursor

def list_by_user(user_id,  kind='Audio',limit=10, cursor=None):
    ds = get_client()
    query = ds.query(
        kind='Audio',
        filters=[
            ('createdById', '=', user_id)
        ]
    )
    # it = query.fetch(limit=limit, start_cursor=cursor)
    # entities, more_results, cursor = it.next_page()
    # entities = builtin_list(map(from_datastore, entities))
    # return entities, cursor.decode('utf-8') if len(entities) == limit else None
    query_iterator = query.fetch(limit=limit, start_cursor=cursor)
    page = next(query_iterator.pages)

    entities = builtin_list(map(from_datastore, page))
    next_cursor = (
        query_iterator.next_page_token.decode('utf-8')
        if query_iterator.next_page_token else None)

    return entities, next_cursor

def read(id):
    ds = get_client()
    key = ds.key('Book', int(id))
    results = ds.get(key)
    print(from_datastore(results))
    return from_datastore(results)

def read_audio(id):
    ds = get_client()
    key = ds.key('Audio', int(id))
    results = ds.get(key)
    print(from_datastore(results))
    return from_datastore(results)


def update(data, kind='Book', id=None):
    ds = get_client()
    if id:
        key = ds.key(kind, int(id))
    else:
        key = ds.key(kind)

    print("**** Updating Datastore")
    entity = datastore.Entity(
        key=key,
        exclude_from_indexes=['entidades','english'])
        # exclude_from_indexes=['description','entidades'])

    entity.update(data)
    ds.put(entity)
    return from_datastore(entity)


create = update


def delete(id, kind='Book'):
    ds = get_client()
    key = ds.key(kind, int(id))
    ds.delete(key)

# Usuarios
def update_user(data, kind='User', id=None):
    ds = get_client()
    if id:
        key = ds.key(kind, int(id))
    else:
        key = ds.key(kind)

    print("**** Updating Datastore")
    entity = datastore.Entity(
        key=key,
        exclude_from_indexes=['entidades','english'])
        # exclude_from_indexes=['description','entidades'])

    entity.update(data)
    ds.put(entity)
    return from_datastore(entity)

create_user = update_user

def read_user(id):
    ds = get_client()
    key = ds.key('User', int(id))
    results = ds.get(key)
    # print(from_datastore(results))
    return from_datastore(results)

def list_user(limit=15,  kind='User',cursor=None):
    ds = get_client()

    query = ds.query(kind='User', order=['email'])
    query_iterator = query.fetch(limit=limit, start_cursor=cursor)
    page = next(query_iterator.pages)

    entities = builtin_list(map(from_datastore, page))
    next_cursor = (
        query_iterator.next_page_token.decode('utf-8')
        if query_iterator.next_page_token else None)

    return entities, next_cursor
