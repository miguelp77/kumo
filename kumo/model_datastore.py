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

from collections import defaultdict
import datetime as dt


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


# BORRAR
# def list(limit=10, cursor=None):
#     ds = get_client()
#     query = ds.query(kind='Book', order=['title'])
#     it = query.fetch(limit=limit, start_cursor=cursor)
#     entities, more_results, cursor = it.next_page()
#     entities = builtin_list(map(from_datastore, entities))
#     return entities, cursor.decode('utf-8') if len(entities) == limit else None

# Old datastore
# def list(limit=10, kind='Allocation', cursor=None):
#     ds = get_client()
#     query = ds.query(kind=kind, order=['project'])
#     it = query.fetch(limit=limit, start_cursor=cursor)
#     entities, more_results, cursor = it.next_page()
#     entities = builtin_list(map(from_datastore, entities))
#     return entities, cursor.decode('utf-8') if len(entities) == limit else None

# OLD
# def list_projects(limit=50, kind='Project', cursor=None):
#     ds = get_client()
#     query = ds.query(kind=kind, order=['country'])
#     it = query.fetch(limit=limit, start_cursor=cursor)
#     entities, more_results, cursor = it.next_page()
#     entities = builtin_list(map(from_datastore, entities))
#     return entities, cursor.decode('utf-8') if len(entities) == limit else None


# OLD
# def list_by_user(user_id, kind='Allocation', limit=10, cursor=None):
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

# list of allocations pending to review
# OLD
def assigned_to_me(user_email, kind='Allocation', limit=50, cursor=None):
    ds = get_client()
    query = ds.query(
        kind=kind,
        filters=[
            ('approver', '=', user_email),
            ('status', '=', 'submit'),
        ]
    )
    it = query.fetch(limit=limit, start_cursor=cursor)
    entities, more_results, cursor = it.next_page()
    entities = builtin_list(map(from_datastore, entities))
    return entities, cursor.decode('utf-8') if len(entities) == limit else None


def list_all(limit=10,  email=None, kind='Allocation',cursor=None):
    ds = get_client()
    if email:
        query = ds.query(kind='Allocation', filters=[('user_email','=',email)])
    else:
        query = ds.query(kind='Allocation', order=['project'])
    query_iterator = query.fetch( start_cursor=cursor, limit=limit)
    page = next(query_iterator.pages)

    entities = builtin_list(map(from_datastore, page))
    next_cursor = (
        query_iterator.next_page_token.decode('utf-8')
        if query_iterator.next_page_token else None)
    return entities, next_cursor


def create_tasklist(name):
    ds = get_client()
    kind = ds.key('TaskList',name)
    task = datastore.Entity(kind)    
    task.update({
        'name': name,
        'head': 'PEPE',
        'Jornadas': 4,
        'description': 'Learn Cloud Datastore'
    })
    id = ds.put(task)

    print('O'*80)
    print('DONE')
    return id

def test_datastore(user_id):
    ds = get_client()
    # create_tasklist('default')
    kind = ds.key('TaskList','default','Task')
    task = datastore.Entity(kind)
    task.update({
        'category': 'Personal',
        'done': False,
        'priority': 4,
        'description': 'Learn Cloud Datastore'
    })
    id = ds.put(task)

    print('O'*80)
    print(user_id)
    query = ds.query(kind='Task')
    # query.add_filter('done', '=', False)
    query.add_filter('priority', '=', 4)
    query.add_filter('done', '=', False)
    query.order = ['-priority']

    # query = ds.query()
    print('$'*80)

    query_iterator = query.fetch(limit=5, start_cursor=None)
    page = next(query_iterator.pages)
    first_page_entities = list(page)
    print(first_page_entities)
    print('^'*80)
    return id



def list_by_user(user_id,  kind='Allocation',limit=5, cursor=None):
    # id = test_datastore(user_id)
    print('TEST ' + str(id))

    # start_date = dt.datetime(2017, 8, 1)
    # end_date = dt.datetime(2017, 8, 30)
    # print('*'*80)
    # print(start_date)
    ds = get_client()
    # ancestor = ds.key('User', user_id)
    # ancestor = ds.key('User', user_id, 'Project', '5664248772427776' )
    query = ds.query(
        kind='Allocation',
        # ancestor=ancestor
        # filters=[
            # ('createdById', '=', user_id),
        #     ('datetime_start', '>', start_date),
        # ],
        # order=['datetime_start']
    )
    query.add_filter('createdById', '=', user_id)
    query_iterator = query.fetch(limit=limit, start_cursor=cursor)
    page = next(query_iterator.pages)

    entities = builtin_list(map(from_datastore, page))
    next_cursor = (
        query_iterator.next_page_token.decode('utf-8')
        if query_iterator.next_page_token else None)

    #get the months
    
    dates = defaultdict(list)
    for e in entities:
        d = e['datetime_start']

        dates[d.strftime('%Y')].append(d.strftime('%m'))

        # if d.strftime('%Y') in dates:
        #     dates[d.strftime('%Y')][d.strftime('%m')]
        # else:
        #     # dates[d.strftime('%Y')]=d.strftime('%m')
        #     dates[d.strftime('%Y')][d.strftime('%m')]=d.strftime('%m')
        #     # dates[d.strftime('%Y')].append(d.strftime('%m'))


    for k,v in dates.items():
        ms = list(set(v))
        print(ms.sort())
        dates[k] = ms

    return entities, next_cursor, dates

def list_by_month(user_id,  kind='Allocation',limit=50, cursor=None,year='2017', month=None):
    ds = get_client()
    query = ds.query(
        kind='Allocation',
    )
    # query.add_filter('createdById', '=', user_id)
    query.add_filter('month', '=', int(month))
    # query.add_filter('year', '=', year)

    query_iterator = query.fetch(limit=limit, start_cursor=cursor)
    page = next(query_iterator.pages)
    entities = builtin_list(map(from_datastore, page))
    next_cursor = (
        query_iterator.next_page_token.decode('utf-8')
        if query_iterator.next_page_token else None)

    #get the months
    
    dates = defaultdict(list)
    for e in entities:
        d = e['datetime_start']
        dates[d.strftime('%Y')].append(d.strftime('%m'))

    for k,v in dates.items():
        ms = list(set(v))
        dates[k] = ms
        
    return entities, next_cursor, dates


def assigned_to_me(user_email, kind='Allocation', limit=50, cursor=None):
    ds = get_client()
    query = ds.query(
        kind=kind,
        filters=[
            ('approver', '=', user_email),
            ('status', '=', 'submit'),
        ]
    )
    query_iterator = query.fetch(limit=limit, start_cursor=cursor)
    page = next(query_iterator.pages)

    entities = builtin_list(map(from_datastore, page))
    next_cursor = (
        query_iterator.next_page_token.decode('utf-8')
        if query_iterator.next_page_token else None)

    return entities, next_cursor

def list_projects(limit=50, kind='Project', cursor=None):
    ds = get_client()
    query = ds.query(kind=kind, order=['country'])
    query_iterator = query.fetch( start_cursor=cursor, limit=limit)
    page = next(query_iterator.pages)

    entities = builtin_list(map(from_datastore, page))
    next_cursor = (
        query_iterator.next_page_token.decode('utf-8')
        if query_iterator.next_page_token else None)
    return entities, next_cursor

def check_projects(user_email, limit=50, kind='Project', cursor=None):
    ds = get_client()
    print(user_email)
    query = ds.query(kind=kind,
            filters=[
            # ('approver', '>=', user_email)
        ]
    )
    if user_email:
        query.add_filter('approver','=',user_email)
    query_iterator = query.fetch( start_cursor=cursor, limit=limit)
    page = next(query_iterator.pages)

    entities = builtin_list(map(from_datastore, page))
    next_cursor = (
        query_iterator.next_page_token.decode('utf-8')
        if query_iterator.next_page_token else None)
    return entities, next_cursor

def read_project(id):
    ds = get_client()
    key = ds.key('Project', int(id))
    results = ds.get(key)
    return from_datastore(results)

def update_project(data, id, users, submit_hours, accept_hours):
    ds = get_client()
    if id:
        key = ds.key('Project', int(id))
    else:
        key = ds.key('Project')
    entity = datastore.Entity(key=key)

    if not data:
        data = ds.get(key)
    if users:
        data['users'] = users 
    if submit_hours:
        data['submit_hours'] = int(submit_hours)
    if accept_hours:
        data['accept_hours'] = int(accept_hours)
    data['consumed_hours'] = int(submit_hours) + int(accept_hours)
    entity.update(data)
    ds.put(entity)
    return from_datastore(entity)

def collect_project_hours(id):
    ds = get_client()
    query = ds.query(kind='Allocation',
    filters=[
            ('project', '=', id)
        ])
    query_iterator = query.fetch()
    page = next(query_iterator.pages)
    entity = builtin_list(map(from_datastore, page))

    submit_hours = 0
    accept_hours = 0
    emails = []
    for e in entity:
        if not e['user_email'] in emails:
            emails.append(e['user_email'])

        if e['status'] == 'submit':
            submit_hours = submit_hours + int(e['hours'])
        if e['status'] == 'accepted':
            accept_hours = accept_hours + int(e['hours'])

    data = update_project(data=None, id=id, users = emails,
        submit_hours=submit_hours, accept_hours= accept_hours)
    print('O0'*80)
    print(emails)    
    return data, submit_hours, accept_hours

def give_me_name(id,kind):
    """
    returns the name of a kind in function of ID
    """
    ds = get_client()
    key = ds.key(kind, int(id))
    results = ds.get(key)
    name = results['name']
    return name    
############
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

# def read_project(id):
#     ds = get_client()
#     key = ds.key('Project', int(id))
#     results = ds.get(key)
#     print(from_datastore(results))
#     return from_datastore(results)

def read_allocation(id):
    ds = get_client()
    key = ds.key('Allocation', int(id))

    results = ds.get(key)
    print(from_datastore(results))
    return from_datastore(results)

def update(data, kind='Allocation', id=None):
    ds = get_client()
    if id:
        key = ds.key('Allocation', int(id))
    else:
        # Ancestors as follow
        # [Project: data['project'], Approver: data['approver']]
        # key = ds.key('User',data['user_id'],'Project', data['project'], 'Allocation')
        key = ds.key('Allocation')
    entity = datastore.Entity(key=key)
    data['month'] =int(data['datetime_start'].strftime('%m'))
    data['year'] =int(data['datetime_start'].strftime('%Y'))
    print('ñ'*80)
    print(data)
    entity.update(data)
    ds.put(entity)
    return from_datastore(entity)



# def update(data, kind='Allocation', id=None):
#     ds = get_client()
#     if id:
#         key = ds.key(kind, int(id))
#     else:
#         key = ds.key('AllocList', 'default','Allocation')
    
#     entity = datastore.Entity(
#         key=key,
#         exclude_from_indexes=['entidades','english'])
#         # exclude_from_indexes=['description','entidades'])

#     entity.update(data)
#     ds.put(entity)
    
#     # task = datastore.Entity(
#     #     ds.key('TaskList', 'default', 'Task'))
#     # task.update({
#     #     'category': 'Personal',
#     #     'description': 'Learn Cloud Datastore',
#     # })
#     # ds.put(task)

#     # # [START ancestor_query]
#     # ancestor = ds.key('TaskList', 'default')
#     # query = ds.query(kind='Task', ancestor=ancestor)
#     # print(query.fetch())
#     # print('*'*100)
#     return from_datastore(entity)


create = update


def update_allocation(data, kind='Allocation', id=None):
    ds = get_client()
    ancestor = ds.key('AllocList', 'default')
    if id:
        key = ds.key(kind, int(id))
    else:
        key = ds.key('AllocList', 'default','Allocation')


    entity = datastore.Entity(key=key)
    entity.update(data)
    ds.put(entity)
 
    return from_datastore(entity)


def delete(id, kind='Allocation'):
    ds = get_client()
    key = ds.key(kind, int(id))
    ds.delete(key)

def delete_multi(ids, kind='Allocation'):
    ds = get_client()
    for id in ids:
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
