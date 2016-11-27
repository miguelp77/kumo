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
import json


from bookshelf import get_model, oauth2, storage
from flask import Blueprint, current_app, redirect, render_template, request, \
    session, url_for
import datetime
from werkzeug.utils import secure_filename
import wave
import urllib.request


crud = Blueprint('crud', __name__)

def get_samplerate(audio_url):
    # w = wave.open(file,'r')
    # framerate = w.getframerate()
    data = urllib.request.urlopen(audio_url)
    w = wave.open(data,'r')
    frame_rate = w.getframerate()
    file_extension = audio_url.split(".")[-1]
    return frame_rate, file_extension


def upload_audio_file(file):
    """
    Upload the user-uploaded file to Google Cloud Storage and retrieve its
    publicly-accessible URL.
    """
    if not file:
        return None

    public_url = storage.upload_file(
        file.read(),
        file.filename,
        file.content_type
    )

    current_app.logger.info(
        "Uploaded file %s as %s.", file.filename, public_url)

    return public_url

@crud.route("/")
def list():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    audios, next_page_token = get_model().list(kind='Audio',cursor=token)

    return render_template(
        "home.html",
        audios=audios,
        next_page_token=next_page_token)

@crud.route("/dashboard")
def dashboard():
    return render_template('dashboard.html')


@crud.route("/audios")
def list_audio():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    audios, next_page_token = get_model().list(kind='Audio',cursor=token)
    # books, next_page_token = get_model().list(kind='Book',cursor=token)

    return render_template(
        "list.html",
        # books=books,
        audios=audios,
        next_page_token=next_page_token)


@crud.route("/mine")
@oauth2.required
def list_mine():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    audios, next_page_token = get_model().list_by_user(
        user_id=session['profile']['id'],
        kind='Audio',
        cursor=token)

    return render_template(
        "list.html",
        audios=audios,
        next_page_token=next_page_token)


@crud.route('/<id>')
def view(id):
    book = get_model().read(id)
    return render_template("view.html", book=book)

@crud.route('/audio/<id>')
def view_audio(id):
    audio = get_model().read_audio(id)
    entidades = "None"
    # entidades = json.loads(json.dumps(audio['entidades']))
    if audio['entidades']:
        cadena = audio['entidades']
        cadena_tratada = cadena.replace("'","\"")
        entidades = json.loads(cadena_tratada)

    return render_template("view_audio.html", audio=audio, entidades=entidades)


# Arreglo 1
@crud.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        # If an image was uploaded, update the data to point to the new image.
        image_url = upload_image_file(request.files.get('image'))

        if image_url:
            data['imageUrl'] = image_url

        # If the user is logged in, associate their profile with the new book.
        if 'profile' in session:
            data['createdBy'] = session['profile']['displayName']
            data['createdById'] = session['profile']['id']

        book = get_model().create(data, kind='Book')

        return redirect(url_for('.view', id=book['id'], kind='Book'))

    return render_template("form.html", action="Add", book={})
# Arreglo 1 fin

@crud.route('/add_audio', methods=['GET', 'POST'])
def add_audio():
    if request.method == 'POST':
        data = request.form.to_dict(flat=True)


        # If an image was uploaded, update the data to point to the new image.
        audio_url = upload_audio_file(request.files.get('audiofile'))
        audio_framerate, audio_extension = get_samplerate(request.files.get(audio_url))

        data['framerate'] = request.files.get('frame_rate')
        data['fileEncoding'] = request.files.get('file_encoding')
        data['language'] = request.files.get('language')

        if audio_url:
            data['audioUrl'] = audio_url
        if audio_framerate:
            data['audioFrameRate'] = audio_framerate

        # If the user is logged in, associate their profile with the new book.
        if 'profile' in session:
            data['createdBy'] = session['profile']['displayName']
            data['createdById'] = session['profile']['id']

        audio = get_model().create(data, kind='Audio')

        return redirect(url_for('.view_audio', id=audio['id'],kind='Audio'))

    return render_template("upload_file.html", action="Add", audio={})
#
# @crud.route('/test', methods=['GET', 'POST'])
# def test():
#     return "post"

# arreglo 2
@crud.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    book = get_model().read(id)

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        image_url = upload_image_file(request.files.get('image'))

        if image_url:
            data['imageUrl'] = image_url

        book = get_model().update(data, id)

        return redirect(url_for('.view', id=book['id']))

    return render_template("form.html", action="Edit", book=book)

# arreglo 2 fin


@crud.route('/drop_audio', methods=['GET', 'POST'])
def upldfile():
    if request.method == 'POST':
        data = request.form.to_dict(flat=True)
        # files = request.files.getlist('file[]')
        files = request.files.getlist("file")

        # print("ACCACACACAACACACACAACACACAACACAACAC")
        # print(request.files.get('frame_rate'))
        # print(request.files.get('file_encoding'))
        # print(request.files)
        # print('request.method : %s',  request.method)
        # print('request.files : %s', request.files)
        # print('request.args : %s', request.args)
        # print('request.form : %s', request.form)
        # print('request.values : %s', request.values)
        # print('request.headers : %s', request.headers)
        # print('request.data : %s', request.data)
        for f in files:
            if f:
                # filename = secure_filename(f.filename)
                filename = f.filename
                audio_url = upload_audio_file(f)
                audio_framerate, audio_extension = get_samplerate(audio_url)

                if audio_extension:
                    if audio_extension.lower() == 'amr':
                        audio_enc = 'AMR'
                    elif audio_extension.lower() == 'fla':
                        audio_enc = 'FLAC'
                    else:
                        audio_enc = 'LINEAR16'

                if audio_framerate:
                    data['audioFrameRate'] = audio_framerate

                if audio_url:
                    data['audioUrl'] = audio_url
                    # If the user is logged in, associate their profile with the new book.
                    if 'profile' in session:
                        data['author'] = session['profile']['displayName']
                        data['createdBy'] = session['profile']['displayName']
                        data['createdById'] = session['profile']['id']
                    else:
                        data['author'] = 'user-no-logged'
                        data['createdBy'] = 'user-no-logged'
                        data['createdById'] = 'user-no-logged'


                    # data['framerate'] = request.files.get('frame_rate')
                    # data['fileEncoding'] = request.files.get('file_encoding')
                    # data['language'] = request.files.get('language')
                    data['framerate'] = audio_framerate
                    data['fileEncoding'] = audio_enc
                    data['language'] = 'es-ES'

                    # data['description'] = 'File uploaded and process automatically'
                    date = datetime.datetime.utcnow().strftime("%Y-%m-%d at %H%M%S")
                    data['publishedDate'] = date

                    audio = get_model().create(data, kind='Audio')
                    id = audio['id']

                    return str(id)
                    # return redirect(url_for('.view_audio', id=audio['id'],kind='Audio'))


    return render_template("upload_file.html", action="Add", audio={})

@crud.route('/<id>/edit_audio', methods=['GET', 'POST'])
def edit_audio(id):
    audio = get_model().read_audio(id)

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        audio_url = upload_audio_file(request.files.get('audiofile'))

        current_app.logger.info("Uploaded file as %s.", audio_url)

        if audio_url:
            data['audioUrl'] = audio_url
            current_app.logger.info("DATA audioUrl %s.", audio_url)

        audio = get_model().update(data,'Audio',id)

        return redirect(url_for('.view_audio', id=audio['id']))

    return render_template("upload_file.html", action="Edit", audio=audio)

@crud.route('/<id>/delete')
def delete(id):
    get_model().delete(id, kind='Audio')
    return redirect(url_for('.list'))
