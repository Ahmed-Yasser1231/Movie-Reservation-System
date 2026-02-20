from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from config import Config
from models import db, Movie, Genre, Theater, Seat, Showtime

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)


# ==================== GENRE ENDPOINTS ====================

@app.route('/genres', methods=['GET'])
def get_genres():
    genres = Genre.query.all()
    return jsonify([{'genre_id': g.genre_id, 'name': g.name} for g in genres]), 200

@app.route('/genres', methods=['POST'])
@jwt_required()
def create_genre():
    claims = get_jwt()
    if claims.get('role') != 'ADMIN':
        return jsonify({'message': 'Admin access required'}), 403
    data = request.get_json()
    genre = Genre(name=data['name'])
    db.session.add(genre)
    db.session.commit()
    return jsonify({'message': 'Genre created', 'genre_id': genre.genre_id}), 201


# ==================== MOVIE ENDPOINTS ====================

@app.route('/movies', methods=['GET'])
def get_movies():
    movies = Movie.query.all()
    result = []
    for movie in movies:
        result.append({
            'movie_id': movie.movie_id,
            'title': movie.title,
            'description': movie.description,
            'poster_url': movie.poster_url,
            'genres': [{'genre_id': g.genre_id, 'name': g.name} for g in movie.genres],
            'showtimes': [{
                'showtime_id': st.showtime_id,
                'start_time': st.start_time.isoformat(),
                'price': float(st.price),
                'theater_name': st.theater.name
            } for st in movie.showtimes]
        })
    return jsonify(result), 200

@app.route('/movies/<int:movie_id>', methods=['GET'])
def get_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    return jsonify({
        'movie_id': movie.movie_id,
        'title': movie.title,
        'description': movie.description,
        'poster_url': movie.poster_url,
        'genres': [{'genre_id': g.genre_id, 'name': g.name} for g in movie.genres],
        'showtimes': [{
            'showtime_id': st.showtime_id,
            'start_time': st.start_time.isoformat(),
            'price': float(st.price),
            'theater_name': st.theater.name
        } for st in movie.showtimes]
    }), 200

@app.route('/movies', methods=['POST'])
@jwt_required()
def create_movie():
    print(f"DEBUG: Movie Service received request. Headers: {request.headers}")
    claims = get_jwt()
    if claims.get('role') != 'ADMIN':
        return jsonify({'message': 'Admin access required'}), 403

    data = request.get_json()
    new_movie = Movie(
        title=data['title'],
        description=data.get('description'),
        poster_url=data.get('poster_url')
    )
    if data.get('genre_ids'):
        genres = Genre.query.filter(Genre.genre_id.in_(data['genre_ids'])).all()
        new_movie.genres.extend(genres)

    db.session.add(new_movie)
    db.session.commit()
    return jsonify({'message': 'Movie created', 'movie_id': new_movie.movie_id}), 201

@app.route('/movies/<int:movie_id>', methods=['PUT'])
@jwt_required()
def update_movie(movie_id):
    claims = get_jwt()
    if claims.get('role') != 'ADMIN':
        return jsonify({'message': 'Admin access required'}), 403

    movie = Movie.query.get_or_404(movie_id)
    data = request.get_json()
    movie.title = data.get('title', movie.title)
    movie.description = data.get('description', movie.description)
    movie.poster_url = data.get('poster_url', movie.poster_url)

    if 'genre_ids' in data:
        movie.genres = Genre.query.filter(Genre.genre_id.in_(data['genre_ids'])).all()

    db.session.commit()
    return jsonify({'message': 'Movie updated'}), 200

@app.route('/movies/<int:movie_id>', methods=['DELETE'])
@jwt_required()
def delete_movie(movie_id):
    claims = get_jwt()
    if claims.get('role') != 'ADMIN':
        return jsonify({'message': 'Admin access required'}), 403

    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return jsonify({'message': 'Movie deleted'}), 200


# ==================== THEATER ENDPOINTS ====================

@app.route('/theaters', methods=['GET'])
def get_theaters():
    theaters = Theater.query.all()
    result = []
    for t in theaters:
        result.append({
            'theater_id': t.theater_id,
            'name': t.name,
            'total_seats': t.total_seats,
            'seats': [{'seat_id': s.seat_id, 'row_label': s.row_label, 'seat_number': s.seat_number} for s in t.seats]
        })
    return jsonify(result), 200

@app.route('/theaters', methods=['POST'])
@jwt_required()
def create_theater():
    claims = get_jwt()
    if claims.get('role') != 'ADMIN':
        return jsonify({'message': 'Admin access required'}), 403

    data = request.get_json()
    theater = Theater(name=data['name'], total_seats=data['total_seats'])
    db.session.add(theater)
    db.session.flush()

    # Auto-generate seats if rows and seats_per_row provided
    if data.get('rows') and data.get('seats_per_row'):
        rows = data['rows']  # e.g. ['A', 'B', 'C']
        seats_per_row = data['seats_per_row']
        for row in rows:
            for num in range(1, seats_per_row + 1):
                seat = Seat(theater_id=theater.theater_id, row_label=row, seat_number=num)
                db.session.add(seat)

    db.session.commit()
    return jsonify({'message': 'Theater created', 'theater_id': theater.theater_id}), 201


# ==================== SHOWTIME ENDPOINTS ====================

@app.route('/showtimes', methods=['GET'])
def get_showtimes():
    movie_id = request.args.get('movie_id')
    query = Showtime.query
    if movie_id:
        query = query.filter_by(movie_id=movie_id)

    showtimes = query.all()
    result = []
    for st in showtimes:
        result.append({
            'showtime_id': st.showtime_id,
            'movie_id': st.movie_id,
            'theater_id': st.theater_id,
            'start_time': st.start_time.isoformat(),
            'price': float(st.price),
            'theater_name': st.theater.name,
            'movie_title': st.movie.title
        })
    return jsonify(result), 200

@app.route('/showtimes/<int:showtime_id>/seats', methods=['GET'])
def get_showtime_seats(showtime_id):
    """Get all seats for a showtime's theater."""
    showtime = Showtime.query.get_or_404(showtime_id)
    seats = Seat.query.filter_by(theater_id=showtime.theater_id).all()
    return jsonify({
        'showtime_id': showtime.showtime_id,
        'theater_name': showtime.theater.name,
        'seats': [{'seat_id': s.seat_id, 'row_label': s.row_label, 'seat_number': s.seat_number} for s in seats]
    }), 200

@app.route('/showtimes', methods=['POST'])
@jwt_required()
def create_showtime():
    claims = get_jwt()
    if claims.get('role') != 'ADMIN':
        return jsonify({'message': 'Admin access required'}), 403

    data = request.get_json()
    showtime = Showtime(
        movie_id=data['movie_id'],
        theater_id=data['theater_id'],
        start_time=data['start_time'],
        price=data['price']
    )
    db.session.add(showtime)
    db.session.commit()
    return jsonify({'message': 'Showtime created', 'showtime_id': showtime.showtime_id}), 201

@app.route('/showtimes/<int:showtime_id>', methods=['DELETE'])
@jwt_required()
def delete_showtime(showtime_id):
    claims = get_jwt()
    if claims.get('role') != 'ADMIN':
        return jsonify({'message': 'Admin access required'}), 403

    showtime = Showtime.query.get_or_404(showtime_id)
    db.session.delete(showtime)
    db.session.commit()
    return jsonify({'message': 'Showtime deleted'}), 200


if __name__ == '__main__':
    app.run(port=5003, debug=True)
