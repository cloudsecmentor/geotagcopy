from argparse import ArgumentParser

arg_parser = ArgumentParser()

arg_parser.add_argument('-f', '--folder', nargs='+',
            help='(geotag mode) Folder(s) where media files are located (will be overwritten!)')
arg_parser.add_argument('-r', '--recursive', action='store_true', default=False,
            help='(geotag mode) Browse folder recursively (default false)')
arg_parser.add_argument('-v', '--verbosity', type=int, default=2, choices=range(1, 4),
            help='Verbosity level (1-3, default 2)')
#argv = argv[1:]
#args = arg_parser.parse_args(argv)

args = arg_parser.parse_args()
args_text = ["-f", "./",  "sys", "-r", "-v", "1"]
args = arg_parser.parse_args(args_text)

print (args)
print (args.folder)






files = ["/Users/sergey/Pictures/iPhone X (S)/IMG_5987.HEIC", "/Users/sergey/Pictures/iPhone X (S)/IMG_5996.MOV"]

with exiftool.ExifToolHelper() as et:
    metadata = et.get_metadata(files)


for d in metadata:
    print("file:{}\n lat: {} lon:{} alt: {}".format(
        d["SourceFile"],
        d["Composite:GPSLatitude"],
        d["Composite:GPSLongitude"],
        d["Composite:GPSAltitude"]
        ))













import exiv2
import os

file_path = "/Users/sergey/Pictures/iPhone X (S)/IMG_5987.HEIC"
file_path = "/Users/sergey/Pictures/iPhone X (S)/IMG_5996.MOV"

image = exiv2.ImageFactory.open(file_path)

image.readMetadata()
data = image.exifData()
b = data.begin()
b.key()


data = image.exifData()
b = data.begin()
e = data.end()
while b != e:
    b.key()
    next(b)



arg_parser.add_argument('mode', choices=('simulate', 'geotag'),
            help=('"simulate mode": creates a clean locations.csv file from a Google LocationHistory.json'
                    'file. Geotagging arguments will be ignored. "geotag" mode: uses the coordinates file'
                    ' passed as argument to geotag all the JPEG pictures in the target folder. Conversion'
                    ' arguments will be ignored.'))
arg_parser.add_argument('-s', '--start-date', help='Start date (inclusive) for conversion, format YYYY-MM-DD')
arg_parser.add_argument('-e', '--end-date', help='End date (inclusive) for conversion, format YYYY-MM-DD')
#arg_parser.add_argument('-tz', '--timezone',
#            help='Time zone (e.g., "UTC", or "Europe/Zurich") of the camera. It will be simulateed to your local time zone prior to geotagging')
arg_parser.add_argument('-r', '--recursive', action='store_true', default=False,
            help='(geotag mode) Browse folder recursively (default false)')

