#!/usr/bin/env python3
import codecs
import csv
import subprocess
import time
import os
import traceback
from copy import deepcopy
from datetime import datetime
from pprint import pprint

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
        print(e)
        traceback.print_exc()
    finally:
        return output


def time_format(s):
    # convert time format from seconds to h:m:s
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return '%d:%02d:%02d' % (h, m, s)


def save_summary(summary, log_file):
    headers = ['application', 'title', 'time']
    with codecs.open(log_file, 'wb', 'utf8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for app_name, data in summary.items():
            total_time = sum(data.values())
            for title, elapsed_time in data.items():
                # writer.writerow([app, title, time_format(elapsed_time)])
                writer.writerow([app_name, title, elapsed_time])

            if ' '.join([app_name,TOTAL_TIME_PREFIX]) not in data:
                writer.writerow([app_name, ' '.join([app_name,TOTAL_TIME_PREFIX]), total_time])


def show_wasted_time():
    summary = {}

    if not os.path.exists(SAVING_LOCATION):
        os.makedirs(SAVING_LOCATION)

    timetuple = datetime.now().timetuple()
    log_file = os.path.join(
        SAVING_LOCATION,
        'wasted_time_%s%s%s.csv' % (timetuple.tm_mday, timetuple.tm_mon, timetuple.tm_year)
    )
    if os.path.exists(log_file):
        print('Reading summary from file: %s' % log_file)
        summary = get_summary_from(log_file)

    while True:
        timetuple = datetime.now().timetuple()
        log_file = os.path.join(
            SAVING_LOCATION,
            'wasted_time_%s%s%s.csv' % (timetuple.tm_mday, timetuple.tm_mon, timetuple.tm_year)
        )
        is_a_new_day = not os.path.exists(log_file)
        if is_a_new_day:
            print('Start logging to file: %s' % log_file)
            summary = {}

        data = get_active_window_data()
        frame_pid = data['pid']
        app_name = data['app_name']
        frame_name = data['title']

        if frame_pid is not None and frame_name and app_name:
            if app_name not in summary:
                summary[app_name] = {}

            application = summary[app_name]
            if frame_name not in application:
                application[frame_name] = PERIOD
            else:
                application[frame_name] += PERIOD

            # print(summary)
            save_summary(summary, log_file)
            time.sleep(PERIOD)


def get_active_window_data():
    app_name = 'Unknown'
    frame_pid = -1
    frame_name = 'Unknown'

    if os.sys.platform == 'linux':
        raise NotImplementedError
        import gi
        import gtk
        gi.require_version('Wnck', '3.0')
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk, Wnck
        Gtk.init([])
        screen = Wnck.Screen.get_default()
        screen.force_update()
        while gtk.events_pending():
            gtk.main_iteration()
        screen.get_windows()
        window = screen.get_active_window()
        app_name = window.get_application().get_name()
        frame_pid = window.get_pid()
        frame_name = window.get_name()
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
        raise NotImplementedError

    return {
        'app_name': app_name,
        'pid': frame_pid,
        'title': frame_name
    }


def combine_time():
    folder = os.path.join(SAVING_LOCATION, 'week51')
    files = [os.path.join(folder, f) for f in os.listdir(folder)]
    total_summary = {}
    for path in files:
        summary = get_summary_from(path)
        total_summary = combine_summaries(total_summary, summary)

    pprint(total_summary)
    save_summary(total_summary, '/tmp/out')


if __name__ == '__main__':
    # TODO: add arguments - run or combine
    show_wasted_time()
    # combine_time()
