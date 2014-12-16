import os
import threading
from flask import Flask, render_template as render, request, jsonify
from flask_peewee.db import Database
from peewee import *

THEME_PATH = os.path.join("default") + os.path.sep
API_VERSION = "v1.0"
DATABASE = {
    'name': 'pomodoros.db',
    'engine': 'peewee.SqliteDatabase',
}

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config.from_object(__name__)
db = Database(app)

### Decorator ###


def setInterval(interval):
    def decorator(function):
        def wrapper(*args, **kwargs):
            stopped = threading.Event()

            def loop():  # executed in another thread
                while not stopped.wait(interval): # until stopped
                    function(*args, **kwargs)

            t = threading.Thread(target=loop)
            t.daemon = True  # stop if the program exits
            t.start()
            return stopped
        return wrapper
    return decorator

### Models ###


class Pomodoros(db.Model):
    user = CharField()
    now = IntegerField(default=0)
    total = IntegerField(default=0)
    state = CharField(null=True)

try:
    Pomodoros.create_table()
except OperationalError:
    pass

### Views ###


@app.route('/')
def monitor():
    return render('%sindex.html' % THEME_PATH)


@app.route('/api/%s/put/pomodoro' % API_VERSION)
def put_pomodoro():
    try:
        user = request.args.get('user')
        now = request.args.get('now')
        total = request.args.get('total')
        state = request.args.get('state')

        # states; work, break, pause, stop
        pmdr = Pomodoros.get_or_create(user=user.lower())
        pmdr.now = now
        pmdr.total = total
        pmdr.state = state
        pmdr.save()
    except:
        return jsonify({'success': False})

    return jsonify({'success': True})


@app.route('/api/%s/get/pomodoros' % API_VERSION)
def get_pomodoros():
    return jsonify(Pomodoros.select().order_by(Pomodoros.user).dicts().get())


@setInterval(1)
def update_pomodoros():
    Pomodoros.update(
        now=Pomodoros.now + 1
    ).where(
        Pomodoros.now <= Pomodoros.total
    ).execute()

update_pomodoros()

if __name__ == '__main__':
    app.run(debug=True)

