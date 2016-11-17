import json
import logging
import base64


from flask import current_app, Flask, redirect, request, session, url_for
import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler, setup_logging
import httplib2
from oauth2client.contrib.flask_util import UserOAuth2
from google.cloud import datastore, translate
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


def list(limit=10, kind='Audio', cursor=None):
    ds = get_client()
    query = ds.query(kind=kind, order=['title'])
    it = query.fetch(limit=limit, start_cursor=cursor)
    entities, more_results, cursor = it.next_page()
    entities = builtin_list(map(from_datastore, entities))
    return entities, cursor.decode('utf-8') if len(entities) == limit else None


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


    @app.route('/api_tasks/<id>')
    def audio_to_text(id):
        # audio_data = get_model().read_audio(id)
        ds = get_client()
        key = ds.key('Audio', int(id))
        results = ds.get(key)
        audio_data = from_datastore(results)

        audio_url = audio_data.get('audioUrl')
        text_from_audio = _speech(audio_url)
        #audio_data = text_from_audio
        jason = json.loads(text_from_audio)
        # El SPEECH API no devuelve siempre text_from_audio
        # - El formato del archivo no es configurado.
        if len(jason) > 0:
            es_text =jason['results'][0]['alternatives'][0]['transcript']
            # es_text = "Enhorabuena por vuestro gran servicio. Me gustaria conocer otros servicios"
            en_text = _translate(es_text)

            sentiment = _sentiment(en_text.encode('utf-8'))
            polarity = sentiment['documentSentiment']['polarity']
            magnitude = sentiment['documentSentiment']['magnitude']



            results.__setitem__("text", str(es_text))
            results.__setitem__("confidence",str(jason['results'][0]['alternatives'][0]['confidence']))
            results.__setitem__("english",str(en_text))
            results.__setitem__("polarity",str(polarity))
            results.__setitem__("magnitude",str(magnitude))

            results.update()
            current_app.logger.info(
                "audio_data: %s" % results)
            ds.put(results)
        else:
            results.__setitem__("text", "No Transcription")
            results.__setitem__("confidence","0")
            results.__setitem__("english","No Translation")
            results.__setitem__("polarity","0")
            results.__setitem__("magnitude","0")

            results.update()
            current_app.logger.info(
                "audio_data: %s" % results)
            ds.put(results)

        # return text_from_audio
        return redirect(url_for('crud.view_audio', id=id))
    # Add a logout handler.
    @app.route('/logout')
    def logout():
        # Delete the user's profile and the credentials stored by oauth2.
        del session['profile']
        session.modified = True
        oauth2.storage.delete()
        return redirect(request.referrer or '/')

    # Register the Bookshelf CRUD blueprint.
    from .crud import crud
    app.register_blueprint(crud, url_prefix='/books')

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
        # 'https://speech.googleapis.com/$discovery/rest?version=v1beta1'
        )

    if resp.status != 200:
        current_app.logger.error(
            "Error while obtaining user profile: %s" % resp)
        return None

    session['profile'] = json.loads(content.decode('utf-8'))

# APIs ML
# [START authenticating]
DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                 'version={apiVersion}')

def _get_speech_service():
    credentials = GoogleCredentials.get_application_default().create_scoped(
        ['https://www.googleapis.com/auth/cloud-platform'])
    http = httplib2.Http()
    credentials.authorize(http)

    return discovery.build(
        'speech', 'v1beta1', http=http, discoveryServiceUrl=DISCOVERY_URL)

def _get_storage_service():
    # Get the application default credentials. When running locally, these are
    # available after running `gcloud init`. When running on compute
    # engine, these are available from the environment.
    credentials = GoogleCredentials.get_application_default()

    # Construct the service object for interacting with the Cloud Storage API -
    # the 'storage' service, at version 'v1'.
    # You can browse other available api services and versions here:
    #     http://g.co/dv/api-client-library/python/apis/
    return discovery.build('storage', 'v1', credentials=credentials)

def _get_sentiment_service():
    credentials = GoogleCredentials.get_application_default()
    return discovery.build('language', 'v1beta1', credentials=credentials)

def _speech(speech_file):
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
    
    service_request = service.speech().syncrecognize(
        body={
            'config': {
                # There are a bunch of config options you can specify. See
                # https://goo.gl/KPZn97 for the full list.
                'encoding': 'LINEAR16',  # raw 16-bit signed LE samples
                # 'sampleRate': 16000,  # 16 khz
                'sampleRate': 8000,  # 16 khz

                # See https://goo.gl/A9KJ1A for a list of supported languages.
                'languageCode': 'es-ES',  # a BCP-47 language tag en-US
            },
            'audio': {
                'uri': speech_uri
                }
            })
    # [END construct_request]
    # [START send_request]
    response = service_request.execute()
    return json.dumps(response)
    # return response
    # [END send_request]
def _translate(text_to_translate, target = 'en'):
    api_key = current_app.config['API_KEY']
    translate_client = translate.Client(api_key)
    text = text_to_translate
    translation = translate_client.translate(text, target_language=target)
    return format(translation['translatedText'])

def _sentiment(text):
    service = _get_sentiment_service()
    service_request = service.documents().analyzeSentiment(
        body={
            'document': {
                'type': 'PLAIN_TEXT',
                'content': text.decode("utf-8"),
            }
        }
    )
    response = service_request.execute()
    return response
