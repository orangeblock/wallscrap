#!/bin/usr/env python
"""

    Created by orangeblock
    https://github.com/orangeblock

    A handy scraping tool for wallbase.cc.
    Uses multithreading and only core python libraries.

    See the changelog section in the README for a list of changes.

"""
import re
import os
import sys
import time
import urllib
import urllib2
import shutil
import random
import Queue
import cookielib
import getpass
import argparse
import threading


class PageGrabber(threading.Thread):
    """
        Worker class - grabs all the wp links present on a page,
        and pushes them in the supplied output queue.
    """
    def __init__(self, q, out_q, opener):
        threading.Thread.__init__(self)
        self.q = q
        self.out_q = out_q
        self.opener = opener

    def run(self):
        while True:
            url, data = self.q.get()

            try:
                html = self.opener.open(url, data).read()

                for link in re.findall(r'<a href="(http://wallbase.cc/wallpaper/\w+)"', html):
                    self.out_q.put(link)
            except Exception:
                print "Couldn't load page: %s\n" % url,

            self.q.task_done()


class WpGrabber(threading.Thread):
    """
        Worker class - opens each link present in the input queue and extracts
        the link for the full-size image, similar to Right click -> View Image.
        Then it pushes that link in the output queue.
    """
    def __init__(self, q, out_q, amount, opener, verbose):
        threading.Thread.__init__(self)
        self.q = q
        self.out_q = out_q
        self.opener = opener
        self.verbose = verbose

    def run(self):
        while True:
            link = self.q.get()

            if self.verbose:
                print 'Retrieving %s\n' % link,
            try:
                html = self.opener.open(link).read()
                soup = re.search(r'src="\'\+B\(\'([\w+/=]+)\'\)', html).group(1)
                self.out_q.put( soup.decode("base64") )
            except Exception:
                print "Couldn't load: %s\n" % link,

            self.q.task_done()


class Downloader(threading.Thread):
    """
        Worker class - opens each supplied link
        and downloads it to the destination folder.
        Also, counts the total number of downloads using the supplied counter.
    """
    def __init__(self, q, opener, dest, verbose, counter):
        threading.Thread.__init__(self)
        self.q = q
        self.opener = opener
        self.dest = dest
        self.verbose = verbose
        self.counter = counter

    def run(self):
        while True:
            url = self.q.get()

            path = os.path.join(self.dest, url[url.rindex('/')+1 : ])
            if not os.path.exists(path):
                if self.verbose:
                    print 'Downloading: %s\n' % url,
                with open(path , 'wb') as f:
                    try:
                        f.write(self.opener.open(url).read())
                        self.counter.incr()

                        if self.verbose:
                            print 'Finished: %s\n' % path,
                    except Exception:
                        print "Couldn't write: %s\n" % path,
            else:
                self.counter.incr()
                if self.verbose:
                    print 'Duplicate of %s found. Skipping...\n' % path,

            self.q.task_done()


def parse_args():
    """
        Parses the command line and returns the parsed args.
    """
    ###===---< Type functions >---===###
    def res_format(res):
        if not re.match(r'\d+x\d+$', res):
            raise argparse.ArgumentTypeError('Invalid format, use one like "1024x768".')
        return res

    def ar_format(ar):
        if not re.match(r'\d+:\d+$', ar):
            raise argparse.ArgumentTypeError('Invalid format, use one like "16:9".')
        ar = ar.split(':')
        # 16:9 --> 1.78, 4:3 --> 1.33, etc.
        return '{0:.2f}'.format(float(ar[0])/float(ar[1]))

    def n_format(n):
        if not re.match(r'[yn][yn][yn]$', n):
            raise argparse.ArgumentTypeError('Invalid format, use one like "yyn". See help for more info.')
        # yyn --> 110, yny --> 101, etc. 
        return ''.join( map(lambda x: '1' if x == 'y' else '0', n) )

    def cat_format(cat):
        if not re.match(r'[yn][yn][yn]$', cat):
            raise argparse.ArgumentTypeError('Invalid format, use one like "yyn". See help for more info.')
        # yyn --> 21, yny --> 23, nny --> 3, nyy --> 13, etc.
        format = '213'
        return ''.join( map(lambda x: format[x] if cat[x] == 'y' else '', range(3)) )

    def a_format(a):
        if int(a) < 0:
            raise argparse.ArgumentTypeError('Negative amount...')
        return int(a)

    def c_format(c):
        if not re.match(r'http://wallbase.cc/user/collection/\d+', c):
            raise argparse.ArgumentTypeError('Invalid collections format, use full link (copy from address bar).')
        return c
    ###===---</ Type functions >---===###


    parser = argparse.ArgumentParser(description='A handy scraping tool for wallbase.cc!', epilog='Made by orangeblock.')


    ###===---< Modes >---===###
    modes = parser.add_argument_group("Lookup modes").add_mutually_exclusive_group()

    # Random
    modes.add_argument('-r', action='store_true', default=True,
                       help='Random mode, default when no other mode selected.')

    # Search 
    modes.add_argument('-s', metavar='query', nargs=1,
                       help='Search mode - a query string is required.')

    # Collections
    modes.add_argument('-c', metavar='url', nargs=1, type=c_format,
                       help='Collections mode - a url is required.')
    ###===---</ Modes >---===###


    ###===---< Filters >---===###
    filters = parser.add_argument_group('Search filters')

    # Amount
    filters.add_argument('-a', metavar='amount', default=50, type=a_format,
                         help="Sets the amount of wps to be downloaded. (default: 50)")

    # Nudity
    filters.add_argument('-n', default='yyn', metavar='nudity_level', type=n_format,
                         help = 'Nudity filter. Combine the three options by using either y or n. The options are [SFW, Sketchy, NSFW] \
                         in that order and the usage is e.g. "nny" for NSFW only. (default: "yyn")')

    # Categories
    filters.add_argument('--cat', default='yyn', metavar='categories', type=cat_format,
                         help='Choose categories. Combine as with nudity filter. Options are [Wallpapers/General, Anime, High-Res]. \
                         (default: "yyn")')

    # Aspect Ratio
    filters.add_argument('--ar', metavar='ratio', default=0, type=ar_format,
                         help='Desired aspect ratio. (e.g. 16:9)')

    # Resolution
    filters.add_argument('--res', metavar='resolution', default='0x0', type=res_format,
                         help='Desired resolution. Works together with ropt.')

    # Resolution relativity
    filters.add_argument('--ropt', default='eqeq', choices=['eqeq','gteq'],
                         help='Specify if matches should be either "exactly" or "at least" as the desired resolution. (default: "eqeq")')

    # Per page
    filters.add_argument('--pp', default='32', choices=['20','32','40','60'],
                         help='Sets the results per page. (default: 32)')

    # Verbose
    filters.add_argument('-v', '--verbose', action='store_true', default=False,
                         help='More verbosity')
    ###===---</ Filters >---===###

    ###===---< File System >---===###
    files = parser.add_argument_group('File System')
    
    # Destination directory
    files.add_argument('dest', nargs='?', default='temp',
                        help='Specify target directory (default: ./temp)')
    ###===---</ File System >---===###

    return parser.parse_args()

def get_opener():
    """ Returns a url opener, equipped with cookie storage """
    cookies = cookielib.CookieJar()
    return urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies))

def auth(opener):
    """ Attempts to log the user and returns the status """
    if raw_input("Would you like to login?[y/n]") in ['y','Y']:
        while True:
            usr = raw_input("Username: ")
            psw = getpass.getpass('Password(hidden): ')

            login_data = urllib.urlencode({'usrname' : usr, 'pass' : psw})
            html = opener.open('http://wallbase.cc/user/login', login_data).read()
            if re.search(r'Wrong username or password', html):
                if not raw_input('Warning: Wrong username or password. Retry?[y/n]: ') in ['y','Y']:
                    break
            else:
                return True
    return False

def get_search_query(args):
    query = urllib.urlencode({ 'query' : args.s[0], 
                               'board' : args.cat,
                               'res_opt' : args.ropt,
                               'res' : args.res,
                               'aspect' : args.ar,
                               'nsfw': args.n,
                               'thpp' : args.pp,
                               'orderby' : 'relevance',
                               'orderby_opt' : 'desc'})
    return query

def get_urls(args):
    """ Return a list of all links to be accessed and the data to be supplied. """
    urls = []
    data = None

    if args.s:
        base = 'http://wallbase.cc/search/'
        data = get_search_query(args)
        scroller = lambda x: str( int(x)*len(urls) )
    elif args.c:
        args.n = '1' if args.n[2] == 'y' else '0'
        base = args.c[0] + '/' + args.n + '/'
        scroller = lambda x: str( 32*len(urls) )
    else:
        base = 'http://wallbase.cc/random/'+args.cat+'/'+args.ropt+'/'+args.res+'/'+str(args.ar)+'/'+args.n+'/'+args.pp+'/'
        scroller = lambda x: str( int(random.random()*1000) )

    # add pages until amount arg is reached, rounded up to the nearest multiple of per page arg.
    while int(args.pp)*len(urls) < args.a:
        urls.append(base + scroller(args.pp))

    return urls, data

def run():
    args = parse_args()    
    opener = get_opener()
    page_queue = Queue.Queue()
    wp_queue = Queue.Queue()
    copy_queue = Queue.Queue()
    temp_queue = Queue.Queue()
    concurrent = 32

    if not auth(opener):
        if re.match(r'[01][01]1$', args.n):
            print 'Cannot use NSFW option without logging in.'
            sys.exit()

    # create dest folder
    try:
        if not os.path.exists(args.dest):
            os.makedirs(args.dest)
    except Exception:
        print "Couldn't create destination directory. Do you have sufficient privileges?"
        sys.exit()

    start = time.time()

    # spawn threads to strip the page
    for i in range(10):
        t = PageGrabber(page_queue, temp_queue, opener)
        t.setDaemon(True)
        t.start()

    print 'Retrieving page urls...'
    urls, data = get_urls(args)
    for url in urls:
        page_queue.put( (url, data) )

    while page_queue.unfinished_tasks > 0:
        time.sleep(1)

    # spawn threads to open each wallpaper link
    for i in range(concurrent):
        t = WpGrabber(wp_queue, copy_queue, args.a, opener, args.verbose)
        t.setDaemon(True)
        t.start()

    # counter to keep track of total downloaded wps
    class Counter:
        def __init__(self):
            self.count = 0

        def incr(self):
            self.count += 1
    counter = Counter()
    # spawn threads to copy the wallpapers
    for i in range(concurrent):
        t = Downloader(copy_queue, opener, args.dest, args.verbose, counter)
        t.setDaemon(True)
        t.start()

    # leave only up to given amount of wps
    total = args.a if temp_queue.qsize() > args.a else temp_queue.qsize()

    print 'Downloading wallpapers...'
    for i in range(total):
        wp_queue.put(temp_queue.get())

    while wp_queue.unfinished_tasks > 0:
        time.sleep(1)
    while copy_queue.unfinished_tasks > 0:
        time.sleep(1)

    print 'Done.'
    print '{0}/{1} copied successfully'.format(counter.count, args.a)
    print 'Total time: {:.2f}s'.format(time.time() - start)

if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print 'KeyboardInterrupt'