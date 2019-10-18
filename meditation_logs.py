#!/usr/bin/env python

"""
Parse downloaded meditation logs from Tergar meditation app
"""
import json
import os
import sys
import glob

def meditation_log_files():
    return glob.glob(os.path.expanduser("~/Downloads/tergar-meditation-logs-20*.json"))

def hours_minutes_seconds(seconds):
    (mins, secs) = divmod(seconds, 60)
    (hours, minutes) = divmod(mins, 60)
    return (hours, minutes, secs)


def format_time(seconds):
    h, m, s = hours_minutes_seconds(seconds)
    if h > 0:
        return "{:d}:{:02d}:{:02d}".format(h, m, s)
    else:
        return "{:d}:{:02d}".format(m, s)


class MeditationLogs:
    def __init__(self, log_file):
        entries = json.load(open(log_file)).get("valor")
        if entries:
            self.all_entries = sorted(entries, key=lambda e: e["date"])
        else:
            raise Exception("No entries")
        self.buckets = {}
        self.bucket_entries()

    def bucket_entries(self):
        # jol3 and not-jol3 should partition the complete set of logs
        self.buckets["jol3"] = [e for e in self.all_entries if e["course"]["code"] == "JOL3"]
        self.buckets["not-jol3"] = [e for e in self.all_entries if e["course"]["code"] == "JOL3"]
        self.buckets["custom"] = [e for e in self.all_entries if e["course"]["code"] == "JOL3"]
        # these buckets are based on my convention of putting W1 through W6 for the week of the course
        # and therefore the different meditations since each week introduced a new method
        self.buckets["jol3-by-week"] = {}
        for bucket in ("W1", "W2", "W3", "W4", "W5", "W6"):
            self.buckets["jol3-by-week"][bucket] = [e for e in self.buckets["jol3"] if e.get("notes") and bucket in e["notes"]]
        # Dying Every Day Course
        self.buckets["ded"] = [e for e in self.buckets["custom"] if e.get("notes") and "DED" in e["notes"]]


    @classmethod
    def total_duration_seconds(cls, bucket):
        elapsed_list = [e.get("elapsed") for e in bucket]
        seconds = sum(int(x) for x in elapsed_list)
        return seconds

    @classmethod
    def most_recent(cls, bucket):
        if len(bucket) > 0:
            return bucket[-1]

    # returns (week name, number of entries, total seconds of meditation for that week) for each week
    def jol3_by_week_totals(self):
        returns = []
        for week in self.buckets['jol3-by-week']:
            returns.append((week,
                           len(self.buckets['jol3-by-week'][week]),
                           MeditationLogs.total_duration_seconds(self.buckets['jol3-by-week'][week])))
        return returns

    def jol3_stats_string(self):
        header = "JOL 3 Meditation"
        overall = "Total sessions: {}, Total Time: {}".format(
            len(self.buckets["jol3"]),
            format_time(MeditationLogs.total_duration_seconds(self.buckets["jol3"])))
        weeks_header = "By Weeks:\n{:6}{:12}{}".format("Week", "Sessions", "Time")
        weeks = "\n".join(["{:>3}{:>8}{:>13}".format(t[0], t[1], format_time(t[2])) for t in self.jol3_by_week_totals()])
        return "\n".join((header, overall, weeks_header, weeks))

    def overall_stats_string(self):
        header = "Overall Meditation"
        overall = "Total sessions: {}, Total Time: {}".format(
            len(self.all_entries),
            format_time(MeditationLogs.total_duration_seconds(self.all_entries)))
        return "\n".join([header, overall])

    def ded_stats_string(self):
        header = "DED Meditation"
        overall = "Total sessions: {}, Total Time: {}".format(
            len(self.buckets["ded"]),
            format_time(MeditationLogs.total_duration_seconds(self.buckets["ded"])))
        return "\n".join([header, overall])


def clean_up_old_files():
    log_files = meditation_log_files()
    if len(log_files) > 1:
        for i, f in enumerate(sorted(log_files)[:-1]):
            os.remove(f)
        print("removed old files: {}".format(i+1))

def latest_log():
    log_files = meditation_log_files()
    if log_files:
        return sorted(log_files)[-1]


if __name__ == "__main__":

    log_file = latest_log()
    if not log_file:
        print("No downloaded logs in ~/Downloads")
        exit(0)
    clean_up_old_files()
    print("meditation log file: {}\n".format(log_file))

    ml = MeditationLogs(log_file)
    print("{}\n\n{}\n\n{}\n".format(ml.jol3_stats_string(), ml.ded_stats_string(), ml.overall_stats_string()))
