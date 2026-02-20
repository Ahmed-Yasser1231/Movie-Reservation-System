from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Association Table for Movie-Genre
movie_genres = db.Table('movie_genres',
    db.Column('movie_id', db.Integer, db.ForeignKey('movies.movie_id', ondelete='CASCADE'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.genre_id', ondelete='CASCADE'), primary_key=True)
)

class Genre(db.Model):
    __tablename__ = 'genres'
    genre_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Movie(db.Model):
    __tablename__ = 'movies'
    movie_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    poster_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    genres = db.relationship('Genre', secondary=movie_genres, lazy='subquery',
                             backref=db.backref('movies', lazy=True))
    showtimes = db.relationship('Showtime', backref='movie', cascade='all, delete-orphan', lazy=True)

class Theater(db.Model):
    __tablename__ = 'theaters'
    theater_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    total_seats = db.Column(db.Integer, nullable=False)
    seats = db.relationship('Seat', backref='theater', cascade='all, delete-orphan', lazy=True)
    showtimes = db.relationship('Showtime', backref='theater', cascade='all, delete-orphan', lazy=True)

class Seat(db.Model):
    __tablename__ = 'seats'
    seat_id = db.Column(db.Integer, primary_key=True)
    theater_id = db.Column(db.Integer, db.ForeignKey('theaters.theater_id', ondelete='CASCADE'), nullable=False)
    row_label = db.Column(db.String(1), nullable=False)
    seat_number = db.Column(db.Integer, nullable=False)
    
    __table_args__ = (db.UniqueConstraint('theater_id', 'row_label', 'seat_number', name='unique_seat_per_theater'),)

class Showtime(db.Model):
    __tablename__ = 'showtimes'
    showtime_id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.movie_id', ondelete='CASCADE'), nullable=False)
    theater_id = db.Column(db.Integer, db.ForeignKey('theaters.theater_id', ondelete='CASCADE'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
