#!/usr/bin/python

import os
import sys


###############################################################
# List of path completion functions
###############################################################
#
# Each path completer is a simple function than take the pattern as
# argument and return a iterator that returns each possible
# completions.
#
# A completer function definition must be wrapped in a try/except
# block if it depends on python modules that are not part of standard
# libraries and are not guaranteed to be installed:
#

available_completers = {}

def register_completer(name):
    """Decorator that registers a path completer function 
       in the global map of available completers
    """
    def real_register(func):
        available_completers[name] = func
        return func

    return real_register


#
# Path completer that works like the native alot one
#
import glob

@register_completer('native')
def native_complete(pattern):
    """Find all the paths matching the pattern by
       simply looking on the filesystem
    """
    return glob.iglob(pattern + '*')


#
# Path completer based on the recoll desktop search tool
#
try:
    from recoll import recoll
    import urlparse
    import urllib

    @register_completer('recoll')
    def recoll_complete(pattern):
        """Use the recoll desktop search tools index
           to quicly locate all filenames maching the 
           pattern, whatever the location on the filesystem
        """

        # 1 or 2 characters would bring way too much results
        if len(pattern) <= 2:
            return

        db = recoll.connect()
        search_data = recoll.SearchData()
        search_data.addclause('filename', pattern + '*')
        query = db.query()
        nres = query.executesd(search_data)

        for _ in range(nres):
            item = query.fetchone() 
            uri = urlparse.urlparse(item.get('url'))
            if uri.scheme != 'file':
                continue

            path = urllib.unquote(uri.path)

            # The recoll database is not garantued to be up to date
            # so we also test if the file really exists
            if (os.path.basename(path).startswith(pattern)
                    and os.path.exists(path)):
                yield path
except:
    pass

#
# Path completer based on Gnome Recent Documents list
#
try:
    import pygtk
    import gtk
    import urlparse
    import urllib

    @register_completer('gnome-recent-docs')
    def gnome_recent_documents_complete(pattern):
        """Find the files maching the pattern amongst the list
           of recently opened document maintained by gnome
        """
        manager = gtk.recent_manager_get_default()

        for item in manager.get_items():
            uri = urlparse.urlparse(item.get_uri())
            if uri.scheme != 'file':
                continue

            path = urllib.unquote(uri.path)
            # The recent documents list can contains files that
            # have been deleted in the meantime so we also test
            # if the file really exists
            if (os.path.basename(path).startswith(pattern)
                    and os.path.exists(path)):
                yield path
except:
    pass

    
###############################################################
# Main code
###############################################################

import inspect
from optparse import OptionParser


parser = OptionParser()
parser.add_option("-c", "--completers", dest="completers", help="list of completion mechanisms to use",
        metavar="COMPLETION,...", default="native")

options, args = parser.parse_args()
search_pattern = ' '.join(args) if args else ''


try:
    selected_completers = [ available_completers[name] for name in options.completers.split(',') ]
except KeyError as e:
    sys.stderr.write("ERROR: Completion mechanisms %s is unknown or not available\n" % e.message)
    sys.exit(2)

existing_completions = set()

for completer in selected_completers:
    candidate_completions = completer(search_pattern)
    for completion in candidate_completions:
        if not completion in existing_completions:
            existing_completions.add(completion)
            print completion

