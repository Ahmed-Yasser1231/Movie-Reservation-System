from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Service URLs
AUTH_SERVICE = 'http://localhost:5001'
USER_SERVICE = 'http://localhost:5002'
MOVIE_SERVICE = 'http://localhost:5003'
RESERVATION_SERVICE = 'http://localhost:5004'


def forward_request(service_url, path):
    """Forward incoming request to the target microservice."""
    url = f"{service_url}{path}"
    headers = {key: value for (key, value) in request.headers if key != 'Host'}

    if 'Authorization' in headers:
        print(f"DEBUG: Forwarding Authorization header: {headers['Authorization'][:20]}...")
    else:
        print("DEBUG: No Authorization header found in request to Gateway!")

    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.get_data(),
            params=request.args,
            cookies=request.cookies,
            allow_redirects=False
        )
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = {k: v for k, v in resp.headers.items() if k.lower() not in excluded_headers}
        return Response(resp.content, resp.status_code, headers=headers)
    except requests.exceptions.RequestException as e:
        return jsonify({'message': f'Service unavailable: {str(e)}'}), 503


# ==================== AUTH ROUTES ====================

@app.route('/api/auth/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def auth_proxy(path):
    return forward_request(AUTH_SERVICE, f'/auth/{path}')


# ==================== USER ROUTES ====================

@app.route('/api/users/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def user_proxy(path):
    return forward_request(USER_SERVICE, f'/users/{path}')


# ==================== MOVIE ROUTES ====================

@app.route('/api/movies', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/api/movies/<path:path>', methods=['GET', 'PUT', 'DELETE'])
def movie_proxy(path):
    target_path = '/movies' if not path else f'/movies/{path}'
    return forward_request(MOVIE_SERVICE, target_path)

@app.route('/api/genres', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/api/genres/<path:path>', methods=['GET'])
def genre_proxy(path):
    target_path = '/genres' if not path else f'/genres/{path}'
    return forward_request(MOVIE_SERVICE, target_path)

@app.route('/api/theaters', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/api/theaters/<path:path>', methods=['GET', 'PUT', 'DELETE'])
def theater_proxy(path):
    target_path = '/theaters' if not path else f'/theaters/{path}'
    return forward_request(MOVIE_SERVICE, target_path)

@app.route('/api/showtimes', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/api/showtimes/<path:path>', methods=['GET', 'DELETE'])
def showtime_proxy(path):
    target_path = '/showtimes' if not path else f'/showtimes/{path}'
    return forward_request(MOVIE_SERVICE, target_path)


# ==================== RESERVATION ROUTES ====================

@app.route('/api/reservations', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/api/reservations/<path:path>', methods=['GET', 'POST', 'DELETE'])
def reservation_proxy(path):
    target_path = '/reservations' if not path else f'/reservations/{path}'
    return forward_request(RESERVATION_SERVICE, target_path)


# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'Gateway Operational'}), 200


if __name__ == '__main__':
    app.run(port=5000, debug=True)
