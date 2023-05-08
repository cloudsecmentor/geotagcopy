import tkinter
from tkintermapview import TkinterMapView

root_tk = tkinter.Tk()
root_tk.geometry(f"{1200}x{600}")
root_tk.title("map_view_simple_example.py")

# create map widget
map_widget = TkinterMapView(root_tk, width=600, height=400, corner_radius=0)
map_widget.place(x=100, y=200, width=200, height=200)
# pack(fill="both", expand=True)

# google normal tile server
map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)

map_widget.set_position(52.5200, 13.4050, marker=True)

root_tk.mainloop()