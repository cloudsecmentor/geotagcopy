import tkinter as tk
import cv2
from PIL import Image, ImageTk

class App:
    def __init__(self, video_source=0):
        self.cap = cv2.VideoCapture(video_source)
        self.root = tk.Tk()
        self.label = tk.Label(self.root)
        self.label.place(x=10,y=10, height=100, width=150)
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.width, self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.show_frame()

    def show_frame(self):
        _, frame = self.cap.read()
        if _:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img_tk = ImageTk.PhotoImage(image=img)
            self.label.img_tk = img_tk
            self.label.config(image=img_tk)
        self.root.after(1, self.show_frame)

    def on_exit(self):
        self.cap.release()
        self.root.destroy()

app = App(video_source='/Volumes/baz2tb/Baz/Pictures/Other/__iPhone Sergey/img0/03.06.2013.mov')
app.root.mainloop()