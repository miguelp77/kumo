import json
import logging
import base64
import time
from datetime import timedelta, datetime
import datetime as dt
import time

from flask import current_app, Flask, redirect, request, session, url_for
import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler, setup_logging
import httplib2
from oauth2client.contrib.flask_util import UserOAuth2
from google.cloud import datastore
from google.cloud import storage as cloud_storage
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials


oauth2 = UserOAuth2()

builtin_list = list

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

def _get_storage_client():
    return cloud_storage.Client(
        project=current_app.config['PROJECT_ID'])

# def list(limit=10, kind='Audio', cursor=None):
#     ds = get_client()
#     query = ds.query(kind=kind, order=['title'])
#     it = query.fetch(limit=limit, start_cursor=cursor)
#     entities, more_results, cursor = it.next_page()
#     entities = builtin_list(map(from_datastore, entities))
#     return entities, cursor.decode('utf-8') if len(entities) == limit else None


def create_app(config, debug=False, testing=False, config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(config)

    app.debug = debug
    app.testing = testing

    if config_overrides:
        app.config.update(config_overrides)

    # [START setup_logging]
    if not app.testing:
        client = google.cloud.logging.Client(app.config['PROJECT_ID'])
        handler = CloudLoggingHandler(client)
        # Attaches the handler to the root logger
        setup_logging(handler)
        logging.getLogger().setLevel(logging.INFO)
    # [END setup_logging]

    # Setup the data model.
    with app.app_context():
        model = get_model()
        model.init_app(app)

    # Initalize the OAuth2 helper.
    oauth2.init_app(
        app,
        scopes=['email', 'profile'],
        authorize_callback=_request_user_info)

    # Add a logout handler.
    @app.route('/logout')
    def logout():
        # Delete the user's profile and the credentials stored by oauth2.
        if 'profile' in session:
            del session['profile']
        session.modified = True
        oauth2.storage.delete()
        session.clear()
        # return redirect(request.referrer or '/')
        return redirect('/')

    # Register the Kumo CRUD blueprint.
    from .crud import crud
    app.register_blueprint(crud, url_prefix='/a')

    # Add a default root route.
    @app.route("/")
    def index():
        return redirect(url_for('crud.showHome'))

    # Add an error handler. This is useful for debugging the live application,
    # however, you should disable the output of the exception for production
    # applications.
    @app.errorhandler(500)
    def server_error(e):
        return """
        An internal error occurred: <pre>{}</pre>
        See logs for full stacktrace.
        """.format(e), 500

    @app.before_request
    def make_session_permanent():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=30)

    @app.template_filter('date_to_millis')
    def date_to_millis(d):
        """Converts a datetime object to the number of milliseconds since the unix epoch."""
        return int(time.mktime(d.timetuple())) * 1000

    return app

def format_date(date):
    """
    Give format to date. From YYYY-MM-DD to DD-MM-YYYY
    """
    temp =  datetime.strptime(date, '%Y-%m-%d').date()
    formated_date = str(temp.day) + "-" + str(temp.month) + "-" + str(temp.year)

    return formated_date

def format_datetime(date):
    """
    returns datetime value
    """
    temp =  datetime.strptime(date, '%Y-%m-%d').date()
    formated_date = dt.datetime(temp.year, temp.month, temp.day)
    return formated_date

def date_to_string(date,reverse=False):
    """
    return YYYY-MM-DD from date
    """
    if reverse:
        return date.strftime('%d-%m-%Y')
    return date.strftime('%Y-%m-%d')

def get_model():
    model_backend = current_app.config['DATA_BACKEND']
    if model_backend == 'cloudsql':
        from . import model_cloudsql
        model = model_cloudsql
    elif model_backend == 'datastore':
        from . import model_datastore
        model = model_datastore
    elif model_backend == 'mongodb':
        from . import model_mongodb
        model = model_mongodb
    else:
        raise ValueError(
            "No appropriate databackend configured. "
            "Please specify datastore, cloudsql, or mongodb")

    return model



def _request_user_info(credentials):
    """
    Makes an HTTP request to the Google+ API to retrieve the user's basic
    profile information, including full name and photo, and stores it in the
    Flask session.
    """
    http = httplib2.Http()
    credentials.authorize(http)
    resp, content = http.request(
        'https://www.googleapis.com/plus/v1/people/me',
        )

    if resp.status != 200:
        current_app.logger.error(
            "Error while obtaining user profile: %s" % resp)
        return None

    user_info = json.loads(content.decode('utf-8'))
    user_email = user_info['emails'][0]['value']
    if "@devoteam.com" in content.decode('utf-8') or "@devoteamgcloud.com" in content.decode('utf-8'):
        # session['profile'] = json.loads(content.decode('utf-8'))
        current_app.logger.info("%s is a Devoteam user" % user_email)
    else:
        current_app.logger.error(
            "No devoteam user: %s" % resp)
        return None
    # Se ha creado un listado de usuarios autorizados

    current_app.logger.info("%s is logged" % user_email)
    if is_auth_user(user_email):
        pass
    else:
        current_app.logger.error("Devoteam user is not in list")
        return None
    profile = get_profile(user_email)
    current_app.logger.info("user is %s" % profile)
    if profile == 'banned':
        return None
    session['role'] = profile
    session['profile'] = json.loads(content.decode('utf-8'))
    # print(content.decode('utf-8'))

# Obtengo los emails de los usuarios autorizados del datastore
# Funcion para determinar la longitud de un objeto Iterable
def count_iterable(i):
    return sum(1 for e in i)

def is_auth_user(user):
    ds = get_client()
    query = ds.query(kind='User')
    query.add_filter('email','=',user)
    if count_iterable(query.fetch(2)) > 0:
        current_app.logger.info("OK: %s is in access list" % user)

        return True
    else:
        data = {}
        current_app.logger.error("WARNING: user %s is not in access list" % user)
        data['user'] = user
        data['profile'] = 'user'
        data['comment'] = 'Created in first login'
        data['country'] = 'mx'
        data['email'] = user
        key = ds.key('User')
        entity = datastore.Entity(key=key)
        entity.update(data)
        ds.put(entity)
        current_app.logger.error("ALERT: User %s was created" % user)

        return True

def get_profile(user):
    temp_date = datetime.utcnow()+ timedelta(hours=1)
    date = temp_date.strftime("%Y-%m-%d at %H%M%S")
    
    ds = get_client()
    query = ds.query(kind='User')
    query.add_filter('email','=',user)
    results = iter(query.fetch(1))
    result = results.__next__()
    
    if not 'banned' in result:
        result['lastAccess']= date
        result.update()
        ds.put(result)
        return result['profile']
    else:
        return 'banned'

# def is_banned(user):
#     ds = get_client()
#     query = ds.query(kind='User')
#     query.add_filter('email','=',user)
#     results = iter(query.fetch(1))
#     result = results.__next__()


# APIs ML
# [START authenticating]
DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                 'version={apiVersion}')



def _get_storage_service():
    credentials = GoogleCredentials.get_application_default()
    return discovery.build('storage', 'v1', credentials=credentials)

    return service

def _get_spreadsheets_service():

    credentials = GoogleCredentials.get_application_default()

    return discovery.build(
        'sheets', 'v4', credentials=credentials)


def write_spreadsheet():
    """Transcribe the given audio file.
    Args:
        speech_file: the name of the audio file.
    """
    service = _get_spreadsheets_service()
    spreadsheetId = '18Gkc--JBp_EKkREyTn5P9CNSgb2flQ80-EKk_9E990M'
    rangeName = 'Data!A2:E'
    print('*' * 80)
    request = service.spreadsheets().values().get(spreadsheetId=spreadsheetId, range=rangeName)
    response = request.execute()
    print(response)




