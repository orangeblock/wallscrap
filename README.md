#Wallscrap

## Description
A handy wallbase.cc scraper to be used through the command line.
It uses only core python libraries, so you shouldn't need to download anything else.

Tested under Windows 7 x64 and Ubuntu 12.04 x86. Python version is 2.7.

##Commands
To download 50 random wallpapers use:

`python wallscrap.py` or `python wallscrap.py -r`  

To download a collection use:

`python wallscrap.py -c <url>`

where `<url>` must be a valid wallbase url.  


To make a query and download the results use:

`python wallscrap.py -s <query>`

The default download amount is 50. To change that use the `-a` flag like so:

`python wallscrap.py -a 100`  

Of course you can mix these up and add filters like resolution, purity, board, etc. For a complete listing type:

`python wallscrap.py --help`  

###License
Check LICENSE.txt.
