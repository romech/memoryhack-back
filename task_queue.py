import pickle

import redis


r = redis.StrictRedis()

STATUS_NAMES = {
    0: 'Enqueued',
    1: 'Processing',
    2: 'Done',
    -1: 'Failed'
}
deoldify_tracking_key = 'deoldify.tracking:{}'.format

def get_output(job_id):
    data = r.hgetall(deoldify_tracking_key(job_id))
    status_code = int(data.get(b'status', 0))
    if status_code != 2:
        return STATUS_NAMES[status_code], None
    else:
        raw_output = data[b'output']
        return STATUS_NAMES[status_code], pickle.loads(raw_output)

def deoldify_job(source_url, render_factor):
    key = {
        'source_url': source_url,
        'render_factor': render_factor,
        'watermarked': False}
    job_id = r.incr('job_ids')
    r.hmset(deoldify_tracking_key(job_id), {'status': 0, 'ts': r.time()[0]})
    r.rpush('deoldify', pickle.dumps((job_id, key)))
    return job_id


if __name__ == '__main__':
    deoldify_job('https://roadheroes.storage.yandexcloud.net/604dcd82b491c98b9ceaea5a2ed82c0c_origin.jpg', 12)
