from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Reservation(db.Model):
    __tablename__ = 'reservations'
    reservation_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False) # Refers to AuthUser ID
    showtime_id = db.Column(db.Integer, nullable=False) # Refers to Movie Service Showtime ID
    reservation_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum('ACTIVE', 'CANCELLED'), default='ACTIVE')
    reservation_seats = db.relationship('ReservationSeat', backref='reservation', cascade='all, delete-orphan', lazy=True)

class ReservationSeat(db.Model):
    __tablename__ = 'reservation_seats'
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.reservation_id', ondelete='CASCADE'), primary_key=True)
    seat_id = db.Column(db.Integer, nullable=False, primary_key=True) # Composite PK
    showtime_id = db.Column(db.Integer, nullable=False)

    __table_args__ = (db.UniqueConstraint('showtime_id', 'seat_id', name='unique_seat_booking_per_showtime'),)
