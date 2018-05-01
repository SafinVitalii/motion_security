from processors.monitor import Monitor

if __name__ == '__main__':
    monitor = Monitor(webcam_id=0)
    monitor.capture_video_and_motion()
