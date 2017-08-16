import json
import logging
import base64
import time
from datetime import timedelta, datetime


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
        del session['profile']
        session.modified = True
        oauth2.storage.delete()
        session.clear()
        return redirect(request.referrer or '/')

    # Register the Kumo CRUD blueprint.
    from .crud import crud
    app.register_blueprint(crud, url_prefix='/a')

    # Add a default root route.
    @app.route("/")
    def index():
        return redirect(url_for('crud.list'))

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

    return app


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
    if "@devoteam.com" in content.decode('utf-8'):
        # session['profile'] = json.loads(content.decode('utf-8'))
        current_app.logger.info("%s is a Devoteam user" % user_email)
    else:
        current_app.logger.error(
            "No devoteam user: %s" % resp)
        return None
    # Se ha creado un listado de usuarios autorizados
    print('*' * 80)
    print('USER_INFO')
    print(user_info)
    print('*' * 80)
    current_app.logger.info("%s is logged" % user_email)
    # if is_auth_user(user_email):
    # else:
    #     current_app.logger.error("Devoteam user is not in allow list")
    #     return None
    # profile = get_profile(user_email)
    # current_app.logger.info("user is %s" % profile)
    # if profile == 'banned':
    #     return None
    # session['role'] = profile
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
        current_app.logger.error("Error: user %s is not in access list" % user)
        return False

def get_profile(user):
    ds = get_client()
    query = ds.query(kind='User')
    query.add_filter('email','=',user)
    results = iter(query.fetch(1))
    result = results.__next__()
    temp_date = datetime.utcnow()+ timedelta(hours=1)
    date = temp_date.strftime("%Y-%m-%d at %H%M%S")
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

# def _get_speech_service():
#     credentials = GoogleCredentials.get_application_default().create_scoped(
#         ['https://www.googleapis.com/auth/cloud-platform'])
#     http = httplib2.Http()
#     credentials.authorize(http)

#     return discovery.build(
#         'speech', 'v1beta1', http=http, discoveryServiceUrl=DISCOVERY_URL)

def _get_storage_service():
    credentials = GoogleCredentials.get_application_default()
    return discovery.build('storage', 'v1', credentials=credentials)

# def _get_sentiment_service():
#     credentials = GoogleCredentials.get_application_default()
#     return discovery.build('language', 'v1beta1', credentials=credentials)

def _speech(speech_file,framerate,language='es-ES'):
    """Transcribe the given audio file.
    Args:
        speech_file: the name of the audio file.
    """
    # [START construct_request]
    storage_service = _get_storage_service()
    bucket = current_app.config['CLOUD_STORAGE_BUCKET']
    req = storage_service.objects().get(bucket=bucket, object=speech_file)

    service = _get_speech_service()
    speech_uri = speech_file.replace('https://storage.googleapis.com/','gs://')

    service_request = service.speech().asyncrecognize(
        body={
            'config': {
                # There are a bunch of config options you can specify. See
                # https://goo.gl/KPZn97 for the full list.
                'encoding': 'LINEAR16',  # raw 16-bit signed LE samples
                # 'sampleRate': 16000,  # 16 khz
                # 'sampleRate': 8000,  # 16 khz
                'sampleRate': framerate,  # 16 khz

                # See https://goo.gl/A9KJ1A for a list of supported languages.
                'languageCode': language,  # a BCP-47 language tag en-US
            },
            'audio': {
                'uri': speech_uri
                }
            })
    # [END construct_request]
    # [START send_request]
    response = service_request.execute()
    name = response['name']
    # Construct a GetOperation request.
    service_request = service.operations().get(name=name)

    while True:
        # Give the server a few seconds to process.
        print('Waiting for server processing...')
        time.sleep(1)
        # Get the long running operation with response.
        response = service_request.execute()
        # if 'progressPercent' in response['metadata']:
        #     print(response['metadata']['progressPercent'])
        if 'done' in response and response['done']:
            break

    # print("***************************")
    print(json.dumps(response['response']))
    if 'results' in response['response']:
        resultado = json.dumps(response['response']['results'])
    else:
        resultado = {'text': 'no results'}
    # print(json.dumps(resultado))
    # print("***************************")
    # print("***************************")
    # print(resultado)
    # print("***************************")
    # print("***************************")
    # print("***************************")
    return json.dumps(resultado)
    # print(json.dumps(response))
    # return json.dumps(response)
    # return response
    # [END send_request]
# def _translate(text_to_translate, target = 'en'):
#     api_key = current_app.config['API_KEY2']
#     translate_client = translate.Client(api_key)
#     text = text_to_translate
#     translation = translate_client.translate(text, target_language=target)
#     return format(translation['translatedText'])

# def _sentiment(text):
#     service = _get_sentiment_service()
#     service_request = service.documents().analyzeSentiment(
#         body={
#             'document': {
#                 'type': 'PLAIN_TEXT',
#                 'content': text.decode("utf-8"),
#             }
#         }
#     )
#     response = service_request.execute()
#     print("response")
#     print("response")
#     print("response")
#     print(response)
#     return response
# def _analyze_entities(text, encoding='UTF32'):
#     body = {
#         'document': {
#             'type': 'PLAIN_TEXT',
#             'content': text,
#         },
#         'encoding_type': encoding,
#     }

#     service = _get_sentiment_service()

#     request = service.documents().analyzeEntities(body=body)
#     response = request.execute()

#     return response

# def audio_to_text(id):
#     # audio_data = get_model().read_audio(id)
#     ds = get_client()
#     key = ds.key('Audio', int(id))

#     results = ds.get(key)

#     audio_data = from_datastore(results)

#     results = datastore.Entity(
#         key=key,
#         exclude_from_indexes=['entidades','english','text','sentences'])

#     # results = audio_data
#     audio_url = audio_data.get('audioUrl')
#     audio_framerate = audio_data.get('framerate')
#     audio_language = audio_data.get('language')

#     text_from_audio = _speech(audio_url, audio_framerate,audio_language)
#     #audio_data = text_from_audio
#     jason = json.loads(text_from_audio)
#     jason2 = json.loads(jason)
#     print("text_from_audio")
#     print(jason)
#     # El SPEECH API no devuelve siempre text_from_audio
#     # - El formato del archivo no es configurado.
#     if len(jason) > 0:
#         # es_text =jason['results'][0]['alternatives'][0]['transcript']
#         es_text = ""
#         confidence = []
#         sentences = []
#         # print(jason)
#         for r in jason2:
#             sentence = r['alternatives'][0]['transcript']
#             # print("---------")
#             # print(r['alternatives'][0]['transcript'])
#             sentences.append(sentence)
#             # print(r)
#             if 'confidence' in r['alternatives'][0]:
#                 confidence.append(float(r['alternatives'][0]['confidence']))
#             else:
#                 confidence.append(0)
#             es_text = es_text + r['alternatives'][0]['transcript'] + ". "
#         # es_text =jason
#         acierto = sum(confidence)/len(confidence)
#         en_text = _translate(str(es_text))
#         # print("Acierto")
#         # print("=======")
#         print(audio_language)
#         # print(acierto)
#         if audio_language == 'fr-FR':
#             entidades = _analyze_entities(str(en_text))
#             sentiment = _sentiment(en_text.encode('utf-8'))
#         elif audio_language == 'ca-ES':
#             entidades = _analyze_entities(str(en_text))
#             sentiment = _sentiment(en_text.encode('utf-8'))
#         elif audio_language == 'it-IT':
#             entidades = _analyze_entities(str(en_text))
#             sentiment = _sentiment(en_text.encode('utf-8'))
#         elif audio_language == 'pt-PT':
#             entidades = _analyze_entities(str(en_text))
#             sentiment = _sentiment(en_text.encode('utf-8'))
#         else:
#             entidades = _analyze_entities(str(es_text))
#             sentiment = _sentiment(es_text.encode('utf-8'))


#         # polarity = sentiment['documentSentiment']['polarity']
#         polarity = sentiment['documentSentiment']['score']
#         magnitude = sentiment['documentSentiment']['magnitude']

#         # Set values to datastore
#         results.__setitem__("text", str(es_text))
#         results.__setitem__("confidence",str(acierto))

#         # New items sentences and confidence
#         # sentences stores each phrase return by GS API
#         # confidences stores each percentage return by GS API
#         results['sentences'] = sentences
#         results['confidences'] = confidence

#         # results.__setitem__("confidence",str(jason['results'][0]['alternatives'][0]['confidence']))
#         results.__setitem__("english",str(en_text))
#         results.__setitem__("polarity",str(polarity))
#         results.__setitem__("magnitude",str(magnitude))
#         results['entidades'] = str(entidades)

#         # Completo toda la entida al haber sido borrada
#         # para quitar las entidades del indice al poder llegar a tener
#         # mas de 1500 caracteres.
#         # results = datastore.Entity(
#         # key=key,
#         # exclude_from_indexes=['entidades','english'])
#         for key, value in audio_data.items():
#             results[key] = value


#         results.update()
#         # current_app.logger.info(
#         #     "audio_data: %s" % results)
#         # current_app.logger.info(
#         #     "audio_data: %s" % results)

#         ds.put(results)
#     else:
#         results.__setitem__("text", "No Transcription")
#         results.__setitem__("confidence","0")
#         results.__setitem__("english","No Translation")
#         results.__setitem__("polarity","0")
#         results.__setitem__("magnitude","0")


#         results.update()
#         results = datastore.Entity(
#             key=key,
#             exclude_from_indexes=['entidades','english'])
#         current_app.logger.info(
#             "audio_data: %s" % results)
#         #

#         ds.put(results)

#     # return text_from_audio
#     return redirect(url_for('crud.view_audio', id=id))
