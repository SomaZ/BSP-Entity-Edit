# import statements
from tkinter import *
from tkinter.messagebox import *

class Help():
    def about(root):
        showinfo(title="About", message="This is an id tech 3 BSP entity editor written by SomaZ using Python, based on the text editor by Insidious")
		
def main(root, text, menubar):

    help = Help()

    helpMenu = Menu(menubar)
    helpMenu.add_command(label="About", command=help.about)
    menubar.add_cascade(label="Help", menu=helpMenu)

    root.config(menu=menubar)
	
if __name__ == "__main__":
    print("Please run 'main.py'")