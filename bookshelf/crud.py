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


crud = Blueprint('crud', __name__)


def upload_image_file(file):
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

    books, next_page_token = get_model().list(kind='Book',cursor=token)

    return render_template(
        "list.html",
        books=books,
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

        return redirect(url_for('.view', id=audio['id'],kind='Audio'))

    return render_template("upload_file.html", action="Add", audio={})


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
    get_model().delete(id, kind='Book')
    return redirect(url_for('.list'))
