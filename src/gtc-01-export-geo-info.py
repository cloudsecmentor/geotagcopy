

import exiftool
import glob
import os
from argparse import ArgumentParser
import logging
import sys

def get_supported_extensions():
    file_extensions = ['jpg', 'jpeg', 'heic', 'mov', 'png', 'mp4']
    file_extensions += [x.upper() for x in file_extensions]
    
    return file_extensions


def get_timestamp():
    import datetime
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d-%H-%M-%S")
    return timestamp


def list_files_in_folder (folder='.', recursive=False):
    ## TODO: add filtering by date
    file_extensions = get_supported_extensions()
    matched_files = []
    for fe in file_extensions:
        if not recursive:
            matched_files.extend(glob.glob(os.path.join(folder, '*.%s' % fe)))
        else:
            for root, folders, files in os.walk(folder):
                matched_files.extend(glob.glob(os.path.join(root, '*.%s' % fe)))
    return matched_files

arg_parser = ArgumentParser()


#arg_parser.add_argument('mode', choices=('simulate', 'geotag'),
#            help=('"simulate mode": creates a clean locations.csv file from a Google LocationHistory.json'
#                    'file. Geotagging arguments will be ignored. "geotag" mode: uses the coordinates file'
#                    ' passed as argument to geotag all the JPEG pictures in the target folder. Conversion'
#                    ' arguments will be ignored.'))
arg_parser.add_argument('-s', '--start-date', help='Start date (inclusive) for conversion, format YYYY-MM-DD')
arg_parser.add_argument('-e', '--end-date', help='End date (inclusive) for conversion, format YYYY-MM-DD')

arg_parser.add_argument('-f', '--folder', nargs='+',
            help='Folder(s) where media files are located (will be overwritten!)')
arg_parser.add_argument('-o', '--outFolder', default="./data/",
            help='Folder where csv file will be created with timestamp')
arg_parser.add_argument('-r', '--recursive', action='store_true', default=True,
            help='(geotag mode) Browse folder recursively (default false)')
arg_parser.add_argument('-v', '--verbosity', type=int, default=2, choices=range(1, 4),
            help='Verbosity level (1-3, default 2)')

args = arg_parser.parse_args()

# for inline - remove for script
args_text = [   "-f",   "/Users/sergey/Pictures/iPhone Sergey", 
                        "/Users/sergey/Pictures/exports", 
                        "/Users/sergey/Pictures/iPhone Irina/iPhone12/106APPLE", 
                "-v", "1"]
args = arg_parser.parse_args(args_text)
# for inline - remove for script

print (args)
print (args.folder)


verbosity_logger = {1: logging.ERROR, 2: logging.INFO, 3: logging.DEBUG}
log_level = verbosity_logger[args.verbosity]
sh = logging.StreamHandler(stream=sys.stdout)  # logging to stdout
lf = logging.Formatter('%(levelname)s\t%(message)s')
sh.setFormatter(lf)
logger = logging.getLogger()
logger.addHandler(sh)
logger.setLevel(log_level)


media_files = []
for curr_folder in args.folder:
    media_files += list_files_in_folder(folder = curr_folder, recursive=args.recursive)

with exiftool.ExifToolHelper() as et:
    metadata = et.get_metadata(media_files)

import pandas as pd
media_metadata = pd.DataFrame.from_dict(metadata)

media_metadata.to_csv( (f"{args.outFolder}/media_metadata_{get_timestamp()}.csv").replace("//","/") )


print ("export done")

sys.exit() 

#########################