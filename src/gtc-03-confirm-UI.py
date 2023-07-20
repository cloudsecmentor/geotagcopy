

from pillow_heif import register_heif_opener
from tkintermapview import TkinterMapView
from PIL import Image, ImageTk
from PIL import ImageTk, Image
import tkinter as tk
import argparse
import pandas as pd
import numpy as np

# create the argument parser
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--filename', help='path to the CSV file')

# testing
args = parser.parse_args(
    ['-f', 'data/media_metadata_2023-05-03-17-01-46-recs-2023-05-04-23-33-54.csv'])

# parse the command-line arguments
args = parser.parse_args()

# read the CSV file into a pandas DataFrame
df = pd.read_csv(args.filename)
# filter only values which have a suggestion for GPS value
_df = df[df['suggested.SourceFile'].notna()].reset_index(drop=True)
# make sure that 'suggested.time.diff' is present and sort df by it descending (so that we review largest time diff first)
media_df = _df[_df['suggested.time.diff'].notna()].sort_values(by='suggested.time.diff', ascending=False).reset_index(drop=True)

if 'suggested.approved' not in media_df.columns:
    media_df['suggested.approved'] = np.nan


########################


# Create a Tkinter window # Define the geometry of the window
root = tk.Tk()
root.geometry("1200x600")


# Create a label to display the image
img_label = tk.Label(root)
img_label.place(x=150, y=100)
img_title_label = tk.Label(root, text="Image without geotag")
img_title_label.place(x=300, y=50, anchor='center')

# Create a label to display the suggested image
suggested_img_label = tk.Label(root)
suggested_img_label.place(x=750, y=100)
suggested_title_label = tk.Label(root, text="Copy geotag from image")
suggested_title_label.place(x=900, y=50, anchor='center')


map_widget = TkinterMapView(root, corner_radius=0)
map_widget.place(x=750, y=410, width=300, height=180)
# pack(fill="both", expand=True)


# Define a function to to detect video


# Define a function to rescale the image
def rescale_image(img, width, height):
    width = 300
    height = 300
    # Calculate the new size of the image while preserving the aspect ratio
    aspect_ratio = img.width / img.height
    if width / aspect_ratio < height:
        new_width = int(width)
        new_height = int(width / aspect_ratio)
    else:
        new_width = int(height * aspect_ratio)
        new_height = int(height)
    # Resize the image and return it as a PhotoImage object
    img = img.resize((new_width, new_height))
    return ImageTk.PhotoImage(img)


# to handle HEIC files
register_heif_opener()


# Define a function to rescale the image
def rescale_and_update_image(img_path, img_label):
    img = Image.open(img_path)
    # Rescale the image
    img_tk = rescale_image(img, img_label.winfo_width(),
                           img_label.winfo_height())
    # Update the label
    img_label.config(image=img_tk)
    img_label.image = img_tk


# Extract first frame of video file
def extract_first_frame(img_path):
    import cv2
    import os
    import tempfile
    import mimetypes
    # Check the file type
    mime_type = mimetypes.guess_type(img_path)[0]

    if mime_type and mime_type.startswith('video'):
        # Create a VideoCapture object
        vidcap = cv2.VideoCapture(img_path)

        # Read the first frame
        success, image = vidcap.read()

        if not success:
            raise Exception("Could not read video file")

        # Create a temporary directory
        tmp_dir = tempfile.gettempdir()

        # Create a path for the new image
        img_name = os.path.basename(img_path) + "_frame1.jpg"
        img_path = os.path.join(tmp_dir, img_name)

        # Save the image
        cv2.imwrite(img_path, image)

    # Return the path to the image
    return img_path


def convert_hours(hours):
    # Constants
    minutes_per_hour = 60
    hours_per_day = 24
    days_per_month = 30.44
    days_per_year = 365.25

    # Conversion
    minutes = (hours - int(hours)) * minutes_per_hour
    hours = int(hours)
    days = hours // hours_per_day
    hours %= hours_per_day
    months = days // days_per_month
    days %= days_per_month
    years = months // 12
    months %= 12

    # Create the result string
    time_string = ""
    if years > 0:
        time_string += f"{int(years)} years, "
    if months > 0:
        time_string += f"{int(months)} months, "
    if days > 0:
        time_string += f"{int(days)} days, "
    if hours > 0:
        time_string += f"{int(hours)} hours, "
    if minutes > 0:
        time_string += f"{int(minutes)} minutes"

    # Remove trailing comma and space if they exist
    time_string = time_string.rstrip(", ")

    return time_string


# Define functions to load images
def change_images(direction, n=1):
    global current_index, media_df, map_widget, img_title_label
    # global current_img_tk, current_img,
    # global suggested_img_tk, suggested_img

    # Get the index of the previous image
    if (direction == "next"):
        current_index = current_index + n
        # If we're at the end of the list, wrap around to the beginning
        if current_index >= len(media_df):
            current_index = 0
    elif (direction == "prev"):
        current_index = current_index - n
        # If we're at the beginning of the list, wrap around to the end
        if current_index < 0:
            current_index = len(media_df) - n
    elif (direction == "start"):
        current_index = 0
    else:
        print(f"Unsupported direction [{direction}]")
        exit()

    # Load the previous image
    current_img_path = media_df.loc[current_index, 'SourceFile']
    suggested_img_path = media_df.loc[current_index, 'suggested.SourceFile']

    # checking if the file is video and getting first frame
    current_img_path = extract_first_frame(current_img_path)
    suggested_img_path = extract_first_frame(suggested_img_path)

    print(current_img_path, suggested_img_path, current_index)
    # Schedule the rescaling and updating of the image label
    delay_after = 1
    root.after(delay_after, rescale_and_update_image(
        current_img_path, img_label))
    root.after(delay_after, rescale_and_update_image(
        suggested_img_path, suggested_img_label))

    # Define the latitude and longitude values
    img_latitude = media_df.loc[current_index, 'suggested.cust.GPSLatt']
    img_longitude = media_df.loc[current_index, 'suggested.cust.GPSLong']
    # google normal tile server
    map_widget.delete_all_marker()
    map_widget.set_tile_server(
        "https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
    map_widget.set_position(img_latitude, img_longitude, marker=True)
    # set the zoom level
    map_widget.set_zoom(5)

    # Display approval status
    approval_status = media_df.loc[current_index, 'suggested.approved']
    if (pd.isna(approval_status)):
        approval_status = "Not defined"
    else:
        if (approval_status):
            approval_status = "Approved"
        else:
            approval_status = "Rejected"
    img_title_label.configure(text=f"""
                              Image without geotag
                              Approval: {approval_status}
                              File: {media_df.loc[current_index, 'SourceFile'] }
                              Date: {media_df.loc[current_index, 'cust.MediaDate']}
                              Time diff (h): {convert_hours(media_df.loc[current_index, 'suggested.time.diff']) }
                            """,
                              justify='left')

    # display suggested image info
    suggested_title_label.configure(text=f"""
                            Copy geotag from image
                                    
                            File: {media_df.loc[current_index, 'suggested.SourceFile'] }
                            Date: {media_df.loc[current_index, 'suggested.cust.MediaDate']}
                        """,
                                    justify='left')


# # Display the first image in the list
change_images("start")


def confirm_suggestion(action):
    print(action)
    if (action == "approve"):
        media_df.loc[current_index, 'suggested.approved'] = True
    elif (action == "reject"):
        media_df.loc[current_index, 'suggested.approved'] = False
    else:
        print(f"Unsupported confirmation [{action}]")
        exit()
    change_images("next")


def bulk_confirm(action):
    print(f"Bulk action: {action}")
    if (action == "approve"):
        media_df['suggested.approved'] = True
    elif (action == "reject"):
        media_df['suggested.approved'] = False
    else:
        print(f"Unsupported confirmation [{action}]")
        exit()


def add_gps_to_image(row):
    import subprocess
    if pd.notnull(row['suggested.approved']) and row['suggested.approved']:
        # print(f"Applying GPS data to file: {row['SourceFile']}")
        comment_text = f"GPS data is copied from the file {row['suggested.SourceFile']}"
        label_text = "GPSCopy"
        subprocess.run(["exiftool", 
                        "-overwrite_original_in_place",
                        f"-Label={label_text}",
                        f"-Comment={comment_text}",
                        f"-DMComment={comment_text}",
                        f"-XMP:UserComment={comment_text}",
                        f"-XMP:GPSAltitude=\"{str(row['suggested.cust.GPSAlt'])}\"",
                        f"-XMP:GPSLongitude=\"{str(row['suggested.cust.GPSLong'])}\"",
                        f"-XMP:GPSLatitude=\"{str(row['suggested.cust.GPSLatt'])}\"",
                       row['SourceFile']],
                       check=True)


from tqdm import tqdm

def apply_gps_data():
    for i in tqdm(media_df.index, total=media_df.shape[0]):
        row = media_df.loc[i]
        add_gps_to_image(row)
    print("All approved changes has been implemented")


# def apply_gps_data():
#     # Apply the function to each row in media_df where 'suggested.approved' is True
#     media_df.apply(add_gps_to_image, axis=1)
#     print("All approved changes has been implemented")


def close(save):
    # Save data before closing the window
    # media_df.to_csv("data.csv")
    if save:
        media_df.to_csv(args.filename)
        print("Saving on_close")
    else:
        print("Exit without save")
    root.destroy()


# Create buttons to go to the previous and next images
button_width = 10
button_height = 3
prev_button = tk.Button(root,
                        text='<< Previous',
                        command=lambda: change_images("prev"),
                        width=button_width,
                        height=button_height).place(x=2, y=100)

next_button = tk.Button(root,
                        text='Next >>',
                        command=lambda: change_images("next"),
                        width=button_width,
                        height=button_height).place(x=2, y=150)

next_10_button = tk.Button(root,
                           text='Next 10 >>',
                           command=lambda: change_images("next", 10),
                           width=button_width,
                           height=button_height).place(x=2, y=200)

approve_button = tk.Button(root,
                           text='Approve >>',
                           command=lambda: confirm_suggestion("approve"),
                           width=button_width,
                           height=button_height).place(x=2, y=250)

reject_button = tk.Button(root,
                          text='Reject >>',
                          command=lambda: confirm_suggestion("reject"),
                          width=button_width,
                          height=button_height).place(x=2, y=300)

approve_all_button = tk.Button(root,
                               text='Approve all',
                               command=lambda: bulk_confirm("approve"),
                               width=button_width,
                               height=button_height).place(x=2, y=350)


close_save_button = tk.Button(root,
                              text='Save and close',
                              command=lambda: close(save=True),
                              width=button_width,
                              height=button_height).place(x=2, y=400)

close_nosave_button = tk.Button(root,
                                text='Close w/o saving',
                                command=lambda: close(save=False),
                                width=button_width,
                                height=button_height).place(x=2, y=450)

apply_gps_data_button = tk.Button(root,
                                text='Apply GPS data',
                                command=lambda: apply_gps_data(),
                                width=button_width,
                                height=button_height).place(x=2, y=500)


# Bind the on_close function to the WM_DELETE_WINDOW protocol
root.protocol("WM_DELETE_WINDOW", lambda: close(save=False))

# Start the Tkinter event loop
root.mainloop()
