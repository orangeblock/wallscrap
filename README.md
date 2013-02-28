#Wallscrap

## Description
A handy wallbase.cc scraper to be used through the command line.
It uses only core python libraries, so you shouldn't need to download anything else.

Tested under Windows 7 x64 and Ubuntu 12.04 x86. Python version is 2.7.

##Commands
To download 50 random wallpapers use:

`python wallscrap.py` or `python wallscrap.py -r`  

To download a collection (up to -a amount, see below) use:

`python wallscrap.py -c <url>`

where `<url>` must be a valid wallbase url.  


To make a query and download the results use:

`python wallscrap.py -s <query>`

For queries with more than one word use double quotes.

The default download amount is 50. To change that use the `-a` flag like so:

`python wallscrap.py -a 100`  

Of course you can mix these up and add filters like resolution, purity, board, etc. For a complete listing type:

`python wallscrap.py --help`  

##Changelog
v1.2

    * Merged code into a single file for easier portability. Everything works as before.

v1.1  

    * Program responds to keyboard interrupts (Ctrl+C).  
      Use them when program seems unresponsive (usually when internet connection crashes).

    * Doesn't download existing files twice (although if wallbase changes wp IDs,  
      this could lead to non-existent files not being downloaded). In general, you should not  
      use the same folder for consecutive downloads over a long period of time (say >1 hour),  
      unless wallbase actually has a constant unique ID for each wp.

    * More verbose output. Also, added -v/--verbose option for even more verbosity madness!  
    
v1.0  

    * Random, search and collections modes.

    * Supports board, nsfw, res, res_opt, aspect, perpage filters,
      as well as an amount argument.

    * Login option allowing access to nsfw content.

    * Defaults to 50 random wps if no arguments given.
    
###License
Check LICENSE.txt.
