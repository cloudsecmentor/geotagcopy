

import exiftool
import glob
import os
from argparse import ArgumentParser
import logging
import sys
import datetime
import pandas as pd

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

# Add a script description
arg_parser = ArgumentParser(description="""
This script is used for exporting media metadata into a csv file, 
then performing a series of operations such as filtering files by dates,
recursive search in directories, and enabling different levels of verbosity. 

The output of the script is a .csv file containing the media metadata filtered according to 
the start and end dates. The script also suggests the next command to execute and 
optionally executes it, based on user confirmation.
""")

# Adding the sample usage to the parser
arg_parser.usage = """

python3 src/gtc-01-export-geo-info.py -f [PATH_1 PATH_2] -o [CSV_DATA_FOLDER] -r [-s YYYY-MM-DD]

python3 src/gtc-01-export-geo-info.py -f '/Users/sergey/Pictures/iPhone Sergey/DCIM' '/Users/sergey/Pictures/a6000/2023/' -o data/2307/ -r -s 2023-07-01

"""
arg_parser.add_argument('-s', '--start-date', 
                    type=lambda s: pd.to_datetime(s), 
                    default=pd.to_datetime('1900-01-01'), 
                    help='Start date, format YYYY-MM-DD (default: 1900-01-01)')
arg_parser.add_argument('-e', '--end-date', 
                    type=lambda s: pd.to_datetime(s), 
                    default=datetime.datetime.now(), 
                    help='End date, format YYYY-MM-DD (default: current)')

arg_parser.add_argument('-f', '--folder', nargs='+',
            help='Folder(s) where media files are located (will be overwritten!)')
arg_parser.add_argument('-o', '--outFolder', default="./data/",
            help='Folder where csv file will be created with timestamp')
arg_parser.add_argument('-r', '--recursive', action='store_true', default=False,
            help='(geotag mode) Browse folder recursively (default false)')
arg_parser.add_argument('-v', '--verbosity', type=int, default=2, choices=range(1, 4),
            help='Verbosity level (1-3, default 2)')


# for inline - remove for script
args_text = [   "-f",   "/Users/sergey/Pictures/iPhone Sergey", 
                        "/Users/sergey/Pictures/exports", 
                        "/Users/sergey/Pictures/iPhone Irina/iPhone12/106APPLE", 
                "-v", "1"]
args = arg_parser.parse_args(args_text)
# for inline - remove for script

args = arg_parser.parse_args()


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
    logger.info(f"Adding folder: [{curr_folder}]")

with exiftool.ExifToolHelper() as et:
    metadata = et.get_metadata(media_files)

media_metadata = pd.DataFrame.from_dict(metadata)

# Update 'cust.MediaDate' column
def try_to_parse(date_str, format_str):
    try:
        return pd.to_datetime(date_str, format=format_str)
    except:
        return None

media_metadata['cust.MediaDate'] = media_metadata.apply(
    lambda row: try_to_parse(row['EXIF:DateTimeOriginal'], "%Y:%m:%d %H:%M:%S") 
                if pd.notnull(row['EXIF:DateTimeOriginal']) 
                else try_to_parse(row['QuickTime:CreateDate'], "%Y:%m:%d %H:%M:%S") 
                if pd.notnull(row['QuickTime:CreateDate']) 
                else None, 
    axis=1)

# filter by date
end_date = args.end_date
start_date = args.start_date
logger.info(f"Filtering dates from {start_date} to {end_date}")
media_metadata_filtered = media_metadata[(media_metadata['cust.MediaDate'] <= end_date) & 
                             (media_metadata['cust.MediaDate'] >= start_date)].reset_index(drop=True)

# save to csv
csv_file_name = (f"{args.outFolder}/media_metadata_{get_timestamp()}.csv").replace("//","/")
media_metadata_filtered.to_csv( csv_file_name )


logger.info("export done")


## execute next step
def exec_next_step (exec_command, force = False):
    import os
    logger.info ("\nSuggested next command:\n")
    logger.info (exec_command)
    print ("\nSuggested next command:\n")
    print (exec_command)
    resp = input('Execute? [Y/n]: ').strip().lower() if not force else "yes"

    if(resp == "" or resp[0] == "y"):
        logger.info("execute!")
        os.system(exec_command)
    else:
        logger.info("STOP")



### R analysis
next_command = f"Rscript r_analysis/metadata-01.R --file {csv_file_name}"
exec_next_step(next_command)

### Review and Apply GPS Data
next_command = f"python3 src/gtc-03-confirm-UI.py -f {csv_file_name}"
exec_next_step(next_command)



sys.exit() 

#########################