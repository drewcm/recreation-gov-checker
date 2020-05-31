# Campsite and Timed Entry Facility Availability Scraping

This script uses the https://recreation.gov API for campsite and time-entry facility availabilities.

## Example Usage

The `recreation.py` script can be used to search for campgrounds or timed-entry facilities.

### Campground Search
```
python recreation.py --start-date 2020-07-20 --end-date 2020-07-21 232463 232462 233187
[2019-07-22 11:07:52] There are no campsites available:
- 0 of 253 site(s) available at MORAINE PARK CAMPGROUND (232463)
- 0 of 160 site(s) available at GLACIER BASIN CAMPGROUND (232462)
- 0 of 54 site(s) available at ASPENGLEN CAMPGROUND (233187)
```

You can also read from stdin. Define a file (e.g. `parks.txt`) with IDs like this:
```
232463
232462
233187
```

and then use it like this:
```
python recreation.py --start-date 2020-07-20 --end-date 2020-07-23 --stdin < campgrounds.txt
```

### Timed-Entry Facility Search
```
python recreation.py --date 2020-07-21 --timed-entry 300013
```

You'll want to put this script into a 5 minute crontab. You could also grep the output for the success emoji (🏕) and then do something in response, like notify you that there is a campsite available. See the "Twitter Notification" section below.

## Getting campground IDs
What you'll want to do is go to https://recreation.gov and search for the campground you want. Click on it in the search sidebar. This should take you to a page for that campground, the URL will look like `https://www.recreation.gov/camping/campgrounds/<number>`. That number is the campground ID.

You can also take [this site for a spin](https://pastudan.github.io/national-parks/). Thanks to [pastudan](https://github.com/pastudan)!

## Installation

I wrote this in Python 3.7 but I've tested it as working with 3.5 and 3.6 also.
```
python3 -m venv myvenv
source myvenv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
# You're good to go!
```

## Development
This code is formatted using black and isort:
```
black -l 80 --py36 recreation.py
isort recreation.py
```

Feel free to submit pull requests, or look at the original: https://github.com/bri-bri/yosemite-camping

### Differences from the original
- Python 3 🐍🐍🐍.
- Campground IDs not hardcoded, passed via the CLI instead.
- Doesn't give you URLs for campsites with availabilities.
- Works with any campground out of the box, not just those in Yosemite like with the original.
- **Update 2018-10-21:** Works with the new recreation.gov site.

## Twitter Notification
If you want to be notified about campsite availabilities via Twitter (they're the only API out there that is actually easy to use), you can do this:
1. Make an app via Twitter. It's pretty easy, go to: https://apps.twitter.com/app/new.
2. Change the values in `twitter_credentials.py` to match your key values.
3. Pipe the output of your command into `notifier.py`. See below for an example.

```
python recreation.py --start-date 2020-07-20 --end-date 2020-07-21 232463 232462 233187 | python notifier.py @banool1
```

You'll want to make the app on another account (like a bot account), not your own, so you get notified when the tweet goes out.

**Thanks to https://github.com/bri-bri/yosemite-camping for getting me most of the way there for the old version.**
