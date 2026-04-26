from flask import Flask, render_template, redirect, url_for, request
import sqlite3
import os

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), 'database.db')


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    db = get_db()
    continents = db.execute('SELECT * FROM continents').fetchall()
    db.close()
    return render_template('index.html', continents=continents)


@app.route('/continent/<int:continent_id>')
def continent(continent_id):
    db = get_db()
    cont = db.execute('SELECT * FROM continents WHERE id = ?', (continent_id,)).fetchone()
    if not cont:
        return "Not found", 404

    destinations = db.execute(
        'SELECT * FROM destinations WHERE continent_id = ?', (continent_id,)
    ).fetchall()

    dest_data = []
    for dest in destinations:
        tours = db.execute(
            'SELECT * FROM tours WHERE destination_id = ?', (dest['id'],)
        ).fetchall()
        tours_with_stops = []
        for tour in tours:
            stops = db.execute(
                'SELECT stop_name FROM tour_stops WHERE tour_id = ?', (tour['id'],)
            ).fetchall()
            tours_with_stops.append({'tour': tour, 'stops': stops})
        dest_data.append({'dest': dest, 'tours': tours_with_stops})

    db.close()
    return render_template('continent.html', continent=cont, dest_data=dest_data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return redirect(url_for('index'))
    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)
