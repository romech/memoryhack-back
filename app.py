import os.path
import tempfile
import time
import uuid

from flask import Flask
from flask import Response
from flask import abort
from flask import request
from flask import send_file
from flask import send_from_directory
from flask import url_for
from flask_cors import CORS, cross_origin
import requests

import task_queue

HOST = 'https://deoldify-044f6348.localhost.run'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
CORS(app)


@app.route('/ping', methods=['GET'])
def ping():
    return 'pong'


@app.route('/deoldify', methods=['POST'])
@cross_origin()
def deoldify():
    data = request.get_json() or request.form
    source_url = data.get('source_url')
    if not source_url:
        file = request.files.get('image')
        if file is None or file.filename == '':
            return abort(400, 'Missing image')

        if file and allowed_file(file.filename):
            filename = f'{uuid.uuid4()}.{_get_extension(file.filename)}'
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            source_url = HOST + url_for('uploaded_file', filename=filename)
            print('Sharing to worker:', source_url)

    job_id = task_queue.deoldify_job(source_url, int(data.get('render_factor', 10)))
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


@app.route('/reenact', methods=['POST'])
@cross_origin()
def reenact():
    resp = requests.request(
        method=request.method,
        url='104.211.46.237:5000/reenact',
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)
    return response


def _get_extension(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower()

def allowed_file(filename):
    return _get_extension(filename) in ALLOWED_EXTENSIONS


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


if __name__ == '__main__':
    port = 8080
    host = '0.0.0.0'

    app.run(host=host, port=port)
