import json
from kumo import get_model, oauth2, storage, format_date, write_spreadsheet
from flask import Blueprint, current_app, redirect, render_template, request, \
    session, url_for
from datetime import datetime, date
from werkzeug.utils import secure_filename
import urllib.request


crud = Blueprint('crud', __name__)


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

# Control de usuarios
# El perfil nos indica que opciones sobre los usuarios podemos realizar

def get_profile(user):
    ds = get_client()
    query = ds.query(kind='User')
    query.add_filter('email','=',user)
    results = iter(query.fetch(1))
    result = results.__next__()
    return result['profile']

# Decorador de control de usuarios
# def user_test_admin(f):
#     def helper(x):
#         if type(x) == int and x > 0:
#             return f(x)
#         else:
#             raise Exception("Argument is not an integer")
#     return helper

# Routing

@crud.route("/")
def list():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    allocations, next_page_token = get_model().list(kind='Allocation',cursor=token)

    return render_template(
        "home.html",
        allocations=allocations,
        next_page_token=next_page_token)

@crud.route("/user", methods=['GET', 'POST'])
def add_user():
    """
    Create an administrative user
    """
    if request.method == 'GET':
        return render_template('add_user.html',user={})
    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        user = get_model().create_user(data, kind='User')

        return redirect(url_for('.view_user', id=user['id'], kind='User'))

@crud.route('/user/<id>')
def view_user(id):
    """
    View details
    """
    user = get_model().read_user(id)
    return render_template("view_user.html", user=user)

# arreglo 2
@crud.route('/user/<id>/edit_user', methods=['GET', 'POST'])
def edit_user(id):
    """
    Update user
    """
    user = get_model().read_user(id)

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        user = get_model().update_user(data, 'User', id)

        return redirect(url_for('.view_user', id=user['id']))

    return render_template("add_user.html", action="Edit", user=user)

@crud.route('/user/list')
# @user_test_admin
def list_user():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    users, next_page_token = get_model().list_user(kind='User',cursor=token)

    return render_template(
        "list_user.html",
        # books=books,
        users=users,
        next_page_token=next_page_token)

# AUDIOS
@crud.route("/allocations")
def list_allocations():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    allocations, next_page_token = get_model().list(kind='Allocation',cursor=token)

    # books, next_page_token = get_model().list(kind='Book',cursor=token)
    return render_template(
        "list.html",
        # books=books,
        allocations=allocations,
        next_page_token=next_page_token)


@crud.route("/mine")
@oauth2.required
def list_mine():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')
    total_hours = 0
    allocations, next_page_token = get_model().list_by_user(
        user_id=session['profile']['id'],
        kind='Allocation',
        cursor=token)
    for allocs in allocations:
        if allocs['status'] == 'created':
            total_hours = total_hours + int(allocs['hours']) 
    # write_spreadsheet('ooo')

    return render_template(
        "list.html",
        allocations=allocations,
        total_hours=total_hours,
        next_page_token=next_page_token)

@crud.route("/check_allocations")
@oauth2.required
def review_allocations():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')
    allocations, next_page_token = get_model().assigned_to_me(
        user_email=session['profile']['emails'][0]['value'],
        kind='Allocation',
        cursor=token)

    # for allocs in allocations:
    #     if allocs['status'] == 'created':
    #         total_hours = total_hours + int(allocs['hours']) 
    # write_spreadsheet('ooo')

    return render_template(
        "list.html",
        allocations=allocations,
        next_page_token=next_page_token)

@crud.route('/<id>')
def view(id):
    allocation = get_model().read_allocation(id)
    entidades = json.loads(json.dumps(allocation))   
    return render_template("view_allocation.html", allocation=allocation, entidades=entidades)


@crud.route('/allocation/<id>')
def view_allocation(id):
    allocation = get_model().read_allocation(id)
    entidades = json.loads(json.dumps(allocation))   
    return render_template("view_allocation.html", allocation=allocation, entidades=entidades)


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

@crud.route('/add_allocation', methods=['GET', 'POST'])
def add_allocation():
    projects, next_page_token2 = get_model().list_projects(50,'Project',None)

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        data['formated_start_date'] = format_date(data['start_date'])
        data['formated_end_date'] = format_date(data['end_date'])

        # If an image was uploaded, update the data to point to the new image.
        # audio_url = upload_audio_file(request.files.get('audiofile'))
        

        # if audio_url:
        #     data['audioUrl'] = audio_url

        # If the user is logged in, associate their profile with the new book.
        if 'profile' in session:
            data['createdBy'] = session['profile']['displayName']
            data['createdById'] = session['profile']['id']

        allocation = get_model().create(data, kind='Allocation')

        # return redirect(url_for('.view_allocation', id=allocation['id'],kind='Allocation'))
        return redirect(url_for('.list_mine'))

    return render_template("upload_file.html", action="Add", audio={},projects=projects)
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
@crud.route('/<id>/submit', methods=['GET', 'POST'])
def submited(id):
    allocation = get_model().read_allocation(id)
    allocation['status'] = 'submit'
    allocation = get_model().update_allocation(data=allocation, kind='Allocation', id=id)
    # return render_template("list.html", allocation=allocation)
    return redirect(url_for('.list_mine'))

@crud.route('/<id>/accepted', methods=['GET', 'POST'])
def accepted(id):
    allocation = get_model().read_allocation(id)
    allocation['status'] = 'accepted'
    allocation = get_model().update_allocation(data=allocation, kind='Allocation', id=id)
    # return render_template("list.html", allocation=allocation)
    # return render_template(
    #     "list.html",
    #     allocations=allocation)
    return redirect(url_for('.review_allocations'))

@crud.route('/<id>/rejected', methods=['GET', 'POST'])
def rejected(id):
    allocation = get_model().read_allocation(id)
    allocation['status'] = 'rejected'
    allocation = get_model().update_allocation(data=allocation, kind='Allocation', id=id)
    # return render_template("list.html", allocation=allocation)
    # return render_template(
    #     "list.html",
    #     allocations=allocation)
    return redirect(url_for('.review_allocations'))


@crud.route('/drop_audio', methods=['GET', 'POST'])
def upldfile():
    if request.method == 'POST':
        data = request.form.to_dict(flat=True)
        # files = request.files.getlist('file[]')
        # files = request.files.getlist("audiofile")
        # files = request.files.get('audiofile')
        print("audio_url")
        audio_url = upload_audio_file(request.files.get('audiofile'))
        print(audio_url)

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
        # filename = files.filename
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

            data['framerate'] = audio_framerate
            data['fileEncoding'] = audio_enc
            data['language'] = request.values['language']

                    # data['description'] = 'File uploaded and process automatically'
            date = datetime.datetime.utcnow().strftime("%Y-%m-%d at %H%M%S")
            data['publishedDate'] = date

            audio = get_model().create(data, kind='Audio')
            id = audio['id']
            print("id=***************")
            print(request.values['language'])

            # return str(id)
            print("AI working")
            print("**********")
            audio_to_text(id)
            print("AI end")
            print("**********")

            return redirect(url_for('.view_audio', id=id,kind='Audio'))


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

# @crud.route('/<id>/delete')
# def delete(id):
#     get_model().delete(id, kind='Audio')
#     return redirect(url_for('.list'))

@crud.route('/<id>/delete')
def delete(id):
    get_model().delete(id, kind='Allocation')
    return redirect(url_for('.list_mine'))


