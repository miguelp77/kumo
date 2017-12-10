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
import json
import datetime as dt

builtin_list = list


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False




def get_profile(user=None):
    if not user:
        user = session['profile']['emails'][0]['value']
    ds = get_client()
    query = ds.query(kind='User')
    query.add_filter('email','=',user)
    results = iter(query.fetch(1))
    print(results)
    result = results.__next__()
    print("get_profile " + result['profile'])
    return result['profile']


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


def list_all(limit=10000,  email=None,  day=None, month=None, year=None, project=None, hours=None,
     status=None, kind='Allocation',cursor=None):
    """
    List all allocations. email is optional
    """
    ds = get_client()
    query = ds.query(kind='Allocation')
    if email:
        query.add_filter('user_email', '=', str(email))
    if day:
        query.add_filter('formated_start_date', '=', str(day))
    if month:
        query.add_filter('month', '=', int(month))
    if year:
        query.add_filter('year', '=', int(year))
    if project:
        query.add_filter('project_name', '=', str(project))
    if hours:
        query.add_filter('hours_type', '=', str(hours))
    if status:
        query.add_filter('status', '=', str(status))

    query_iterator = query.fetch()
    entities = list(query_iterator)
    # page = next(query_iterator.pages)
    #
    # entities = builtin_list(map(from_datastore, page))
    # next_cursor = (
    #     query_iterator.next_page_token.decode('utf-8')
    #     if query_iterator.next_page_token else None)
    next_cursor = None
    return entities, next_cursor


def list_by_user(user_id, day=None, month=None, year=None, project=None, hours=None,
     status=None, kind='Allocation', limit=500, cursor=None):
    """
    List by users and params from GET
    """
    ds = get_client()
    query = ds.query(kind='Allocation')

    query.add_filter('createdById', '=', user_id)
    print(project)
    if day:
        query.add_filter('formated_start_date', '=', str(day))
    if month:
        query.add_filter('month', '=', int(month))
    if year:
        query.add_filter('year', '=', int(year))
    if project:
        query.add_filter('project_name', '=', str(project))
    if hours:
        query.add_filter('hours_type', '=', str(hours))
    if status:
        query.add_filter('status', '=', str(status))

    # query.add_filter('archived', '=', '-')

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
        print(ms.sort())
        dates[k] = ms

    return entities, next_cursor, dates

def list_by_month(user_id,  kind='Allocation',limit=50, cursor=None,year='2017', month=None):
    ds = get_client()
    query = ds.query(
        kind='Allocation',
    )
    query.add_filter('createdById', '=', user_id)
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


def assigned_to_me(user_email, kind='Allocation', limit=None,  email=None,  day=None, month=None, year=None, project=None, hours=None,
     status=None, cursor=None):
    ds = get_client()

    query = ds.query(kind='Allocation')

    if email:
        print('email -->' + email + "<")
        query.add_filter('user_email', '=', email)
    if day:
        query.add_filter('formated_start_date', '=', str(day))
    if month:
        query.add_filter('month', '=', int(month))
    if year:
        query.add_filter('year', '=', int(year))
    if project:
        query.add_filter('project_name', '=', str(project))
    if hours:
        query.add_filter('hours_type', '=', str(hours))
    if status:
        query.add_filter('status', '=', str(status))

    query.add_filter('approver','=',str(user_email))
    # query.add_filter('status','=','submit')

    query_iterator = query.fetch()
    page = next(query_iterator.pages)

    entities = builtin_list(map(from_datastore, page))
    next_cursor = (
        query_iterator.next_page_token.decode('utf-8')
        if query_iterator.next_page_token else None)
    return entities, next_cursor


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
    data['approver'] = data['approver'].strip()
    entity.update(data)
    ds.put(entity)
    return from_datastore(entity)


create = update



def create_allocations(data):
    ds = get_client()
    entidades = []
    for d in data:
        key = ds.key('Allocation')
        entity = datastore.Entity(key=key)
        entity.update(d)
        entidades.append(entity)
    ds.put_multi(entidades)

    return from_datastore(entity)


def update_allocation(data, kind='Allocation', id=None):
    ds = get_client()
    ancestor = ds.key('AllocList', 'default')
    if id:
        key = ds.key(kind, int(id))
    else:
        key = ds.key(kind)


    entity = datastore.Entity(key=key)
    entity.update(data)
    ds.put(entity)
 
    return from_datastore(entity)

def update_multi(data, new_status):
    '''
    Update status of allocations
    :param data: Allocations data
    :param new_status: New status for all these allocations
    :return: None
    '''
    client = get_client()
    entidades = []
    for d in data:
        entidad = read_allocation(int(d))
        entidad['status'] = new_status
        entidades.append(entidad)
    client.put_multi(entidades)


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

def list_user(limit=200,  kind='User',cursor=None):
    ds = get_client()

    query = ds.query(kind='User', order=['email'])
    query_iterator = query.fetch(start_cursor=cursor)
    page = next(query_iterator.pages)

    entities = builtin_list(map(from_datastore, page))
    next_cursor = (
        query_iterator.next_page_token.decode('utf-8')
        if query_iterator.next_page_token else None)

    return entities, next_cursor



#Projects
def set_auths(id):
    ds = get_client()
    key = ds.key('Project', int(id))

    entity = datastore.Entity(key=key)

    data = ds.get(key)
    if data['users']:
        data["auths"]=data["users"]

    entity.update(data)
    ds.put(entity)
    return from_datastore(entity)

def list_projects(limit=50, kind='Project', user_email=None, cursor=None):
    ds = get_client()
    query = ds.query(kind=kind)
    if user_email:
        query.add_filter('auths','=',user_email)
    query_iterator = query.fetch( start_cursor=cursor, limit=limit)
    page = next(query_iterator.pages)

    entities = builtin_list(map(from_datastore, page))
    next_cursor = (
        query_iterator.next_page_token.decode('utf-8')
        if query_iterator.next_page_token else None)
    return entities, next_cursor


def generic_projects(kind='Project', user_email=None, cursor=None):
    ds = get_client()
    query = ds.query(kind=kind)
    query.add_filter('for_all','=',True)
    query_iterator = query.fetch( start_cursor=cursor, limit=10)
    page = next(query_iterator.pages)

    entities = builtin_list(map(from_datastore, page))
    next_cursor = (
        query_iterator.next_page_token.decode('utf-8')
        if query_iterator.next_page_token else None)
    return entities


def check_projects(user_email, limit=50, kind='Project', cursor=None):
    ds = get_client()
    query = ds.query(kind=kind,
            filters=[
            # ('approver', '>=', user_email)
        ]
    )
    if user_email:
        query.add_filter('approver','=',user_email)
    query_iterator = query.fetch( start_cursor=cursor)
    page = next(query_iterator.pages)

    entities = builtin_list(map(from_datastore, page))
    next_cursor = (
        query_iterator.next_page_token.decode('utf-8')
        if query_iterator.next_page_token else None)
    return entities, next_cursor

def list_projects_full(kind='Project'):
    ds = get_client()
    query = ds.query(kind=kind)
    query_iterator = query.fetch()
    page = next(query_iterator.pages)

    entities = builtin_list(map(from_datastore, page))

    return entities



def regularizar(ee):
    print("regularizar" + str(ee))
    ds = get_client()
    query = ds.query(kind='Allocation')
    query.add_filter('status','=','approved')
    # query.add_filter('project_name','=','Google Group Iberia')

    query_iterator = query.fetch()
    page = next(query_iterator.pages)
    entities = builtin_list(map(from_datastore, page))
    for e in entities:
        print(e['id'])
        e['status'] = 'accepted'
        # e.update(data)
        ds.put(e)
    return entities



def read_project(id):
    ds = get_client()
    key = ds.key('Project', int(id))
#    regularizar(11)
    results = ds.get(key)
    return from_datastore(results)



def create_project(data, id=None):
    ds = get_client()
    if id:
        key = ds.key('Project', int(id))
    else:
        key = ds.key('Project')
    entity = datastore.Entity(key=key)
    # if not data:
    #     data = ds.get(key)
    if data['approver']:
        approvers =[]
        approvers = [x.strip() for x in str(data['approver']).split(',')]
        data['approver'] = ''
        data['approver'] = approvers

    if data['hours_type']:
        hours_type =[]
        hours_type = [x.strip() for x in str(data['hours_type']).split(',')]
        data['hours_type'] = hours_type
    # if data['name']:
    data['dvt_code'] = data['project_id']

    data['name'] = str(data['client']) + ' - ' + str(data['product']) + ' [' + str(data['project_id']) + ']'

    entity.update(data)
    ds.put(entity)
    return from_datastore(entity)




def update_project(data, id, users, submit_hours, accept_hours, hours_per_user=None):
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
    data['hours_per_user'] = json.dumps(hours_per_user)
    entity.update(data)
    ds.put(entity)
    return from_datastore(entity)



def add_auths(id,emails):
    ds = get_client()
    if id:
        key = ds.key('Project', int(id))
    else:
        key = ds.key('Project')
    entity = datastore.Entity(key=key)
    data = ds.get(key)

    if emails:
        auths = [x.strip() for x in str(emails).split(',')]
        if 'auths' in data:
            data['auths'].extend(auths)
            # data['auths'] = set(data['auths'])
        else:
            data['auths'] = auths
            # data['auths'] = set(data['auths'])

    entity.update(data)
    ds.put(entity)
    return from_datastore(entity)


def remove_auth(id,email):
    ds = get_client()
    if id:
        key = ds.key('Project', int(id))
    else:
        key = ds.key('Project')
    entity = datastore.Entity(key=key)
    data = ds.get(key)

    if email:
        if 'auths' in data:
            if email in data['auths']: data['auths'].remove(email)

        # auths = [x.strip() for x in str(emails).split(',')]
        #
        #     # data['auths'] = set(data['auths'])
        # else:
        #     data['auths'] = auths
        #     # data['auths'] = set(data['auths'])

    entity.update(data)
    ds.put(entity)
    return from_datastore(entity)


def collect_project_hours(id):
    """
    Collect all the information of one Project

    :param id: Project ID in allocations
    :return: submit_hours and accept_hours
    """
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
    temp = 0
    emails = []
    hours_per_user = {}
    for e in entity:

        if not e['user_email'] in emails:
            emails.append(e['user_email'])

        if e['status'] == 'submit':
            submit_hours = submit_hours + int(e['hours'])
            temp = int(e['hours'])
        if e['status'] == 'accepted':
            accept_hours = accept_hours + int(e['hours'])
            temp = int(e['hours'])


        if e['user_email'] in hours_per_user:
            hours_per_user[e['user_email']] = int(hours_per_user[e['user_email']]) + temp
        else:
            hours_per_user[e['user_email']] = temp

    data = update_project(data=None, id=id, users = emails,
        submit_hours=submit_hours, accept_hours= accept_hours, hours_per_user= hours_per_user)
    get_vacances_from_project(id)
    return data, submit_hours, accept_hours


def get_vacances_from_project(id):
    """
    Collect the dates for timeline

    :param id: Project ID in allocations
    :return: start and end date
    """
    ds = get_client()
    query = ds.query(kind='Allocation',
    filters=[
            ('project', '=', id)
        ])
    query_iterator = query.fetch()
    page = next(query_iterator.pages)
    entity = builtin_list(map(from_datastore, page))


    emails = {}
    for e in entity:
        if not e['user_email'] in emails:
            emails[e['user_email']] = [e['start_date']]
        else:
            emails[e['user_email']].append(e['start_date'])
    submit_hours = 0
    accept_hours = 0
    temp = 0
    hours_per_user = {}
    for user, val in emails.items():
        dates = set(val)
        emails[user] = sorted(dates, key=lambda d: tuple(map(int, d.split('-'))))

    print(emails)
    return emails


def set_country(id, cty):
    ds = get_client()
    key = ds.key('User', int(id))

    entity = datastore.Entity(key=key)
    data = ds.get(key)

    data['country'] = cty
    entity.update(data)

    ds.put(entity)
    return from_datastore(entity)


def set_bulk_country(cty):
    ds = get_client()

    query = ds.query(kind='User', order=['email'])
    query_iterator = query.fetch()
    page = next(query_iterator.pages)

    entities = builtin_list(map(from_datastore, page))
    for entity in entities:
        if 'country' in entity:
            print(entity['email'] + " " + entity['country'] + " - " + cty)
            if entity['country'] == 'tbd':
                set_country(entity['id'], cty)
        else:
            set_country(entity['id'], cty)
            print(entity['email'] + " - " + cty)


    return entities


# def add_auths(id,emails):
#     ds = get_client()
#     if id:
#         key = ds.key('Project', int(id))
#     else:
#         key = ds.key('Project')
#     entity = datastore.Entity(key=key)
#     data = ds.get(key)
#
#     if emails:
#         auths = [x.strip() for x in str(emails).split(',')]
#         if 'auths' in data:
#             data['auths'].extend(auths)
#             # data['auths'] = set(data['auths'])
#         else:
#             data['auths'] = auths
#             # data['auths'] = set(data['auths'])
#
#     entity.update(data)
#     ds.put(entity)
#     return from_datastore(entity)