from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from datetime import datetime, timedelta, date

app = Flask(__name__)
api = Api(app)

ALLOCS = {
    'alloc1': 
        {'email': 'demo@demo.com',
        'startDate': '01-01-2017',
        'endDate': '14-01-2017',
        'project': 'demoProject',
        'approval': 'dApproval',
        'status': 'dStatus'},
    'todo2': {'task': '?????'},
    'todo3': {'task': 'profit!'},
}

HOLIDAYS = {
    'h1': '2017-01-01',
    'h2': '2017-02-02',
    'h3': '2017-01-03'}

def is_holiday(date):
    return str(date) in HOLIDAYS.values()

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)


def work_hours(start_date,end_date_inc):
    hours = 0
    for single_date in daterange(start_date, end_date_inc):
        # print(single_date.strftime("%d-%m-%Y"))
        weekno = single_date.weekday()
        
        if weekno<5 and not is_holiday(single_date):
            print("Weekday")
            hours = hours + 8

    return hours

def abort_if_allocation_doesnt_exist(allocation_id):
    if allocation_id not in ALLOCS:
        abort(404, message="Todo {} doesn't exist".format(allocation_id))

parser = reqparse.RequestParser()
parser.add_argument('task')

# Todo
# shows a single todo item and lets you delete a todo item
class Todo(Resource):
    def get(self, allocation_id):
        abort_if_allocation_doesnt_exist(allocation_id)
        # transform strings to date
        start_date = datetime.strptime(ALLOCS[allocation_id]['startDate'], '%d-%m-%Y').date()
        end_date = datetime.strptime(ALLOCS[allocation_id]['endDate'], '%d-%m-%Y').date()
        end_date_inc = end_date + timedelta(days=1)
        hours = work_hours(start_date,end_date_inc)
        # return str(hours)
        return ALLOCS[allocation_id] 

    def delete(self, allocation_id):
        abort_if_allocation_doesnt_exist(allocation_id)
        del ALLOCS[allocation_id]
        return '', 204

    def put(self, allocation_id):
        args = parser.parse_args()
        task = {'task': args['task']}
        ALLOCS[allocation_id] = task
        return task, 201


# TodoList
# shows a list of all ALLOCS, and lets you POST to add new tasks
class TodoList(Resource):
    def get(self):
        return ALLOCS

    def post(self):
        args = parser.parse_args()
        allocation_id = int(max(ALLOCS.keys()).lstrip('todo')) + 1
        allocation_id = 'todo%i' % allocation_id
        ALLOCS[allocation_id] = {'task': args['task']}
        return ALLOCS[allocation_id], 201

##
## Actually setup the Api resource routing here
##
api.add_resource(TodoList, '/todos')
api.add_resource(Todo, '/todos/<allocation_id>')


if __name__ == '__main__':
    app.run(debug=True)