

from PIL import ImageTk, Image
import tkinter as tk
import argparse
import pandas as pd

# create the argument parser
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--filename', help='path to the CSV file')

# testing
args = parser.parse_args(
    ['-f', 'data/media_metadata_2023-05-03-17-01-46-recs-2023-05-04-23-33-54.csv'])

# parse the command-line arguments
# args = parser.parse_args()

# read the CSV file into a pandas DataFrame
df = pd.read_csv(args.filename)

df_files_only = df.filter(like='SourceFile')

df_suggested = df_files_only[df_files_only['suggested.SourceFile'].notna()]

df_suggested


########################

import tkinter as tk
from PIL import Image, ImageTk

# Create a Tkinter window
root = tk.Tk()

# Define the geometry of the window
root.geometry("1200x600")

# Read the data from the dataframe
img_paths = df_suggested['SourceFile'].tolist()
suggested_img_paths = df_suggested['suggested.SourceFile'].tolist()

# Create a label for the title

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

# Define the latitude and longitude values
img_latitude = 40.7128
img_longitude = -74.0060

map_widget = TkinterMapView(root, corner_radius=0)
map_widget.place(x=750, y=410, width=300, height=180)
# pack(fill="both", expand=True)

# google normal tile server
map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)

map_widget.set_position(img_latitude, img_longitude, marker=True)

# Define a function to rescale the image

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


# # Display the first image in the list
# current_img_path = img_paths[0]
# current_img_tk = rescale_and_update_image(current_img_path, img_label)
# suggested_img_path = suggested_img_paths[0]
# suggested_img_tk = rescale_and_update_image(suggested_img_path, suggested_img_label)
# current_img = Image.open(current_img_path)
# suggested_img = Image.open(suggested_img_path)


# Define functions to handle button clicks

def change_images(direction):
    global current_img_path, current_img_tk, img_paths, current_img
    global suggested_img_path, suggested_img_tk, suggested_img_paths, suggested_img

    # Get the index of the previous image
    if (direction == "next"):
        index = img_paths.index(current_img_path) + 1
        # If we're at the end of the list, wrap around to the beginning
        if index >= len(img_paths):
            index = 0
    elif (direction == "prev"):
        index = img_paths.index(current_img_path) - 1
        # If we're at the beginning of the list, wrap around to the end
        if index < 0:
            index = len(img_paths) - 1
    elif (direction == "start"):
        index = 0
    else:
        print(f"Unsupported direction [{direction}]")
        exit()

    # Load the previous image
    current_img_path = img_paths[index]
    suggested_img_path = suggested_img_paths[index]
    print (current_img_path, suggested_img_path, index)
    # Schedule the rescaling and updating of the image label
    delay_after = 1
    root.after(delay_after, rescale_and_update_image(current_img_path, img_label))
    root.after(delay_after, rescale_and_update_image(suggested_img_path, suggested_img_label))



# # Display the first image in the list
change_images("start")

# Create buttons to go to the previous and next images
button_width=10
button_height=3
prev_button = tk.Button(root, 
                        text='<< Previous', 
                        command=lambda: change_images("prev"), 
                        width=button_width, 
                        height=button_height)
# prev_button.pack(side='left')
prev_button.place(x=0, y=100)
next_button = tk.Button(root, 
                        text='Next >>', 
                        command=lambda: change_images("next"), 
                        width=button_width, 
                        height=button_height)
# next_button.pack(side='right')
next_button.place(x=0, y=150)


# Start the Tkinter event loop
root.mainloop()


