

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

# Create a label to display the image
img_label = tk.Label(root)
img_label.place(x=150, y=0)

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

def rescale_and_update_image():
    global current_img_path, current_img_tk, current_img
    # Rescale the image
    current_img_tk = rescale_image(current_img, img_label.winfo_width(), img_label.winfo_height())
    # Update the label
    img_label.config(image=current_img_tk)

# Display the first image in the list
current_img_path = img_paths[0]
current_img = Image.open(current_img_path)
current_img_tk = rescale_and_update_image()
img_label.config(image=current_img_tk)
root.after(1, rescale_and_update_image)

# Define functions to handle button clicks

def prev_image():
    global current_img_path, current_img_tk, img_paths, current_img
    # Get the index of the previous image
    index = img_paths.index(current_img_path) - 1
    # If we're at the beginning of the list, wrap around to the end
    if index < 0:
        index = len(img_paths) - 1
    # Load the previous image
    current_img_path = img_paths[index]
    print (current_img_path)
    current_img = Image.open(current_img_path)
    # Schedule the rescaling and updating of the image label
    root.after(1, rescale_and_update_image)

def next_image():
    global current_img_path, current_img_tk, img_paths, current_img
    # Get the index of the next image
    index = img_paths.index(current_img_path) + 1
    # If we're at the end of the list, wrap around to the beginning
    if index >= len(img_paths):
        index = 0
    # Load the next image
    current_img_path = img_paths[index]
    print (current_img_path)
    current_img = Image.open(current_img_path)
    # Schedule the rescaling and updating of the image label
    root.after(1, rescale_and_update_image)

# Create buttons to go to the previous and next images
button_width=10
button_height=3
prev_button = tk.Button(root, 
                        text='<< Previous', 
                        command=prev_image, 
                        width=button_width, 
                        height=button_height)
# prev_button.pack(side='left')
prev_button.place(x=0, y=100)
next_button = tk.Button(root, 
                        text='Next >>', 
                        command=next_image, 
                        width=button_width, 
                        height=button_height)
# next_button.pack(side='right')
next_button.place(x=0, y=150)


# Start the Tkinter event loop
root.mainloop()


