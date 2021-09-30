import glob
from copy import deepcopy
import cv2
import numpy


def load_image(file_path):
    frame = cv2.imread(file_path)
    grayed_src = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return grayed_src


def compare_frames(frame1, frame2, source1='Player 1', source2='Player 2'):
    src1 = load_image(frame1)
    src2 = load_image(frame2)

    diff = cv2.absdiff(src1, src2)
    print("Diff")
    print(diff)
    thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    print("Thresh ")
    print(thresh)

    cv2.putText(src1, source1, (25, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
    cv2.putText(src2, source2, (25, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)

    sources = numpy.concatenate((src1, src2), axis=1)
    meta = numpy.concatenate((thresh, diff), axis=1)
    all = numpy.concatenate((sources, meta), axis=0)

    cv2.namedWindow('Result', cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Result", 1920, 1080)
    cv2.imshow("Result", all)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def compare_multiple_frames(frames_prefix_1, frames_prefix_2):
    source_1_frames = sorted(glob.glob(frames_prefix_1), key=lambda x: int(x.split('_')[1].split('.')[0]))
    source_2_frames = sorted(glob.glob(frames_prefix_2), key=lambda x: int(x.split('_')[1].split('.')[0]))
    assert len(source_1_frames) == len(source_2_frames)

    # Compare frames one-by-one
    differences = []
    for frame1, frame2 in zip(source_1_frames, source_2_frames):
        src1 = load_image(frame1)
        src2 = load_image(frame2)
        diff = cv2.absdiff(src1, src2)
        diff = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        differences.append(diff)

    start_time, increment = 30, 30
    diff_frames = []
    tmp = []

    # Split into rows of 5, add timestamps
    for diff_frame in differences:
        cv2.putText(diff_frame, str(start_time), (25, 75), cv2.FONT_HERSHEY_SIMPLEX, 3, (0,), 18)
        cv2.putText(diff_frame, str(start_time), (25, 75), cv2.FONT_HERSHEY_SIMPLEX, 3, (255,), 9)
        tmp.append(diff_frame)
        start_time += increment
        if len(tmp) == 6:
            diff_frames.append(deepcopy(tmp))
            tmp = []

    # Merge images from one row
    all_frames = []
    for diff_array in diff_frames:
        tmp = None
        for diff_frame in diff_array:
            if tmp is None:
                tmp = diff_frame
            else:
                tmp = numpy.concatenate((tmp, diff_frame), axis=1)
        all_frames.append(deepcopy(tmp))

    # Merge rows into a single page
    all_rows = []
    for idx, merged_row in enumerate(all_frames):
        if all_rows == []:
            all_rows = merged_row
        else:
            all_rows = numpy.concatenate((all_rows, merged_row), axis=0)

    cv2.namedWindow('Result', cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Result", 1920, 1080)
    cv2.imshow("Result", all_rows)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # compare_frames(
    #     '/home/vitalii/Pictures/js_30.png',
    #     '/home/vitalii/Pictures/theo_30.png',
    #     'VideoJS',
    #     'THEOPlayer'
    # )
    compare_multiple_frames(
        "/home/vitalii/Pictures/theo*",
        "/home/vitalii/Pictures/js_*",
    )
