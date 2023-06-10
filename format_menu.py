# import statements
from tkinter import *
from tkinter.colorchooser import askcolor
from tkinter.font import Font, families
from tkinter.scrolledtext import *

class Format():

	def __init__(self, text, root):
		self.text = text
		self.root = root

	def changeBg(self):
		(triple, hexstr) = askcolor()
		if hexstr:
			self.text.config(bg=hexstr)

	def changeFg(self):
		(triple, hexstr) = askcolor()
		if hexstr:
			self.text.config(fg=hexstr)

	def textchange(self, event):
		if self.root.title().endswith("*"):
			return
		self.root.title(self.root.title() + "*")

def main(root, text, menubar):
	objFormat = Format(text, root)

	fontoptions = families(root)
	font = Font(family="Arial", size=12)
	text.configure(font=font)

	formatMenu = Menu(menubar)

	fsubmenu = Menu(formatMenu, tearoff=0)
	ssubmenu = Menu(formatMenu, tearoff=0)

	for option in fontoptions:
		fsubmenu.add_command(label=option, command=lambda option=option: font.configure(family=option))
	for value in range(1, 31):
		ssubmenu.add_command(label=str(value), command=lambda value=value: font.configure(size=value))

	formatMenu.add_command(label="Change Background", command=objFormat.changeBg)
	formatMenu.add_command(label="Change Font Color", command=objFormat.changeFg)
	formatMenu.add_cascade(label="Font", underline=0, menu=fsubmenu)
	formatMenu.add_cascade(label="Size", underline=0, menu=ssubmenu)
	menubar.add_cascade(label="Format", menu=formatMenu)

	text.bind('<KeyPress>', objFormat.textchange)

	root.grid_columnconfigure(0, weight=1)
	root.resizable(True, True)

	root.config(menu=menubar)

if __name__ == "__main__":
	print("Please run 'main.py'")