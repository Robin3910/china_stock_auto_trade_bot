import functools
from flask import Flask, request, jsonify
from thsauto import ThsAuto
import time
import sys
import threading
import requests

import os

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

auto = ThsAuto()

client_path = None
def run_client():
    os.system('start ' + client_path)
    

lock = threading.Lock()
next_time = 0
interval = 0.5

ip_whitelist = ["52.89.214.238", "34.212.75.30", "54.218.53.128", "52.32.178.7", "192.168.31.109"]


@app.before_request
def process_request():
    ip = request.remote_addr
    print("remote ip: ", ip)

    if ip not in ip_whitelist:
        return 'ip is not in whitelist!', 400


def interval_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global interval
        global lock
        global next_time
        lock.acquire()
        now = time.time()
        if now < next_time:
            time.sleep(next_time - now)
        try:
            rt = func(*args, **kwargs)
        except Exception as e:
            rt = ({'code': 1, 'status': 'failed', 'msg': '{}'.format(e)}, 400)
        next_time = time.time() + interval
        lock.release()
        return rt
    return wrapper

@app.route('/thsauto/balance', methods = ['GET'])
@interval_call
def get_balance():
    auto.active_mian_window()
    result = auto.get_balance()
    return jsonify(result), 200

@app.route('/thsauto/position', methods = ['GET'])
@interval_call
def get_position():
    auto.active_mian_window()
    result = auto.get_position()
    return jsonify(result), 200

@app.route('/thsauto/orders/active', methods = ['GET'])
@interval_call
def get_active_orders():
    auto.active_mian_window()
    result = auto.get_active_orders()
    return jsonify(result), 200

@app.route('/thsauto/orders/filled', methods = ['GET'])
@interval_call
def get_filled_orders():
    auto.active_mian_window()
    result = auto.get_filled_orders()
    return jsonify(result), 200

# post body demo
# {
#     "direction": "long"/"close"
#     "ticker": "512170",
#     "amount": "1000",
#     "price": "0.416"
# }

@app.route('/thsauto/order', methods = ['POST'])
@interval_call
def order():
    auto.active_mian_window()
    json_data = request.get_json()
    direction = json_data.get('direction')
    stock = json_data.get('ticker')
    amount = json_data.get('amount')
    price = json_data.get('price')
    if price is not None:
        price = float(price)
    result = ""
    if direction == "long":
        result = auto.buy(stock_no=stock, amount=int(amount), price=price)
    if direction == "close":
        result = auto.sell(stock_no=stock, amount=int(amount), price=price)

    requests.get(f'https://sctapi.ftqq.com/SCT143186TIvKuCgmwWnzzzGQ6mE5qmyFU.send?title=A_{stock}_{amount}')
    return jsonify(result), 200

@app.route('/thsauto/sell', methods = ['POST'])
@interval_call
def sell():
    auto.active_mian_window()
    json_data = request.get_json()
    print(json_data)
    stock = json_data.get('ticker')
    amount = json_data.get('amount')
    price = json_data.get('price')
    if price is not None:
        price = float(price)
    result = auto.sell(stock_no=stock, amount=int(amount), price=price)
    return jsonify(result), 200

@app.route('/thsauto/buy', methods = ['POST'])
@interval_call
def buy():
    auto.active_mian_window()
    json_data = request.get_json()
    print(json_data)
    stock = json_data.get('ticker')
    amount = json_data.get('amount')
    price = json_data.get('price')
    if price is not None:
        price = float(price)
    result = auto.buy(stock_no=stock, amount=int(amount), price=price)
    return jsonify(result), 200

@app.route('/thsauto/buy/kc', methods = ['GET'])
@interval_call
def buy_kc():
    auto.active_mian_window()
    stock = request.args['stock_no']
    amount = request.args['amount']
    price = request.args.get('price', None)
    if price is not None:
        price = float(price)
    result = auto.buy_kc(stock_no=stock, amount=int(amount), price=price)
    return jsonify(result), 200

@app.route('/thsauto/sell/kc', methods = ['GET'])
@interval_call
def sell_kc():
    auto.active_mian_window()
    stock = request.args['stock_no']
    amount = request.args['amount']
    price = request.args.get('price', None)
    if price is not None:
        price = float(price)
    result = auto.sell_kc(stock_no=stock, amount=int(amount), price=price)
    return jsonify(result), 200

@app.route('/thsauto/cancel', methods = ['GET'])
@interval_call
def cancel():
    auto.active_mian_window()
    entrust_no = request.args['entrust_no']
    result = auto.cancel(entrust_no=entrust_no)
    return jsonify(result), 200

@app.route('/thsauto/client/kill', methods = ['GET'])
@interval_call
def kill_client():
    auto.active_mian_window()
    auto.kill_client()
    return jsonify({'code': 0, 'status': 'succeed'}), 200


@app.route('/thsauto/client/restart', methods = ['GET'])
@interval_call
def restart_client():
    auto.active_mian_window()
    auto.kill_client()
    run_client()
    time.sleep(5)
    auto.bind_client()
    if auto.hwnd_main is None:
        return jsonify({'code': 1, 'status': 'failed'}), 200
    else:
        return jsonify({'code': 0, 'status': 'succeed'}), 200


@app.route('/thsauto/test', methods = ['GET'])
@interval_call
def test():
    auto.active_mian_window()
    auto.test()
    return jsonify({}), 200


if __name__ == '__main__':
    host = '127.0.0.1'
    port = 5000
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    if len(sys.argv) > 3:
        client_path = sys.argv[3]
    auto.bind_client()
    if auto.hwnd_main is None and client_path is not None:
        restart_client()
    app.run(host=host, port=port)