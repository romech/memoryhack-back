import tempfile
import time

from flask import Flask
from flask import abort
from flask import request
from flask import send_file
from flask_cors import CORS, cross_origin

import task_queue

app = Flask(__name__)
CORS(app)


@app.route('/ping', methods=['GET'])
def ping():
    return 'pong'


@app.route('/deoldify', methods=['POST'])
@cross_origin()
def deoldify():
    data = request.get_json() or request.form
    if 'source_url' not in data:
        abort(400, 'Image URL missing')

    job_id = task_queue.deoldify_job(data.get('source_url'),
                                     int(data.get('render_factor', 10)))
    time.sleep(0.2)
    while True:
        status, result = task_queue.get_output(job_id)
        if status == 'Done':
            with tempfile.NamedTemporaryFile('wb', suffix='.jpg') as f:
                result.save(f.name)
                callback = send_file(f.name, mimetype='image/jpeg')
                return callback, 200
        elif status == 'Failed':
            print('Failed job status')
            abort(500, 'Unable to process request')
        else:
            time.sleep(0.5)


if __name__ == '__main__':
    port = 8080
    host = '0.0.0.0'

    app.run(host=host, port=port)
