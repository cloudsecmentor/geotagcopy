

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

media_df = df[df['suggested.SourceFile'].notna()].reset_index(drop=True)
if 'suggested.approved' not in media_df.columns:
    media_df['suggested.approved'] = np.nan


########################

import tkinter as tk
from PIL import Image, ImageTk

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

from tkintermapview import TkinterMapView


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


# Define a function to rescale the image

def rescale_and_update_image(img_path, img_label):
    img = Image.open(img_path)
    # Rescale the image
    img_tk = rescale_image(img, img_label.winfo_width(), img_label.winfo_height())
    # Update the label
    img_label.config(image=img_tk)
    img_label.image = img_tk


# Define functions to load images

def change_images(direction):
    global current_index, media_df, map_widget, img_title_label
    # global current_img_tk, current_img, 
    # global suggested_img_tk, suggested_img

    # Get the index of the previous image
    if (direction == "next"):
        current_index = current_index + 1
        # If we're at the end of the list, wrap around to the beginning
        if current_index >= len(media_df):
            current_index = 0
    elif (direction == "prev"):
        current_index = current_index - 1
        # If we're at the beginning of the list, wrap around to the end
        if current_index < 0:
            current_index = len(media_df) - 1
    elif (direction == "start"):
        current_index = 0
    else:
        print(f"Unsupported direction [{direction}]")
        exit()

    # Load the previous image
    current_img_path = media_df.loc[current_index, 'SourceFile']
    suggested_img_path = media_df.loc[current_index, 'suggested.SourceFile']
    print (current_img_path, suggested_img_path, current_index)
    # Schedule the rescaling and updating of the image label
    delay_after = 1
    root.after(delay_after, rescale_and_update_image(current_img_path, img_label))
    root.after(delay_after, rescale_and_update_image(suggested_img_path, suggested_img_label))


    # Define the latitude and longitude values
    img_latitude = media_df.loc[current_index, 'suggested.cust.GPSLatt']
    img_longitude = media_df.loc[current_index, 'suggested.cust.GPSLong']
    # google normal tile server
    map_widget.delete_all_marker()
    map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
    map_widget.set_position(img_latitude, img_longitude, marker=True)
    # set the zoom level
    map_widget.set_zoom(5)

    # Display approval status
    approval_status = media_df.loc[current_index, 'suggested.approved']
    if ( pd.isna(approval_status) ):
        approval_status = "Not defined"
    else:
        if(approval_status):
            approval_status = "Approved"
        else:
            approval_status = "Rejected"
    img_title_label.configure(text=f"Image without geotag: {approval_status}")






# # Display the first image in the list
change_images("start")

def confirm_suggestion(action):
    print (action)
    if (action == "approve"):
        media_df.loc[current_index, 'suggested.approved'] = True
    elif (action == "reject"):
        media_df.loc[current_index, 'suggested.approved'] = False
    else:
        print(f"Unsupported confirmation [{action}]")
        exit()
    change_images("next")

# Create buttons to go to the previous and next images
button_width=10
button_height=3
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

approve_button = tk.Button(root, 
                        text='Approve >>', 
                        command=lambda: confirm_suggestion("approve"), 
                        width=button_width, 
                        height=button_height).place(x=2, y=200)

reject_button = tk.Button(root, 
                        text='Reject >>', 
                        command=lambda: confirm_suggestion("reject"), 
                        width=button_width, 
                        height=button_height).place(x=2, y=250)

close_save_button = tk.Button(root, 
                        text='Close and save', 
                        command=lambda: close(save=True), 
                        width=button_width, 
                        height=button_height).place(x=2, y=300)


def close(save):
    # Save data before closing the window
        #media_df.to_csv("data.csv")
    if save:
        media_df.to_csv(args.filename)
        print ("Saving on_close")
    else:
        print ("Exit without save")
    root.destroy()

# Bind the on_close function to the WM_DELETE_WINDOW protocol
root.protocol("WM_DELETE_WINDOW", lambda: close(save=False) )

# Start the Tkinter event loop
root.mainloop()


