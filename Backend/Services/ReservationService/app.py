from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, get_jwt
import requests
from config import Config
from models import db, Reservation, ReservationSeat

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

MOVIE_SERVICE_URL = 'http://localhost:5003'


# ==================== USER ENDPOINTS ====================

@app.route('/reservations', methods=['GET'])
@jwt_required()
def get_my_reservations():
    user_id = get_jwt_identity()
    reservations = Reservation.query.filter_by(user_id=user_id).all()

    result = []
    for r in reservations:
        result.append({
            'reservation_id': r.reservation_id,
            'showtime_id': r.showtime_id,
            'status': r.status,
            'reservation_time': r.reservation_time.isoformat(),
            'seats': [rs.seat_id for rs in r.reservation_seats]
        })
    return jsonify(result), 200

@app.route('/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    user_id = get_jwt_identity()
    data = request.get_json()

    showtime_id = data.get('showtime_id')
    seat_ids = data.get('seat_ids', [])

    if not showtime_id or not seat_ids:
        return jsonify({'message': 'Showtime and seats are required'}), 400

    # Check if seats are already booked for this showtime
    existing = ReservationSeat.query.filter(
        ReservationSeat.showtime_id == showtime_id,
        ReservationSeat.seat_id.in_(seat_ids)
    ).all()

    if existing:
        booked = [e.seat_id for e in existing]
        return jsonify({'message': 'Seats already booked', 'booked_seat_ids': booked}), 409

    try:
        reservation = Reservation(user_id=user_id, showtime_id=showtime_id)
        db.session.add(reservation)
        db.session.flush()

        for seat_id in seat_ids:
            rs = ReservationSeat(
                reservation_id=reservation.reservation_id,
                seat_id=seat_id,
                showtime_id=showtime_id
            )
            db.session.add(rs)

        db.session.commit()
        return jsonify({'message': 'Reservation successful', 'reservation_id': reservation.reservation_id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Booking failed: {str(e)}'}), 500

@app.route('/reservations/<int:reservation_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_reservation(reservation_id):
    print(f"DEBUG: Cancel request for reservation {reservation_id}")
    print(f"DEBUG: Headers: {request.headers}")
    current_user_id = int(get_jwt_identity())
    reservation = Reservation.query.get_or_404(reservation_id)

    if str(reservation.user_id) != str(current_user_id):
        return jsonify({'message': 'Unauthorized'}), 403

    if reservation.status == 'CANCELLED':
        return jsonify({'message': 'Already cancelled'}), 400

    reservation.status = 'CANCELLED'
    # Remove seat bookings so others can book them
    ReservationSeat.query.filter_by(reservation_id=reservation_id).delete()
    db.session.commit()
    return jsonify({'message': 'Reservation cancelled'}), 200

@app.route('/reservations/showtime/<int:showtime_id>/booked-seats', methods=['GET'])
def get_booked_seats(showtime_id):
    """Public: get list of booked seat IDs for a showtime."""
    booked = ReservationSeat.query.filter_by(showtime_id=showtime_id).all()
    return jsonify({'booked_seat_ids': [b.seat_id for b in booked]}), 200


# ==================== ADMIN ENDPOINTS ====================

@app.route('/reservations/all', methods=['GET'])
@jwt_required()
def get_all_reservations():
    claims = get_jwt()
    if claims.get('role') != 'ADMIN':
        return jsonify({'message': 'Admin access required'}), 403

    reservations = Reservation.query.all()
    result = []
    for r in reservations:
        result.append({
            'reservation_id': r.reservation_id,
            'user_id': r.user_id,
            'showtime_id': r.showtime_id,
            'status': r.status,
            'reservation_time': r.reservation_time.isoformat(),
            'seats': [rs.seat_id for rs in r.reservation_seats]
        })
    return jsonify(result), 200

@app.route('/reservations/stats', methods=['GET'])
@jwt_required()
def get_stats():
    claims = get_jwt()
    if claims.get('role') != 'ADMIN':
        return jsonify({'message': 'Admin access required'}), 403

    total = Reservation.query.count()
    active = Reservation.query.filter_by(status='ACTIVE').count()
    cancelled = Reservation.query.filter_by(status='CANCELLED').count()
    total_seats_booked = ReservationSeat.query.count()

    return jsonify({
        'total_reservations': total,
        'active_reservations': active,
        'cancelled_reservations': cancelled,
        'total_seats_booked': total_seats_booked
    }), 200


if __name__ == '__main__':
    app.run(port=5004, debug=True)
