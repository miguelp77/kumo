import json
from kumo import get_model, oauth2, storage, format_date, format_datetime, \
    date_to_string, write_spreadsheet
from functools import update_wrapper

from flask import Blueprint, current_app, redirect, render_template, request, \
    session, url_for, jsonify, Response
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
import urllib.request
from collections import defaultdict
from functools import wraps



crud = Blueprint('crud', __name__)

def getCSV(datos):
    # with open("outputs/Adjacency.csv") as fp:
    #     csv = fp.read()
    print(datos)
    csv = '1,2,3\n4,5,6\n'
    return Response(csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename=" + datos +".csv"})

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
# def user_test_admin(req_roles = None):
#     if req_roles is None:
#         req_roles = ['any']
#     # print('='*80)
#     # print('DECORADOR')
#     # print(req_roles)
#     r = get_role(req_roles)
#     # print(r)
#     # render_template("home.html")
#     # print(session)
#     def decorator (f):
#         def decorated_view(*args, **kwargs):
#             # …
#             r = get_role(req_roles)
#             # print('r=' + r)
#             if r == 'manager':
#                 return f(*args, **kwargs)
#             else:
#                 return render_template('not_access.html')

#         return decorated_view

#     return decorator
def user_test_admin(req_roles = 'None'):
    def decorator (func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            email=session['profile']['emails'][0]['value']
            auth_role = get_model().get_profile(email)
            if str(req_roles) == str(auth_role) or 'su' == str(auth_role):
                return func(*args, **kwargs)
            else:
                return render_template('not_access.html')
        return decorated_view
    return decorator
# DECORADOR


# Calculo de horas
HOLIDAYS = {
    'h1': '2017-01-06',
    'h2': '2017-03-20',
    'h3': '2017-04-13',
    'h4': '2017-04-14',
    'h5': '2017-05-01',
    'h6': '2017-05-02',
    'h7': '2017-05-15',
    'h8': '2017-08-15',
    'h9': '2017-10-12',
    'h10': '2017-11-01',
    'h11': '2017-11-09',
    'h12': '2017-12-06',
    'h13': '2017-12-08',
    'h14': '2017-12-25'}

def is_holiday(date):
    formated = date_to_string(date)
    print(str(formated) in HOLIDAYS.values())
    return str(formated) in HOLIDAYS.values()

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

def work_days(start_date, end_date_inc):
    """
    Split date range. Exception for Weekends
    """
    dates = []
    if start_date.weekday() >= 5:
        # Imputacion de fin de semana
        for single_date in daterange(start_date, end_date_inc):
            dates.append(single_date)
        return dates    
    for single_date in daterange(start_date, end_date_inc):
        weekno = single_date.weekday()
        if weekno < 5 and not is_holiday(single_date):
            dates.append(single_date)
    return dates

def work_hours(start_date,end_date_inc):
    hours = 0
    for single_date in daterange(start_date, end_date_inc):
        # print(single_date.strftime("%d-%m-%Y"))
        weekno = single_date.weekday()
        if weekno<5 and not is_holiday(single_date):
            hours = hours + 8
    return hours

# Routing
@crud.route("/")
def showHome():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    allocations, next_page_token = get_model().list_all(kind='Allocation',cursor=token)

    return render_template(
        "home.html",
        allocations=allocations,
        next_page_token=next_page_token)

@crud.route("/user", methods=['GET', 'POST'])
@oauth2.required
@user_test_admin(req_roles='manager')
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
@user_test_admin(req_roles='manager')
def view_user(id):
    """
    View details
    """
    user = get_model().read_user(id)
    return render_template("view_user.html", user=user)

# arreglo 2
@crud.route('/user/<id>/edit_user', methods=['GET', 'POST'])
@oauth2.required
@user_test_admin(req_roles='manager')
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
@oauth2.required
@user_test_admin(req_roles='manager')
def list_user():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')
    users, next_page_token = get_model().list_user(kind='User',cursor=token)

    return render_template(
        "list_user.html",
        users=users,
        next_page_token=next_page_token)

# Imputaciones
@crud.route("/allocations")
@oauth2.required
@user_test_admin(req_roles='manager')
def list_allocations():
    token = request.args.get('page_token', None)
    day = request.args.get('date', None)
    month = request.args.get('month', None)
    year = request.args.get('year', None)
    project = request.args.get('project', None)
    hours = request.args.get('hours', None)
    status = request.args.get('status', None)
    email = request.args.get('user_email', None)
    csv = request.args.get('csv', None)


    if token:
        token = token.encode('utf-8')
    allocations, next_page_token = get_model().list_all(kind='Allocation',cursor=token, email=email,
         day=day, month=month, year=year, project=project, hours=hours, status=status)

    total_hours = {}
    for allocs in allocations:
        s = allocs['status']
        if s in total_hours:
            total_hours[s] = int(total_hours[s]) + int(allocs['hours'])
        else:
            total_hours[s] = int(allocs['hours'])

    print(total_hours)

    if csv:
        datos = []   
        for a in allocations:
            linea = str(a['year']) + ',' + \
                str(a['month']) + ',' + \
                str(a['formated_start_date']) + ',' + \
                str(a['createdBy']) + ',' + \
                str(a['hours']) + ',' + \
                str(a['project_name']) + ',' + \
                str(a['status']) + ',' + \
                str(a['approver']) + '\n'
            datos.append(linea)

        return Response(list(datos),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=" + csv +".csv"}
            )

    return render_template(
        "list_all.html",
        allocations=allocations,
        day = day,
        month = month,
        year=year,
        project=project,
        hours=hours,
        status=status,
        user_email=email,
        total_hours=total_hours,
        next_page_token=next_page_token)


@crud.route("/dirfin")
@oauth2.required
@user_test_admin(req_roles='manager')
def csv_allocations():
    token = request.args.get('page_token', None)
    day = request.args.get('date', None)
    month = request.args.get('month', None)
    year = request.args.get('year', None)
    project = request.args.get('project', None)
    hours = request.args.get('hours', None)
    status = request.args.get('status', None)
    csv = request.args.get('csv', None)

    if token:
        token = token.encode('utf-8')
    allocations, next_page_token = get_model().list_all(kind='Allocation',cursor=token,
         day=day, month=month, year=year, project=project, hours=hours, status=status)

    total_hours = {}
    for allocs in allocations:
        s = allocs['status']
        if s in total_hours:
            total_hours[s] = int(total_hours[s]) + int(allocs['hours'])
        else:
            total_hours[s] = int(allocs['hours'])

        # print(total_hours)

    if csv:
        datos = []   
        for a in allocations:
            linea = str(a['year']) + ',' + \
                str(a['month']) + ',' + \
                str(a['formated_start_date']) + ',' + \
                str(a['createdBy']) + ',' + \
                str(a['hours']) + ',' + \
                str(a['project_name']) + ',' + \
                str(a['status']) + ',' + \
                str(a['approver']) + '\n'
            datos.append(linea)

        return Response(list(datos),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=" + csv +".csv"}
            )

    return render_template(
        "list_all.html",
        allocations=allocations,
        day = day,
        month = month,
        year=year,
        project=project,
        hours=hours,
        status=status,
        total_hours=total_hours,
        next_page_token=next_page_token)


@crud.route("/allocations/<email>")
@oauth2.required
@user_test_admin(req_roles='manager')
def user_allocations(email):
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    day = request.args.get('date', None)
    month = request.args.get('month', None)
    year = request.args.get('year', None)
    project = request.args.get('project', None)
    hours = request.args.get('hours', None)
    status = request.args.get('status', None)

    allocations, next_page_token = get_model().list_all(kind='Allocation',cursor=token,email=email,
        day=day, month=month, year=year, project=project, hours=hours, status=status)

    start_dates = defaultdict(list)
    for allocation in allocations:
        start_date = allocation['datetime_start']
        hour = allocation['hours']
        start_dates[str(start_date.timestamp()*1000)].append(int(hour))


    return render_template(
        "list_by_user.html",
        # books=books,
        allocations=allocations,
        start_dates=start_dates,
        next_page_token=next_page_token)



@crud.route("/my_projects")
@oauth2.required
@user_test_admin(req_roles='manager')
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
@user_test_admin(req_roles='su')
def all_projects():
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
@user_test_admin(req_roles='manager')
def view_project(id):
    # print(get_model().give_me_name(5664248772427776	,'Project'))
    project = get_model().read_project(id)
    return render_template(
        "view_project.html",
        project=project)

@crud.route("/update_project/<id>/")
@oauth2.required
@user_test_admin(req_roles='manager')
def update_project(id):
    project, submit_hours, accept_hours = get_model().collect_project_hours(id)
    return render_template(
        "view_project.html",
        project=project)

@crud.route("/mine")
@oauth2.required
def list_mine():
    token = request.args.get('page_token', None)
    day = request.args.get('date', None)
    month = request.args.get('month', None)
    year = request.args.get('year', None)
    project = request.args.get('project', None)
    hours = request.args.get('hours', None)
    status = request.args.get('status', None)
    
    if token:
        token = token.encode('utf-8')
    total_hours = {}
    
    allocations, next_page_token, dates = get_model().list_by_user(
        user_id=session['profile']['id'],
        day = day,
        month = month,
        year=year,
        project=project,
        hours=hours,
        status=status,
        limit=100,
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
        day=day,
        month=month,
        year=year,
        hours=hours,
        project=project,
        status=status,
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
@user_test_admin(req_roles='manager')
def review_allocations():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')
    allocations, next_page_token = get_model().assigned_to_me(
        user_email=session['profile']['emails'][0]['value'],
        kind='Allocation',
        cursor=token)
    logged_user = session['profile']['emails'][0]['value']

    return render_template(
        "review_allocations.html",
        allocations=allocations,
        logged_user=logged_user,
        next_page_token=next_page_token)

@crud.route("/as/<email>/check_allocations")
@oauth2.required
@user_test_admin(req_roles='su')
def review_allocations_as_other(email):
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')
    if not email:
        email = session['profile']['emails'][0]['value']
    allocations, next_page_token = get_model().assigned_to_me(
        user_email=email,
        kind='Allocation',
        cursor=token)

    return render_template(
        "review_allocations.html",
        allocations=allocations,
        logged_user=email,
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
@oauth2.required
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
@oauth2.required
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
@oauth2.required
def edit_allocation(id):
    projects, next_page_token2 = get_model().list_projects(50,'Project',None)
    allocation = get_model().read_allocation(id)

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)
        data['user_id'] = allocation['user_id']
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
@oauth2.required
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
@oauth2.required
def submited(id):
    allocation = get_model().read_allocation(id)
    allocation['status'] = 'submit'
    allocation = get_model().update_allocation(data=allocation, kind='Allocation', id=id)
    # return render_template("list.html", allocation=allocation)
    return redirect(url_for('.list_mine'))

@crud.route('/accept/<id>/', methods=['GET', 'POST'])
@oauth2.required
@user_test_admin(req_roles='manager')
def accepted(id):
    allocation = get_model().read_allocation(id)
    allocation['status'] = 'accepted'
    allocation = get_model().update_allocation(data=allocation, kind='Allocation', id=id)
    return redirect(url_for('.review_allocations'))

@crud.route('/reject/<id>/', methods=['GET', 'POST'])
@oauth2.required
@user_test_admin(req_roles='manager')
def rejected(id):
    allocation = get_model().read_allocation(id)
    allocation['status'] = 'rejected'
    allocation = get_model().update_allocation(data=allocation, kind='Allocation', id=id)

    return redirect(url_for('.review_allocations'))

# Prjects
# ./{{pj.id}}/update_pj_hours

@crud.route('/<id>/update_pj_hours', methods=['GET', 'POST'])
@oauth2.required
@user_test_admin(req_roles='manager')
def update_pj_hours(id):
    """
    This function read all allocations for the project
    and update the number of hours consumed
    """
    project = get_model().read_project(id)

    allocation['status'] = 'rejected'
    allocation = get_model().update_allocation(data=allocation, kind='Allocation', id=id)
    return render_template("upload_file.html", action="Add", audio={},projects=projects)

@crud.route('/delete/<id>/')
@oauth2.required
def delete(id):
    get_model().delete(id, kind='Allocation')
    return redirect(url_for('.list_mine'))


@crud.route('/_delete_selection')
@oauth2.required
def delete_selection():
    if request.method == 'GET':
        data = eval(request.args.get('ids'))
        get_model().delete_multi(data)
    return jsonify('DELEETED')

@crud.route('/_submit_selection')
@oauth2.required
def submit_selection():
    if request.method == 'GET':
        data = eval(request.args.get('ids'))
        for id in data:
            submited(id)
    return jsonify('submit')

@crud.route('/_reject_selection')
@oauth2.required
def reject_selection():
    if request.method == 'GET':
        data = eval(request.args.get('ids'))
        for id in data:
            rejected(id)
    return jsonify('reject')

@crud.route('/_approve_selection')
@oauth2.required
def approve_selection():
    if request.method == 'GET':
        data = eval(request.args.get('ids'))
        for id in data:
            accepted(id)
    return jsonify('approve')

# @crud.route('/_cleandb')
# @oauth2.required
# def cleandb():
#     if request.method == 'GET':
#         # newdata = ['Normal']
#         newdata = 'Normal'
#         field = 'hours_type'
#         res = get_model().set_value(kind='Allocation', field=field, newdata=newdata)

#     return jsonify('clean')


@crud.route('/roadmap')
def roadmap():
    next_release = [
        {'v.0.0.1':'Init','Release':'31-08-2017'},
        {'v.0.0.2':'Current, some issues has been fixed.',
            'Release':'04-09-2017',
            'Details':' /allocations can download CSV. Project manager can review and view a calendar by user.'
        },
        {'v.0.0.3':'Hora inicio, Hora Fin','ETA':'TBD'}
        ]
    return jsonify(next_release)