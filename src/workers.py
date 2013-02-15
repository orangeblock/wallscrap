import threading
import os
import re
import sys

class PageGrabber(threading.Thread):
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
                sys.stdout.write("Couldn't load page: %s\n" % url)

            self.q.task_done()

class WpGrabber(threading.Thread):
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
                sys.stdout.write('Retrieving: %s\n' % link)
            try:
                html = self.opener.open(link).read()
                soup = re.search(r'src="\'\+B\(\'([\w+/=]+)\'\)', html).group(1)
                self.out_q.put( soup.decode("base64") )
            except Exception:
                sys.stdout.write("Couldn't load: %s\n" % link)

            self.q.task_done()

class Downloader(threading.Thread):
    def __init__(self, q, opener, dest, verbose):
        threading.Thread.__init__(self)
        self.q = q
        self.opener = opener
        self.dest = dest
        self.verbose = verbose

    def run(self):
        while True:
            url = self.q.get()

            path = os.path.join(self.dest, url[url.rindex('/')+1 : ])
            if not os.path.exists(path):
                if self.verbose:
                    sys.stdout.write('Downloading: %s\n' % url)
                with open(path , 'wb') as f:
                    try:
                        f.write(self.opener.open(url).read())
                    except Exception:
                        sys.stdout.write("Couldn't write: %s\n" % path)

            self.q.task_done()