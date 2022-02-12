from flask import Flask
from flask import request, jsonify, render_template
import datetime

app = Flask(__name__)

BOTS_STATUS = {
}

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    bot_uuid = request.args.get('bot_uuid')
    user_count = request.args.get('user_count')
    if not bot_uuid in BOTS_STATUS:
        BOTS_STATUS[bot_uuid] = {}
    BOTS_STATUS[bot_uuid]['user_count'] = user_count
    BOTS_STATUS[bot_uuid]['last_heartbeat'] = datetime.datetime.now()
    if (datetime.datetime.now() - BOTS_STATUS[bot_uuid]['last_heartbeat']).total_seconds() > 300:
        BOTS_STATUS[bot_uuid]['status'] = 'offline'
    else:
        BOTS_STATUS[bot_uuid]['status'] = 'online'
    return jsonify({'status': 'ok'})

@app.route('/', methods=['GET'])
def status():
    return render_template('status.html', bots_status=BOTS_STATUS)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
