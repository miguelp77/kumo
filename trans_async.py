
# [START import_libraries]
import argparse
import base64
import json
import time

from googleapiclient import discovery
import httplib2
from oauth2client.client import GoogleCredentials
import pprint
# [END import_libraries]


# [START authenticating]


# Application default credentials provided by env variable
# GOOGLE_APPLICATION_CREDENTIALS
def get_speech_service():
    credentials = GoogleCredentials.get_application_default().create_scoped(
        ['https://www.googleapis.com/auth/cloud-platform'])
    http = httplib2.Http()
    credentials.authorize(http)

    return discovery.build('speech', 'v1beta1', http=http)
# [END authenticating]


# def main(speech_file):
def main():
    """Transcribe the given audio file asynchronously.
    Args:
        speech_file: the name of the audio file.
    """
    # [START construct_request]
    # with open(speech_file, 'rb') as speech:
    #     # Base64 encode the binary audio file for inclusion in the request.
    #     speech_content = base64.b64encode(speech.read())

    service = get_speech_service()
    service_request = service.speech().asyncrecognize(
        body={
            'config': {
                # There are a bunch of config options you can specify. See
                # https://goo.gl/KPZn97 for the full list.
                # 'encoding': 'LINEAR16',  # raw 16-bit signed LE samples
                'encoding': 'LINEAR16',  # raw 16-bit signed LE samples
                'sampleRate': 8000,  # 16 khz
                # See http://g.co/cloud/speech/docs/languages for a list of
                # supported languages.
                'languageCode': 'es-ES',  # a BCP-47 language tag
                "speech_context": {
                    "phrases":["servicedesk Buenos d\\u00edas la atiende"]
                }
            },
            'audio': {
                # 'content': speech_content.decode('UTF-8')
                # 'uri': 'gs://devodemo-2016/produban_recortado_mx.wav'
                'uri': 'gs://devodemo-2016/606312450_29_900_20170102085747-2017-01-25-101807.wav'
                }
            })
    # [END construct_request]
    # [START send_request]
    response = service_request.execute()
    print(json.dumps(response))
    # [END send_request]

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

    pprint.pprint(json.dumps(response['response']['results']))

    # print(json.dumps(response['response']['results']))


# [START run_application]
if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     'speech_file', help='Full path of audio file to be recognized')
    # args = parser.parse_args()
    # main(args.speech_file)
    main()
    # [END run_application]
