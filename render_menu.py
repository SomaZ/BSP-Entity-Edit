# import statements
from tkinter import *
from tkinter.filedialog import *
from tkinter.messagebox import *

class render_settings():
	def __init__(self, opengl_frame):
		self.opengl_frame = opengl_frame

	def set_msaa_0(self):
		self.opengl_frame.set_msaa(0)

	def set_msaa_2(self):
		self.opengl_frame.set_msaa(2)

	def set_msaa_4(self):
		self.opengl_frame.set_msaa(4)

	def set_msaa_8(self):
		self.opengl_frame.set_msaa(8)

def main(root, menubar, opengl_frame):
	filemenu = Menu(menubar)
	settings = render_settings(opengl_frame)
	filemenu.add_command(label="No MSAA", command=settings.set_msaa_0)
	filemenu.add_command(label="2xMSAA", command=settings.set_msaa_2)
	filemenu.add_command(label="4xMSAA", command=settings.set_msaa_4)
	filemenu.add_command(label="8xMSAA", command=settings.set_msaa_8)
	menubar.add_cascade(label="Render", menu=filemenu)
	root.config(menu=menubar)

if __name__ == "__main__":
	print("Please run 'main.py'")