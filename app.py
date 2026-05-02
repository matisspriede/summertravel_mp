from flask import Flask, render_template, redirect, url_for, request, abort
import sqlite3
import os

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), 'database.db')


# ── DB helper ────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


# ── Routes ───────────────────────────────────────────────────────────────────

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
        abort(404)

    destinations = db.execute(
        'SELECT * FROM destinations WHERE continent_id = ?', (continent_id,)
    ).fetchall()

    dest_data = []
    for dest in destinations:
        tours = db.execute(
            'SELECT * FROM tours WHERE destination_id = ? AND continent_id IS NULL', (dest['id'],)
        ).fetchall()
        tours_with_stops = []
        for tour in tours:
            stops = db.execute(
                'SELECT stop_name FROM tour_stops WHERE tour_id = ?', (tour['id'],)
            ).fetchall()
            tours_with_stops.append({'tour': tour, 'stops': stops})
        dest_data.append({'dest': dest, 'tours': tours_with_stops})

    # Also fetch custom tours added via the form
    custom_tours = db.execute(
        'SELECT * FROM tours WHERE continent_id = ?', (continent_id,)
    ).fetchall()
    for tour in custom_tours:
        stops = db.execute(
            'SELECT stop_name FROM tour_stops WHERE tour_id = ?', (tour['id'],)
        ).fetchall()
        dest_data.append({
            'dest': {'name': tour['country'], 'image': tour['image'] or 'backgroung.jpg'},
            'tours': [{'tour': tour, 'stops': stops}]
        })

    db.close()
    return render_template('continent.html', continent=cont, dest_data=dest_data)

@app.route('/gallery')
def gallery():
    db = get_db()
    continents = db.execute('SELECT * FROM continents').fetchall()
    all_destinations = {}
    for c in continents:
        dests = db.execute(
            'SELECT * FROM destinations WHERE continent_id = ?', (c['id'],)
        ).fetchall()
        all_destinations[c['name']] = dests
    db.close()
    return render_template('gallery.html', all_destinations=all_destinations)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Placeholder — just redirect back home for now
        return redirect(url_for('index'))
    return render_template('login.html')


# ── CRUD: Tours ──────────────────────────────────────────────────────────────

@app.route('/tours')
def tours():
    db = get_db()
    rows = db.execute('''
        SELECT t.id, t.title, t.price, t.external_url,
               COALESCE(t.country, d.name) AS destination,
               COALESCE(c2.name, c1.name) AS continent
        FROM tours t
        LEFT JOIN destinations d ON t.destination_id = d.id AND t.continent_id IS NULL
        LEFT JOIN continents c1 ON d.continent_id = c1.id
        LEFT JOIN continents c2 ON t.continent_id = c2.id
        ORDER BY continent, destination
    ''').fetchall()
    db.close()
    return render_template('tours.html', tours=rows)


@app.route('/tours/add', methods=['GET', 'POST'])
def tour_add():
    db = get_db()
    if request.method == 'POST':
        title   = request.form['title'].strip()
        price   = request.form['price']
        url     = request.form['external_url'].strip()
        stops   = request.form['stops'].strip()
        if title and price:
            image = request.form['image'].strip()
            country = request.form['country'].strip()
            continent_id = request.form['continent_id']
            cur = db.execute(
                'INSERT INTO tours(destination_id,title,price,external_url,image,country,continent_id) VALUES(?,?,?,?,?,?,?)',
                (1, title, int(price), url, image, country, continent_id)
            )
            tour_id = cur.lastrowid
            for stop in [s.strip() for s in stops.split(',') if s.strip()]:
                db.execute('INSERT INTO tour_stops(tour_id,stop_name) VALUES(?,?)', (tour_id, stop))
            db.commit()
        db.close()
        return redirect(url_for('tours'))
    continents = db.execute('SELECT * FROM continents').fetchall()
    db.close()
    return render_template('tour_form.html', tour=None, continents=continents)


@app.route('/tours/<int:tour_id>/edit', methods=['GET', 'POST'])
def tour_edit(tour_id):
    db = get_db()
    tour = db.execute('SELECT * FROM tours WHERE id = ?', (tour_id,)).fetchone()
    if not tour:
        abort(404)
    if request.method == 'POST':
        dest_id = request.form.get('destination_id', 1)
        title   = request.form['title'].strip()
        price   = request.form['price']
        url     = request.form['external_url'].strip()
        stops   = request.form['stops'].strip()
        image = request.form['image'].strip()
        country = request.form['country'].strip()
        continent_id = request.form['continent_id']
        db.execute(
            'UPDATE tours SET title=?, price=?, external_url=?, image=?, country=?, continent_id=? WHERE id=?',
            (title, int(price), url, image, country, continent_id, tour_id)
        )
        db.execute('DELETE FROM tour_stops WHERE tour_id = ?', (tour_id,))
        for stop in [s.strip() for s in stops.split(',') if s.strip()]:
            db.execute('INSERT INTO tour_stops(tour_id,stop_name) VALUES(?,?)', (tour_id, stop))
        db.commit()
        db.close()
        return redirect(url_for('tours'))
    stops = db.execute('SELECT stop_name FROM tour_stops WHERE tour_id=?', (tour_id,)).fetchall()
    stops_str = ', '.join(r['stop_name'] for r in stops)
    image = tour['image'] or ''
    continents = db.execute('SELECT * FROM continents').fetchall()
    db.close()
    return render_template('tour_form.html', tour=tour, stops_str=stops_str, continents=continents)

@app.route('/tours/<int:tour_id>/delete', methods=['POST'])
def tour_delete(tour_id):
    db = get_db()
    db.execute('DELETE FROM tour_stops WHERE tour_id = ?', (tour_id,))
    db.execute('DELETE FROM tours WHERE id = ?', (tour_id,))
    db.commit()
    db.close()
    return redirect(url_for('tours'))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)