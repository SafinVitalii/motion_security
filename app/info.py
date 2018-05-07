import glob


def available_devices():
    video_devices = glob.glob('/dev/video*')
    resp = []
    for _ in video_devices:
        resp.append({str(len(resp)): "Available"})
    return [{'0': 'Available'}, {'1': 'Active'}]
