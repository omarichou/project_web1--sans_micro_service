from flask import Flask, request, jsonify, Response, render_template, session, redirect, url_for
import requests
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret')

AUTH_URL = os.environ.get("AUTH_URL", "http://auth:5001")
DISHES_URL = os.environ.get("DISHES_URL", "http://dishes:5002")
ORDERS_URL = os.environ.get("ORDERS_URL", "http://orders:5003")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "gateway"})


def proxy(path, method="GET", target_url=None):
    url = f"{target_url}{path}"
    headers = {k: v for k, v in request.headers if k.lower() != 'host'}
    resp = requests.request(method, url, headers=headers, json=request.get_json(silent=True), params=request.args)
    return Response(resp.content, status=resp.status_code, mimetype=resp.headers.get('Content-Type','application/json'))


@app.route('/api/auth/<path:path>', methods=['GET','POST','PUT','DELETE'])
def auth_proxy(path):
    return proxy(f"/{path}", method=request.method, target_url=AUTH_URL)


@app.route('/api/dishes/<path:path>', methods=['GET','POST','PUT','DELETE'])
def dishes_proxy(path):
    return proxy(f"/{path}", method=request.method, target_url=DISHES_URL)


@app.route('/api/orders/<path:path>', methods=['GET','POST','PUT','DELETE'])
def orders_proxy(path):
    return proxy(f"/{path}", method=request.method, target_url=ORDERS_URL)


@app.route('/api/dishes', methods=['GET','POST'])
def dishes_root():
    return proxy('/dishes', method=request.method, target_url=DISHES_URL)


@app.route('/api/orders', methods=['GET','POST'])
def orders_root():
    return proxy('/orders', method=request.method, target_url=ORDERS_URL)


@app.route('/api/auth/register', methods=['POST'])
def register():
    return proxy('/register', method='POST', target_url=AUTH_URL)


@app.route('/api/auth/login', methods=['POST'])
def login():
    return proxy('/login', method='POST', target_url=AUTH_URL)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))


@app.route('/')
def index():
    try:
        cats = requests.get(f"{DISHES_URL}/categories", timeout=2).json()
    except Exception:
        cats = []
    try:
        dishes = requests.get(f"{DISHES_URL}/dishes", timeout=2).json()
    except Exception:
        dishes = []
    return render_template('index.html', categories=cats, dishes=dishes, user=session.get('user'))


@app.route('/dishes')
def dishes_view():
    category = request.args.get('category')
    params = {}
    if category:
        params['category'] = category
    try:
        dishes = requests.get(f"{DISHES_URL}/dishes", params=params, timeout=2).json()
    except Exception:
        dishes = []
    try:
        cats = requests.get(f"{DISHES_URL}/categories", timeout=2).json()
    except Exception:
        cats = []
    return render_template('dishes.html', dishes=dishes, categories=cats, selected_category=category, user=session.get('user'))


@app.route('/register', methods=['GET', 'POST'])
def page_register():
    if request.method == 'GET':
        return render_template('register.html')
    data = request.form.to_dict() or request.get_json() or {}
    resp = requests.post(f"{AUTH_URL}/register", json=data)
    if resp.status_code == 201:
        user = resp.json()
        session['user'] = user
        return redirect(url_for('index'))
    return render_template('register.html', error=resp.text)


@app.route('/login', methods=['GET', 'POST'])
def page_login():
    if request.method == 'GET':
        return render_template('login.html')
    data = request.form.to_dict() or request.get_json() or {}
    resp = requests.post(f"{AUTH_URL}/login", json=data)
    if resp.status_code == 200:
        user = resp.json()
        session['user'] = user
        return redirect(url_for('index'))
    return render_template('login.html', error=resp.text)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


@app.route('/cart')
def cart_page():
    cart = session.get('cart', [])
    # enrich with dish details
    detailed = []
    for item in cart:
        try:
            d = requests.get(f"{DISHES_URL}/dishes", params={'category': ''}, timeout=2)
        except Exception:
            d = None
        detailed.append(item)
    return render_template('cart.html', cart=cart, user=session.get('user'))


@app.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json() or {}
    user = session.get('user')
    if not user:
        return jsonify({'error': 'not authenticated'}), 401
    items = data.get('items') or session.get('cart', [])
    payload = {'user_id': user.get('id'), 'items': items}
    resp = requests.post(f"{ORDERS_URL}/orders", json=payload)
    if resp.status_code in (200, 201):
        session['cart'] = []
        return jsonify({'status': 'ok', 'order': resp.json()}), resp.status_code
    return jsonify({'error': 'order failed', 'details': resp.text}), 500
