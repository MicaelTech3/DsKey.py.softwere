import tkinter as tk
from tkinter import ttk

def status_dot(canvas, x, y, color):
    canvas.create_oval(x, y, x+12, y+12, fill=color, outline="")
