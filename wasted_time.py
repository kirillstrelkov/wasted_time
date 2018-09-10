#!/usr/bin/env python3
import argparse
import csv
import subprocess
import time
import traceback
from datetime import datetime
from tempfile import gettempdir

import codecs
import os
from copy import deepcopy

PERIOD = 1.0  # second
TOTAL_TIME_PREFIX = 'total time'
SAVING_LOCATION = os.path.join(os.path.expanduser('~'), 'wasted_time')


def get_summary_from(path):
    summary = {}

    with codecs.open(path, 'rb', 'utf8') as f:
        for row in csv.reader(f):
            if row == ['application', 'title', 'time']:
                continue
            assert len(row) == 3
            app_name, frame_name, elapsed_time = row

            if app_name not in summary:
                summary[app_name] = {}

            app_data = summary[app_name]
            if frame_name not in app_data:
                app_data[frame_name] = float(elapsed_time)
            else:
                app_data[frame_name] += float(elapsed_time)

    add_total_time(summary)

    return summary


def add_total_time(dictionary):
    for app_name, app_data in dictionary.items():
        total_time_prefix = ' '.join([app_name, TOTAL_TIME_PREFIX])
        if total_time_prefix in app_data:
            del app_data[total_time_prefix]
        app_data[total_time_prefix] = sum(app_data.values())


def combine_summaries(summary1, summary2):
    combined_summary = deepcopy(summary1)
    add_total_time(combined_summary)

    for app_name, app_data in summary2.items():
        if app_name in combined_summary:
            for frame_name, elapsed_time in app_data.items():
                app = combined_summary[app_name]
                if frame_name in app:
                    app[frame_name] += elapsed_time
                else:
                    app[frame_name] = elapsed_time
        else:
            combined_summary[app_name] = deepcopy(app_data)

    add_total_time(combined_summary)

    return combined_summary


def get_cmd_output(command):
    output = None
    try:
        output = subprocess.check_output(command).decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        traceback.print_exc()
    finally:
        return output


def time_format(s):
    # convert time format from seconds to h:m:s
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return '{:02d}:{:02d}:{:02d}'.format(h, m, s)


def save_summary(summary, log_file):
    headers = ['application', 'title', 'time']
    with codecs.open(log_file, 'wb', 'utf8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for app_name, data in summary.items():
            total_time = sum(data.values())
            for title, elapsed_time in data.items():
                writer.writerow([app_name, title, elapsed_time])

            if ' '.join([app_name, TOTAL_TIME_PREFIX]) not in data:
                writer.writerow([app_name, ' '.join([app_name, TOTAL_TIME_PREFIX]), total_time])


def __get_log_file():
    timetuple = datetime.now().timetuple()
    return os.path.join(
        SAVING_LOCATION,
        'wasted_time_{:02d}{:02d}{:d}.csv'.format(
            timetuple.tm_mday, timetuple.tm_mon, timetuple.tm_year
        )
    )


def record_wasted_time():
    summary = {}

    if not os.path.exists(SAVING_LOCATION):
        os.makedirs(SAVING_LOCATION)

    log_file = __get_log_file()
    if os.path.exists(log_file):
        print('Reading summary from file: {}'.format(log_file))
        summary = get_summary_from(log_file)

    while True:
        log_file = __get_log_file()
        is_a_new_day = not os.path.exists(log_file)
        if is_a_new_day:
            print('Start logging to file: {}'.format(log_file))
            summary = {}

        data = get_active_window_data()
        frame_pid = data['pid']
        app_name = data['app_name']
        frame_name = data['title']

        if frame_pid > 0 and frame_name != 'Unknown' and app_name != 'Unknown':
            if app_name not in summary:
                summary[app_name] = {}

            application = summary[app_name]
            if frame_name not in application:
                application[frame_name] = PERIOD
            else:
                application[frame_name] += PERIOD

            save_summary(summary, log_file)
            time.sleep(PERIOD)


def get_active_window_data():
    app_name = 'Unknown'
    frame_pid = -1
    frame_name = 'Unknown'
    try:
        if os.sys.platform == 'linux':
            frame_pid = get_cmd_output(['xdotool', 'getactivewindow', 'getwindowpid'])
            frame_name = get_cmd_output(['xdotool', 'getwindowfocus', 'getwindowname'])
            if frame_pid:
                app_name = get_cmd_output(['ps', '-p', frame_pid, '-o', 'comm='])
            else:
                app_name = 'Unknown'
        elif os.sys.platform == "darwin":
            from AppKit import NSWorkspace
            from Quartz import CGWindowListCopyWindowInfo, \
                kCGWindowListOptionOnScreenOnly, \
                kCGNullWindowID

            application = NSWorkspace.sharedWorkspace().activeApplication()
            frame_pid = application['NSApplicationProcessIdentifier']
            app_name = application['NSApplicationName']
            for window in CGWindowListCopyWindowInfo(
                    kCGWindowListOptionOnScreenOnly, kCGNullWindowID
            ):
                pid = window['kCGWindowOwnerPID']
                window_title = window.get('kCGWindowName', u'Unknown')
                if frame_pid == pid:
                    frame_name = window_title
                    break
        elif os.sys.platform == "win32":
            import win32gui, win32process, psutil
            window = win32gui.GetForegroundWindow()
            frame_pid =  win32process.GetWindowThreadProcessId(window)[-1]
            frame_name = win32gui.GetWindowText(window)
            app_name = psutil.Process(frame_pid).name()
    except:
        traceback.print_exc()

    return {
        'app_name': app_name,
        'pid': frame_pid,
        'title': frame_name
    }


def merge_time(folder):
    folder = os.path.abspath(folder)
    if not os.path.exists(folder):
        raise FileNotFoundError("Folder not found '{}'".format(folder))

    files = [os.path.join(folder, f) for f in os.listdir(folder)]
    total_summary = {}
    for path in files:
        summary = get_summary_from(path)
        total_summary = combine_summaries(total_summary, summary)

    log_file = os.path.join(gettempdir(), 'wasted_time_merged.csv')
    print("Saving merged results to '{}'".format(log_file))
    save_summary(total_summary, log_file)


def __main():
    parser = argparse.ArgumentParser(
        description='Records all time which was spent on different windows/apps with titles'
    )
    parser.add_argument('-m', '--merge', action='store_true', help='merge all files into one')
    parser.add_argument('-i', '--input', help='input directory where to take files for merging')

    args = parser.parse_args()
    if args.merge and args.input and os.path.isdir(args.input):
        merge_time(args.input)
    elif not args.merge and not args.input:
        record_wasted_time()
    else:
        raise ValueError('Please specify both -m and -i or nothing')


if __name__ == '__main__':
    __main()
