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
from parse import *
from workers import *

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

# TODO: Refactor
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

    print 'Retrieving urls...'
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

    # spawn threads to copy the wallpapers
    for i in range(concurrent):
        t = Downloader(copy_queue, opener, args.dest, args.verbose)
        t.setDaemon(True)
        t.start()

    # leave only up to given amount of wps
    total = args.a if temp_queue.qsize() > args.a else temp_queue.qsize()
    print 'Copying wallpapers...'
    for i in range(total):
        wp_queue.put(temp_queue.get())

    while wp_queue.unfinished_tasks > 0:
        time.sleep(1)

    while copy_queue.unfinished_tasks > 0:
        time.sleep(1)

    print 'Done.'
    print 'Total time: {}s'.format(time.time() - start)

if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print 'KeyboardInterrupt'