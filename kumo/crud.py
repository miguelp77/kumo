import json
from kumo import get_model, oauth2, storage, format_date, format_datetime, \
    date_to_string, write_spreadsheet
from functools import update_wrapper

from flask import Blueprint, current_app, redirect, render_template, request, \
    session, url_for, jsonify
from datetime import datetime, date, timedelta
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

def get_role(role):
    print(role)
    r = 'No'
    try:
        if session['role']:
            r = session['role']
    except:
        r = 'no session'
    finally:
        return r
    # return session['role'] if session['role'] else None

# DECORADOR
def user_test_admin(req_roles = None):
    if req_roles is None:
        req_roles = ['any']
    # print('='*80)
    # print('DECORADOR')
    # print(req_roles)
    r = get_role(req_roles)
    # print(r)
    # render_template("home.html")
    # print(session)
    def decorator (f):
        def decorated_view(*args, **kwargs):
            # …
            r = get_role(req_roles)
            # print('r=' + r)
            if r == 'manager':
                return f(*args, **kwargs)
            else:
                return render_template('not_access.html')

        return decorated_view

    return decorator
# DECORADOR


# Calculo de horas
HOLIDAYS = {
    'h1': '2017-01-01',
    'h2': '2017-01-06',
    'h3': '2017-08-15'}

def is_holiday(date):
    print('eval holiday: ' + str(date))
    formated = date_to_string(date)

    print(str(formated) in HOLIDAYS.values())

    return str(formated) in HOLIDAYS.values()

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

def work_days(start_date, end_date_inc):
    dates = []
    for single_date in daterange(start_date, end_date_inc):
        weekno = single_date.weekday()
        if weekno<5 and not is_holiday(single_date):
            dates.append(single_date)
    return dates

def work_hours(start_date,end_date_inc):
    hours = 0
    for single_date in daterange(start_date, end_date_inc):
        # print(single_date.strftime("%d-%m-%Y"))
        weekno = single_date.weekday()
        
        if weekno<5 and not is_holiday(single_date):
            print("Weekday")
            hours = hours + 8
            print(hours)
    return hours



# Routing

@crud.route("/")
def list():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    allocations, next_page_token = get_model().list_all(kind='Allocation',cursor=token)

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
        if data['profile'] == '':
            data['profile'] == 'editor'
        user = get_model().create_user(data, kind='User')

        return redirect(url_for('.view_user', id=user['id'], kind='User'))

@crud.route('/user/<id>')
@oauth2.required
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
@user_test_admin(req_roles=['manaager'])
def list_user():
    print('KK')
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')
    users, next_page_token = get_model().list_user(kind='User',cursor=token)

    return render_template(
        "list_user.html",
        # books=books,
        users=users,
        next_page_token=next_page_token)

# Imputaciones
@crud.route("/allocations")
# @user_test_admin(req_roles=['manaager'])
def list_allocations():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    allocations, next_page_token = get_model().list_all(kind='Allocation',cursor=token)

    # books, next_page_token = get_model().list(kind='Book',cursor=token)
    return render_template(
        "list.html",
        # books=books,
        allocations=allocations,
        next_page_token=next_page_token)

@crud.route("/allocations/<email>")
# @user_test_admin(req_roles=['manaager'])
def user_allocations(email):
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    allocations, next_page_token = get_model().list_all(kind='Allocation',cursor=token,email=email)

    # books, next_page_token = get_model().list(kind='Book',cursor=token)
    return render_template(
        "list.html",
        # books=books,
        allocations=allocations,
        next_page_token=next_page_token)

@crud.route("/my_projects")
@oauth2.required
def my_projects():
    print(get_model().give_me_name(5664248772427776	,'Project'))
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    projects, next_page_token = get_model().check_projects(
        user_email=session['profile']['emails'][0]['value'],
        kind='Project',cursor=token)
    print(projects)
    # books, next_page_token = get_model().list(kind='Book',cursor=token)
    return render_template(
        "list_projects.html",
        # books=books,
        projects=projects,
        next_page_token=next_page_token)

@crud.route("/all_projects")
@oauth2.required
def all_projects():
    print(get_model().give_me_name(5664248772427776	,'Project'))
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    projects, next_page_token = get_model().check_projects(
        user_email=None,
        kind='Project',cursor=token)
    print(projects)
    # books, next_page_token = get_model().list(kind='Book',cursor=token)
    return render_template(
        "list_projects.html",
        # books=books,
        projects=projects,
        next_page_token=next_page_token)

@crud.route("/view_project/<id>/")
@oauth2.required
def view_project(id):
    # print(get_model().give_me_name(5664248772427776	,'Project'))
    project = get_model().read_project(id)
    return render_template(
        "view_project.html",
        project=project)

@crud.route("/update_project/<id>/")
@oauth2.required
def update_project(id):
    # print(get_model().give_me_name(5664248772427776	,'Project'))
    project, submit_hours, accept_hours = get_model().collect_project_hours(id)

    return render_template(
        "view_project.html",
        project=project)

@crud.route("/mine")
@oauth2.required
def list_mine():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')
    total_hours = {}
    allocations, next_page_token, dates = get_model().list_by_user(
        user_id=session['profile']['id'],
        limit=50,
        kind='Allocation',
        cursor=token)

    for allocs in allocations:
        s = allocs['status']
        if s in total_hours:
            total_hours[s] = int(total_hours[s]) + int(allocs['hours'])
        else:
            total_hours[s] = int(allocs['hours'])

        print(total_hours)
        # if allocs['status'] == 'created':
        #     total_hours.created = total_hours.created + int(allocs['hours']) 
    # write_spreadsheet('ooo')
    logged_user = session['profile']['emails'][0]['value']

    return render_template(
        "list.html",
        allocations=allocations,
        total_hours=total_hours,
        logged_user=logged_user,
        dates=dates,
        next_page_token=next_page_token)

@crud.route("/<year>/<month>/mine")
@oauth2.required
def list_mine_date(year,month):
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')
    total_hours = {}
    allocations, next_page_token, dates = get_model().list_by_month(
        user_id=session['profile']['id'],
        kind='Allocation',
        year=year,
        month=month,
        cursor=token)

    for allocs in allocations:
        s = allocs['status']
        if s in total_hours:
            total_hours[s] = int(total_hours[s]) + int(allocs['hours'])
        else:
            total_hours[s] = int(allocs['hours'])

        print(total_hours)
        # if allocs['status'] == 'created':
        #     total_hours.created = total_hours.created + int(allocs['hours']) 
    # write_spreadsheet('ooo')
    logged_user = session['profile']['emails'][0]['value']

    return render_template(
        "list.html",
        allocations=allocations,
        total_hours=total_hours,
        logged_user=logged_user,
        dates=dates,
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
    logged_user = session['profile']['emails'][0]['value']

    # for allocs in allocations:
    #     if allocs['status'] == 'created':
    #         total_hours = total_hours + int(allocs['hours']) 
    # write_spreadsheet('ooo')

    return render_template(
        "review_allocations.html",
        allocations=allocations,
        logged_user=logged_user,
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

        data['datetime_start'] = format_datetime(data['start_date'])
        data['datetime_end'] = format_datetime(data['end_date'])
        data['project_name'] = get_model().give_me_name(data['project'],'Project')

        if 'profile' in session:
            data['createdBy'] = session['profile']['displayName']
            data['createdById'] = session['profile']['id']

        if int(data['hours']) > 8:
            # listamos el numero de jornadas
            dates = work_days(data['datetime_start'],data['datetime_end']+ timedelta(days=1))
            for workday in dates:
                data['formated_start_date'] = date_to_string(workday,reverse=True)
                data['formated_end_date'] = date_to_string(workday,reverse=True)
                data['datetime_start'] = workday
                data['hours'] = 8
                allocation = get_model().create(data, kind='Allocation')
        else:
            allocation = get_model().create(data, kind='Allocation')

        # return redirect(url_for('.view_allocation', id=allocation['id'],kind='Allocation'))
        return redirect(url_for('.list_mine'))

    return render_template("create_allocation.html", action="Crear",projects=projects, allocation={})

@crud.route('/edit_allocation/<id>', methods=['GET', 'POST'])
def edit_allocation(id):
    projects, next_page_token2 = get_model().list_projects(50,'Project',None)
    allocation = get_model().read_allocation(id)

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        if not 'project' in data:
            data['project'] = allocation['project']
        if not 'createdBy' in data:
            data['createdBy'] = allocation['createdBy']
        if not 'createdById' in data:
            data['createdById'] = allocation['createdById']
        if not 'approver' in data:
            data['approver'] = allocation['approver']
        
        data['formated_start_date'] = format_date(data['start_date'])
        data['formated_end_date'] = format_date(data['end_date'])

        data['datetime_start'] = format_datetime(data['start_date'])
        data['datetime_end'] = format_datetime(data['end_date'])
        data['project_name'] = get_model().give_me_name(data['project'],'Project')

        if 'profile' in session:
            data['editedBy'] = session['profile']['displayName']
            data['editedById'] = session['profile']['id']

        if int(data['hours']) > 8:
            # listamos el numero de jornadas
            dates = work_days(data['datetime_start'],data['datetime_end']+ timedelta(days=1))
            for workday in dates:
                data['formated_start_date'] = date_to_string(workday,reverse=True)
                data['formated_end_date'] = date_to_string(workday,reverse=True)
                data['datetime_start'] = workday
                data['hours'] = 8
                allocation = get_model().create(data, kind='Allocation', id=id)
        else:
            allocation = get_model().create(data, kind='Allocation', id=id)

        # return redirect(url_for('.view_allocation', id=allocation['id'],kind='Allocation'))
        return redirect(url_for('.list_mine'))

    return render_template("create_allocation.html", action="Editar",projects=projects,allocation=allocation)

#
# @crud.route('/test', methods=['GET', 'POST'])
# def test():
#     return "post"

# arreglo 2
@crud.route('/edit/<id>/', methods=['GET', 'POST'])
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
@crud.route('/submit/<id>/', methods=['GET', 'POST'])
def submited(id):
    allocation = get_model().read_allocation(id)
    allocation['status'] = 'submit'
    allocation = get_model().update_allocation(data=allocation, kind='Allocation', id=id)
    # return render_template("list.html", allocation=allocation)
    return redirect(url_for('.list_mine'))

@crud.route('/accept/<id>/', methods=['GET', 'POST'])
def accepted(id):
    allocation = get_model().read_allocation(id)
    allocation['status'] = 'accepted'
    allocation = get_model().update_allocation(data=allocation, kind='Allocation', id=id)
    # return render_template("list.html", allocation=allocation)
    # return render_template(
    #     "list.html",
    #     allocations=allocation)
    return redirect(url_for('.review_allocations'))

@crud.route('/reject/<id>/', methods=['GET', 'POST'])
def rejected(id):
    allocation = get_model().read_allocation(id)
    allocation['status'] = 'rejected'
    allocation = get_model().update_allocation(data=allocation, kind='Allocation', id=id)
    # return render_template("list.html", allocation=allocation)
    # return render_template(
    #     "list.html",
    #     allocations=allocation)
    return redirect(url_for('.review_allocations'))

# Prjects
# ./{{pj.id}}/update_pj_hours

@crud.route('/<id>/update_pj_hours', methods=['GET', 'POST'])
def update_pj_hours(id):
    """
    This function read all allocations for the project
    and update the number of hours consumed
    """
    project = get_model().read_project(id)

    allocation['status'] = 'rejected'
    allocation = get_model().update_allocation(data=allocation, kind='Allocation', id=id)
    return render_template("upload_file.html", action="Add", audio={},projects=projects)


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

@crud.route('/delete/<id>/')
def delete(id):
    get_model().delete(id, kind='Allocation')
    return redirect(url_for('.list_mine'))


@crud.route('/_delete_selection')
def delete_selection():
    if request.method == 'GET':
        data = eval(request.args.get('ids'))
        get_model().delete_multi(data)
    return jsonify('DELEETED')

@crud.route('/_submit_selection')
def submit_selection():
    if request.method == 'GET':
        data = eval(request.args.get('ids'))
        for id in data:
            submited(id)
    return jsonify('submit')

@crud.route('/_reject_selection')
def reject_selection():
    if request.method == 'GET':
        data = eval(request.args.get('ids'))
        for id in data:
            rejected(id)
    return jsonify('reject')

@crud.route('/_approve_selection')
def approve_selection():
    if request.method == 'GET':
        data = eval(request.args.get('ids'))
        for id in data:
            accepted(id)
    return jsonify('approve')

