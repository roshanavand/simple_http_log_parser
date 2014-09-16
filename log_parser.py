import sys
import re
import collections
import argparse


TOP_10_REQUESTS = None
TOP_10_FAILED = None
TOP_10_BY_SRC = None

ALL_REQ = {}
SUCCESS_REQ_DATA = {}
FAILED_REQ_DATA = {}
REQ_PER_SRC = {}


TOTAL_REQ = 0
SUCCESS_RESP = 0
FAILED_RESP = 0


line_pattern = re.compile( '(.*) - - \[(.*)\] "(.*) (.*) HTTP\/(.*)" (.*) (.*)\n' )


class TOPContainer(object):
    def __init__(self, count=10):
        self.count = count
        self.top_list = {}
        self.min_val = 0
        self.max_val = 0

    def check(self, key, latest_val):
        if len(self.top_list) < self.count:
            self._add_item(key, latest_val)

        elif latest_val>self.max_val or latest_val>self.min_val:
            self._add_item(key, latest_val)

    def _add_item(self, k, v):
        self.top_list[k] = v
        self.max_val = max(self.max_val, v)
        self.min_val = min(self.top_list.values())
        if len(self.top_list) > self.count:
            top_list = self.get_top_list()
            top_list.popitem() #remove last one
            self.top_list = dict(top_list)

    def get_top_list(self):
        top_list = collections.OrderedDict(
            sorted(self.top_list.items(),
                   key=lambda x: x[1], reverse=True)
        )
        return top_list


def parse_line(line):
    """
    Parse and extract data from each line
    """
    group = line_pattern.findall(line)
    if not group:
        return

    group = group[0]
    src_ip = group[0]
    req_time = group[1]
    path = group[3]
    status = int(group[-2])

    update_stats(src_ip, path, req_time, status)


def update_total(path, req_time):
    if path not in ALL_REQ:
        ALL_REQ[path] = 0
    ALL_REQ[path] += 1

    TOP_10_REQUESTS.check(path, ALL_REQ[path])

def update_success(path, req_time):
    if path not in SUCCESS_REQ_DATA:
        SUCCESS_REQ_DATA[path] = 0
    SUCCESS_REQ_DATA[path] += 1


def update_failed(path, req_time):
    if path not in FAILED_REQ_DATA:
        FAILED_REQ_DATA[path] = 0
    FAILED_REQ_DATA[path] += 1

    TOP_10_FAILED.check(path, FAILED_REQ_DATA[path])


def update_src_stats(src):
    if src not in REQ_PER_SRC:
        REQ_PER_SRC[src] = 0
    REQ_PER_SRC[src] += 1

    TOP_10_BY_SRC.check(src, REQ_PER_SRC[src])


def update_stats(src, path, req_time, status):
    """
    Update stats for each extracted data row
    """
    global TOTAL_REQ, SUCCESS_RESP, FAILED_RESP

    update_src_stats(src)
    update_total(path, req_time)

    TOTAL_REQ += 1
    if status >= 200 and status <= 400:
        SUCCESS_RESP += 1
        update_success(path, req_time)
    else:
        FAILED_RESP += 1
        update_failed(path, req_time)


def calc_percent_req():
    success_percent = (SUCCESS_RESP*100.0)/TOTAL_REQ
    failed_percent = (FAILED_RESP*100.0)/TOTAL_REQ
    return success_percent, failed_percent



if __name__ == '__main__':

    aparser = argparse.ArgumentParser(description='Options')
    #aparser.add_argument('--total', help='Show Total Requests')
    aparser.add_argument('--success', help='Show Percentage of Successful Requests')
    aparser.add_argument('--failed', help='Show Percentage of Unsuccessful Requests')
    aparser.add_argument('--top-pages', help='Show Top 10 Requested Pages')
    aparser.add_argument('--top-failed', help='Show Top 10 Unsuccessful Requests')
    aparser.add_argument('--top-src', help='Show Total 10 Source IP By Request Number')
    aparser.add_argument('input', help='Input Log File')

    args = aparser.parse_args()
    #print args

    TOP_10_FAILED = TOPContainer(10)
    TOP_10_REQUESTS = TOPContainer(10)
    TOP_10_BY_SRC = TOPContainer(10)

    input_file = args.input
    output_file = open(args.input+'_report.txt', 'w')

    fd = open(input_file)
    for line in fd:
        parse_line(line)

    if args.top_pages:
        output_file.write( 'Top 10 Requested Pages:\n' )
        for path, count in TOP_10_REQUESTS.get_top_list().items():
            output_file.write('\t%s: %s\n'%(count, path))

    ####################
    success, failed = calc_percent_req()
    if args.success:
        output_file.write('Successful Requests(%%): %s\n'%success)

    if args.failed:
        output_file.write('Unsuccessful Requests(%%): %s\n'%failed)

    ####################
    if args.top_failed:
        output_file.write('Top 10 Unsuccessful Requested Pages:\n')
        for path, count in TOP_10_FAILED.get_top_list().items():
            output_file.write('\t%s: %s\n'%(count, path))

    if args.top_src:
        output_file.write('Top 10 Source IPs:\n')
        for path, count in TOP_10_BY_SRC.get_top_list().items():
            output_file.write('\t%s: %s\n'%(count, path))

    output_file.close()
