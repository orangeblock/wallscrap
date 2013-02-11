"""

    Created by orangeblock
    https://github.com/orangeblock

    An argument parser for use with the wallbase scraper.

"""
import argparse
import re

def parse_args():
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


    parser = argparse.ArgumentParser(description='A handy scraping tool for wallbase.cc!', epilog='Made by orangeblock.', version="1.0")


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
    ###===---</ Filters >---===###

    ###===---< File System >---===###
    files = parser.add_argument_group('File System')
    
    # Destination directory
    files.add_argument('dest', nargs='?', default='temp',
                        help='Specify target directory (default: ./temp)')
    ###===---</ File System >---===###

    return parser.parse_args()