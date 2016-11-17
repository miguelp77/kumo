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

from bookshelf import get_model, oauth2, storage
from flask import Blueprint, current_app, redirect, render_template, request, \
    session, url_for
import datetime
from werkzeug.utils import secure_filename


crud = Blueprint('crud', __name__)

def samplerate(file):
    pass

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
    return render_template("view_audio.html", audio=audio)

@crud.route('/add_audio', methods=['GET', 'POST'])
def add_audio():
    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        # If an image was uploaded, update the data to point to the new image.
        audio_url = upload_audio_file(request.files.get('audiofile'))
        if audio_url:
            data['audioUrl'] = audio_url
        # If the user is logged in, associate their profile with the new book.
        if 'profile' in session:
            data['createdBy'] = session['profile']['displayName']
            data['createdById'] = session['profile']['id']

        audio = get_model().create(data, kind='Audio')

        return redirect(url_for('.view_audio', id=audio['id'],kind='Audio'))

    return render_template("upload_file.html", action="Add", audio={})

@crud.route('/test', methods=['GET', 'POST'])
def test():
    return "post"

@crud.route('/drop_audio', methods=['GET', 'POST'])
def upldfile():
    if request.method == 'POST':
        data = request.form.to_dict(flat=True)
        # files = request.files.getlist('file[]')
        files = request.files.getlist("file")

        # print('request.method : %s',  request.method)
        # print('request.files : %s', request.files)
        # print('request.args : %s', request.args)
        # print('request.form : %s', request.form)
        # print('request.values : %s', request.values)
        # print('request.headers : %s', request.headers)
        # print('request.data : %s', request.data)
        for f in files:
            print("***************")
            print(f)
            print("***************")
            if f:
                filename = secure_filename(f.filename)
                audio_url = upload_audio_file(f)
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

                    data['description'] = 'File uploaded and process automatically'
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
