import glob
from flask import request


def available_devices():
    video_devices = glob.glob('/dev/video*')
    resp = []
    for _ in video_devices:
        resp.append({str(len(resp)): "Available"})
    return resp
    # return [{'0': 'Available'}, {'1': 'Active'}]


def is_browser_request():
    return any([s in request.user_agent.string for s in
                ['Mozilla', 'AppleWebKit', 'Gecko', 'Chrome', 'Safari']])
