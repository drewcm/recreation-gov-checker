#!/usr/bin/env python3

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta

import requests
from fake_useragent import UserAgent


LOG = logging.getLogger(__name__)
formatter = logging.Formatter(
    "%(asctime)s - %(process)s - %(levelname)s - %(message)s")
sh = logging.StreamHandler()
sh.setFormatter(formatter)
LOG.addHandler(sh)


BASE_URL = "https://www.recreation.gov"
TICKET_BOOKING_URL = "/ticket/facility/{}"
TICKETS_AVAIL_ENDPOINT = "/api/ticket/availability/facility/"
FACILITY_ENDPOINT = "/api/ticket/facility/"
CAMPGROUND_BOOKING_URL = "/camping/campgrounds/{}/availability"
CAMPGROUND_AVAIL_ENDPOINT = "/api/camps/availability/campground/"
CAMPGROUNDS_ENDPOINT = "/api/camps/campgrounds/"

INPUT_DATE_FORMAT = "%Y-%m-%d"

SUCCESS_EMOJI = "-"
FAILURE_EMOJI = "-"

headers = {"User-Agent": UserAgent().random}


def format_datetime(date_object):
    return '{:%Y-%m-%d %H:%M:%S}'.format(date_object)


def format_date(date_object):
    date_formatted = datetime.strftime(date_object,
        "%Y-%m-%dT00:00:00Z")
    return date_formatted


def generate_params(start, end):
    params = {"start_date": format_date(start),
              "end_date": format_date(end)}
    return params


def send_request(url, params):
    resp = requests.get(url, params=params, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(
            "failedRequest",
            "ERROR, {} code received from {}: {}".format(
                resp.status_code, url, resp.text
            ),
        )
    return resp.json()


def get_num_available_tickets(facility_id, date):
    date_str = date.strftime(INPUT_DATE_FORMAT)
    url = "{}{}{}".format(BASE_URL, TICKETS_AVAIL_ENDPOINT, facility_id)
    resp = send_request(url, {"date": date_str})
    return resp


def get_campground_information(campground_id, params):
    url = "{}{}{}".format(BASE_URL, CAMPGROUND_AVAIL_ENDPOINT, campground_id)
    return send_request(url, params)


def get_name_of_campground(campground_id):
    url = "{}{}{}".format(BASE_URL, CAMPGROUNDS_ENDPOINT, campground_id)
    resp = send_request(url, {})
    return resp["campground"]["facility_name"]


def get_name_of_facility(facility_id):
    url = "{}{}{}".format(BASE_URL, FACILITY_ENDPOINT, facility_id)
    resp = send_request(url, {})
    return resp["facility_name"]


def get_num_available_sites(resp, start_date, end_date):
    maximum = resp["count"]
    num_available = 0
    num_days = (end_date - start_date).days
    dates = [end_date - timedelta(days=i) for i in range(1, num_days + 1)]
    dates = set(format_date(i) for i in dates)
    for site in resp["campsites"].values():
        available = bool(len(site["availabilities"]))
        for date, status in site["availabilities"].items():
            if date not in dates:
                continue
            if status != "Available":
                available = False
                break
        if available:
            num_available += 1
            LOG.debug("Available site {}: {}".format(num_available,
                json.dumps(site, indent=1)))
    return num_available, maximum


def valid_date(s):
    try:
        return datetime.strptime(s, INPUT_DATE_FORMAT)
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def timed_entry(facility_ids, date):
    out = []
    availabilities = False
    for facility_id in facility_ids:
        name_of_site = get_name_of_facility(facility_id)
        out.append("{} ({})".format(name_of_site, date.strftime(INPUT_DATE_FORMAT)))
        timeslots = get_num_available_tickets(facility_id, date)
        for timeslot in timeslots:
            inventory = timeslot["inventory_count"]["ANY"]
            available = inventory - timeslot["reservation_count"]["ANY"]
            out.append(" - {}: {} of {} tickets available".format(
                timeslot["tour_time"], available, inventory))
            if available:
                availabilities = True
        if available:
            print("\n".join(out))
            print("\nBooking URL(s):")
            for facility_id in facility_ids:
                print(BASE_URL + TICKET_BOOKING_URL.format(facility_id))
    return availabilities


def campgrounds(campground_ids, start_date, end_date):
    out = []
    available_campground_ids = []
    availabilities = False
    for campground_id in campground_ids:
        params = generate_params(start_date, end_date)
        LOG.debug("Querying for {} with these params: {}".format(
            campground_id, params))
        campground_information = get_campground_information(campground_id, params)
        LOG.debug(
            "Information for {}: {}".format(
                campground_id, json.dumps(campground_information, indent=1)
            )
        )
        name_of_site = get_name_of_campground(campground_id)
        current, maximum = get_num_available_sites(
            campground_information, args.start_date, args.end_date
        )
        if current:
            emoji = SUCCESS_EMOJI
            availabilities = True
            available_campground_ids.append(campground_id)
        else:
            emoji = FAILURE_EMOJI

        out.append(
            "{} {} of {} site(s) available at {} ({})".format(
                emoji, current, maximum, name_of_site, campground_id
            )
        )

    if availabilities:
        print(
            "[{}] There *are* campsites available from {} to {}:".format(
                format_datetime(datetime.now()),
                args.start_date.strftime(INPUT_DATE_FORMAT),
                args.end_date.strftime(INPUT_DATE_FORMAT),
            )
        )
    else:
        print("[{}] There are no campsites available:".format(format_datetime(
            datetime.now())))

    print("\n".join(out))

    if availabilities:
        print("\nBooking URL(s):")
        for campground_id in available_campground_ids:
            print(BASE_URL + CAMPGROUND_BOOKING_URL.format(campground_id))

    return availabilities


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", "-d", action="store_true", help="Debug log level")
    parser.add_argument("--timed-entry", "-t", action="store_true", help="Timed entry ticket mode")
    parser.add_argument(
        "--start-date", help="Start date [YYYY-MM-DD]", type=valid_date
    )
    parser.add_argument(
        "--end-date",
        required=False,
        help="End date [YYYY-MM-DD]. You expect to leave this day, not stay the night.",
        type=valid_date,
    )
    parser.add_argument(
        "--date", help="Date [YYYY-MM-DD]", type=valid_date
    )
    parser.add_argument(
        dest="site_ids", metavar="site_id", nargs="+", help="Recreation.gov campground/facility ID(s)", type=int
    )
    parser.add_argument(
        "--stdin",
        "-",
        action="store_true",
        help="Read list of Recreation.gov site ID(s) from stdin",
    )

    args = parser.parse_args()

    if args.timed_entry and not args.date:
        parser.error("--date argument required in timed entry mode")
    if not args.timed_entry and (not args.start_date or not args.end_date):
        parser.error("--start-date and --end-date arguments required")

    if args.debug:
        LOG.setLevel(logging.DEBUG)

    site_ids = args.site_ids or [p.strip() for p in sys.stdin]
    try:
        if args.timed_entry:
            ret_val = timed_entry(site_ids, args.date)
        else:
            ret_val = campgrounds(site_ids, args.start_date, args.end_date)

        if ret_val:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception:
        print("Something went wrong")
        raise
