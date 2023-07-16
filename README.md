# GPS Tag Copy Utility

This is a tool designed to add location information, also known as GPS tags, to photos taken by a camera that does not support or lacks GPS tags. This is particularly useful when you want to sort photos not only by date but also by location. 

## Problem Statement

Cameras such as the Sony A6000 take wonderful pictures but lack the ability to add location information. Photos and videos taken with a mobile device like iPhone X contain location information, but the same is not true for screenshots or other types of media. There are apps available that allow you to transfer the information from your phone's GPS tracker if you're taking pictures with your camera, but they are not retroactive, leaving older photos without location tags. This tool is designed to address these gaps.

## Solution

This utility transfers the location information from an iPhone photo to the photo without GPS. It finds the closest photo in time on the iPhone that has a GPS tag. The time difference between the two should be the smallest. Once it finds the photo, it copies the GPS coordinates from the iPhone photo onto the photo from the camera.

## Implementation

The utility comprises three modules written in Python and R. The Python module collects information about the files and uses the Exif tool to add information about these files. The R module is used to find the closest photo in time with GPS coordinates for a photo that does not have GPS coordinates.

This tool also accommodates situations with multiple authors. Different people might be walking around with different phones, hence there may be different sources of geolocation data.

## Usage

See details in
´´´
python3 src/gtc-01-export-geo-info.py -h
´´´

The tool provides a visual interface that lets you compare which exact photos are going to receive new GPS coordinates and from where they'll get them. You can approve and confirm the application of a geotag or reject it. After you've reviewed the proposals and if you're happy with them, you can approve all the suggested GPS positions.

Once you've approved, you can apply the data. For each file that it changes, the system adds a specific label stating that a GPS copy happened for that file, and it adds information about from which file the GPS coordinates were taken. 

Once all the information is updated, you can search your files, not only by when the shot was taken but also by the location. 

## Results

After using this utility, you can import the updated photos into programs like Adobe Lightroom and do a search by address. For example, having GPS coordinates, you could set a city and search by city. The utility adds a label called 'GPS copy' to photos that have had their GPS info transferred from some other photo. 

This utility has proved beneficial in managing a large number of photos taken over time with different devices. 


## Similar repos and links used
https://github.com/nperony/pybatchgeotag/blob/master/pybatchgeotag.py


https://github.com/kburchfiel/media_geotag_mapper


https://www.youtube.com/watch?v=5MIYyw9E2wY


https://pypi.org/project/geotagger/


https://python3-exiv2.readthedocs.io/en/latest/tutorial.html#reading-and-writing-exif-tags


https://exiftool.org/

