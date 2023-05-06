

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


#################
# GUI


# img_file = df_suggested.iloc[0, 0]
# img_file = '/Users/sergey/Documents/github/geotagcopy/data/tst.png'


# ##########

# # Create an instance of tkinter window
# win = tk.Tk()

# # Define the geometry of the window
# win.geometry("700x500")

# frame = tk.Frame(win, width=600, height=400)
# frame.pack()
# frame.place(anchor='center', relx=0.5, rely=0.5)

# # Open the image using PIL
# pil_img = Image.open(img_file)

# # Resize the image to fit the frame
# width, height = frame.winfo_width(), frame.winfo_height()
# if width and height:
#     ratio = min(width / pil_img.width, height / pil_img.height)
#     new_size = (int(pil_img.width * ratio), int(pil_img.height * ratio))
#     pil_img = pil_img.resize(new_size, Image.ANTIALIAS)

# # Create an object of tkinter ImageTk
# img = ImageTk.PhotoImage(pil_img)

# # Create a Label Widget to display the image
# label = tk.Label(frame, image=img)
# label.pack()

# win.mainloop()


# #######


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


# # Bind a function to the label's resize event to rescale the image when the window size changes
# def on_label_resize(event):
#     global current_img_tk
#     current_img_tk = rescale_image(current_img, event.width, event.height)
#     img_label.config(image=current_img_tk)
# img_label.bind('<Configure>', on_label_resize)

# Start the Tkinter event loop
root.mainloop()



############

# ########################

# import tkinter as tk
# from PIL import Image, ImageTk

# # Create a Tkinter window
# root = tk.Tk()

# # Define the geometry of the window
# root.geometry("700x500")

# # Read the data from the dataframe
# img_paths = df_suggested['SourceFile'].tolist()

# # Create a label to display the image
# img_label = tk.Label(root)
# img_label.pack()

# # Define a function to rescale the image
# def rescale_image(img, width, height):
#     # Calculate the new size of the image while preserving the aspect ratio
#     aspect_ratio = img.width / img.height
#     if width / aspect_ratio < height:
#         new_width = int(width)
#         new_height = int(width / aspect_ratio)
#     else:
#         new_width = int(height * aspect_ratio)
#         new_height = int(height)
#     # Resize the image and return it as a PhotoImage object
#     img = img.resize((new_width, new_height))
#     return ImageTk.PhotoImage(img)

# # Display the first image in the list
# current_img_path = img_paths[0]
# current_img = Image.open(current_img_path)
# current_img_tk = rescale_image(current_img, img_label.winfo_width(), img_label.winfo_height())
# img_label.config(image=current_img_tk)

# # Define functions to handle button clicks
# def prev_image():
#     global current_img_path, current_img_tk
#     # Get the index of the previous image
#     index = img_paths.index(current_img_path) - 1
#     # If we're at the beginning of the list, wrap around to the end
#     if index < 0:
#         index = len(img_paths) - 1
#     # Load and display the previous image
#     current_img_path = img_paths[index]
#     current_img = Image.open(current_img_path)
#     current_img_tk = rescale_image(current_img, img_label.winfo_width(), img_label.winfo_height())
#     img_label.config(image=current_img_tk)

# def next_image():
#     global current_img_path, current_img_tk
#     # Get the index of the next image
#     index = img_paths.index(current_img_path) + 1
#     # If we're at the end of the list, wrap around to the beginning
#     if index >= len(img_paths):
#         index = 0
#     # Load and display the next image
#     current_img_path = img_paths[index]
#     current_img = Image.open(current_img_path)
#     current_img_tk = rescale_image(current_img, img_label.winfo_width(), img_label.winfo_height())
#     img_label.config(image=current_img_tk)

# # Create buttons to go to the previous and next images
# prev_button = tk.Button(root, text='Previous', command=prev_image)
# prev_button.pack(side='left')
# next_button = tk.Button(root, text='Next', command=next_image)
# next_button.pack(side='right')

# # Bind a function to the label's resize event to rescale the image when the window size changes
# def on_label_resize(event):
#     global current_img_tk
#     current_img_tk = rescale_image(current_img, event.width, event.height)
#     img_label.config(image=current_img_tk)
# img_label.bind('<Configure>', on_label_resize)

# # Start the Tkinter event loop
# root.mainloop()



# ############
# import tkinter as tk
# from PIL import Image, ImageTk


# # Create a Tkinter window
# root = tk.Tk()

# # Read the data from the dataframe
# img_paths = df_suggested['SourceFile'].tolist()

# # Create a label to display the image
# img_label = tk.Label(root)
# img_label.pack()

# # Display the first image in the list
# current_img = ImageTk.PhotoImage(Image.open(img_paths[0]))
# img_label.config(image=current_img)

# # Define functions to handle button clicks


# def prev_image():
#     global current_img
#     # Get the index of the previous image
#     index = img_paths.index(current_img_path) - 1
#     # If we're at the beginning of the list, wrap around to the end
#     if index < 0:
#         index = len(img_paths) - 1
#     # Load and display the previous image
#     current_img_path = img_paths[index]
#     current_img = ImageTk.PhotoImage(Image.open(current_img_path))
#     img_label.config(image=current_img)


# def next_image():
#     global current_img
#     # Get the index of the next image
#     index = img_paths.index(current_img_path) + 1
#     # If we're at the end of the list, wrap around to the beginning
#     if index >= len(img_paths):
#         index = 0
#     # Load and display the next image
#     current_img_path = img_paths[index]
#     current_img = ImageTk.PhotoImage(Image.open(current_img_path))
#     img_label.config(image=current_img)


# # Create buttons to go to the previous and next images
# prev_button = tk.Button(root, text='Previous', command=prev_image)
# prev_button.pack(side='left')
# next_button = tk.Button(root, text='Next', command=next_image)
# next_button.pack(side='right')

# # Start the Tkinter event loop
# root.mainloop()


# #############

# class ImageBrowser:
#     def __init__(self, df):
#         self.df = df
#         self.current_row = 0
#         self.root = tk.Tk()
#         self.root.title("Image Browser")

#         # Load the images for the current row
#         self.load_images()

#         # Create the image areas
#         self.image1 = tk.Label(self.root, image=self.img1)
#         self.image2 = tk.Label(self.root, image=self.img2)
#         self.image1.pack(side=tk.LEFT)
#         self.image2.pack(side=tk.RIGHT)

#         # Create the navigation buttons
#         self.prev_button = tk.Button(
#             self.root, text="<<", command=self.prev_row)
#         self.next_button = tk.Button(
#             self.root, text=">>", command=self.next_row)
#         self.prev_button.pack(side=tk.LEFT)
#         self.next_button.pack(side=tk.RIGHT)

#         # Start the GUI
#         self.root.mainloop()

#     def load_images(self):
#         # Load the images for the current row
#         src_file = self.df.iloc[self.current_row]['SourceFile']
#         suggested_file = self.df.iloc[self.current_row]['suggested.SourceFile']
#         self.img1 = ImageTk.PhotoImage(Image.open(src_file))
#         self.img2 = ImageTk.PhotoImage(Image.open(suggested_file))

#     def update_images(self):
#         # Update the images for the current row
#         self.image1.configure(image=self.img1)
#         self.image2.configure(image=self.img2)

#     def prev_row(self):
#         # Move to the previous row
#         if self.current_row > 0:
#             self.current_row -= 1
#             self.load_images()
#             self.update_images()

#     def next_row(self):
#         # Move to the next row
#         if self.current_row < len(self.df) - 1:
#             self.current_row += 1
#             self.load_images()
#             self.update_images()


# # Create the image browser UI
# browser = ImageBrowser(df_suggested)


# import tkinter as tk
# from PIL import Image, ImageTk


# # Create a Tkinter window
# root = tk.Tk()

# # Create a label to display the image
# img_label = tk.Label(root)
# img_label.pack()

# # Load the image
# image = Image.open(img_file)
# tk_image = ImageTk.PhotoImage(image)
# img_label.config(image=tk_image)

# # Define a function to be called when the label has been fully rendered
# def on_img_label_rendered():
#     width = img_label.winfo_width()
#     print(width)

# # Use the 'after' method to schedule the function to be called after a delay
# img_label.after(100, on_img_label_rendered)

# # Start the Tkinter event loop
# root.mainloop()


