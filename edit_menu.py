# import statements
from tkinter import *
from tkinter.simpledialog import *
from tkinter.filedialog import *
from tkinter.messagebox import *

# creating Edit
class Edit():

	def popup(self, event):
		self.rightClick.post(event.x_root, event.y_root)

	def copy(self, *args):
		sel = self.text.selection_get()
		self.clipboard = sel

	def cut(self, *args):
		sel = self.text.selection_get()
		self.clipboard = sel
		self.text.delete(SEL_FIRST, SEL_LAST)

	def paste(self, *args):
		self.text.insert(INSERT, self.clipboard)

	def select_all(self, *args):
		self.text.tag_add(SEL, "1.0", END)

	def undo(self, *args):
		self.text.edit_undo()
		self.text.mark_unset(INSERT)

	def redo(self, *args):
		self.text.edit_redo()
		self.text.mark_unset(INSERT)

	def find(self, *args):
		self.text.focus_set()
		self.current_select = 0
		target = askstring('Find', 'Search String:')
		if target:
			self.target = target
			idx = '1.0'
			while 1:
				idx = self.text.search(target, idx, nocase=1, stopindex=END)
				if not idx:
					break
				lastidx = '%s+%dc' % (idx, len(target))
				self.text.tag_add("found", idx, lastidx)
				self.text.tag_config('found', foreground='white', background='green')
				idx = lastidx

		self.text.tag_remove(SEL, '1.0', END)
		if target:
			idx = '1.0'
			while 1:
				idx = self.text.search(target, idx, nocase=1, stopindex=END)
				if not idx:
					break
				lastidx = '%s+%dc' % (idx, len(target))
				self.text.tag_add(SEL, idx, lastidx)
				self.text.see(idx)
				idx = lastidx
				self.current_select+=1
				break

	def find_next(self, *args):
		self.text.tag_remove(SEL, '1.0', END)
		if self.target:
			idx = '1.0'
			current_select = 0
			while 1:
				idx = self.text.search(self.target, idx, nocase=1, stopindex=END)
				if not idx:
					self.current_select = 0
					break
				lastidx = '%s+%dc' % (idx, len(self.target))
				if self.current_select == current_select:
					self.text.tag_add(SEL, idx, lastidx)
					self.text.see(idx)
					self.current_select+=1
					break
				idx = lastidx
				current_select += 1

	def unmark_all(self, *args):
		self.text.tag_remove("found", '1.0', END)

	def __init__(self, text, root):
		self.clipboard = None
		self.text = text
		self.rightClick = Menu(root)
		self.current_select = 0
		self.target = None

def main(root, text, menubar):

	objEdit = Edit(text, root)

	editmenu = Menu(menubar)
	editmenu.add_command(label="Copy", command=objEdit.copy, accelerator="Ctrl+C")
	editmenu.add_command(label="Cut", command=objEdit.cut, accelerator="Ctrl+X")
	editmenu.add_command(label="Paste", command=objEdit.paste, accelerator="Ctrl+V")
	editmenu.add_command(label="Undo", command=objEdit.undo, accelerator="Ctrl+Z")
	editmenu.add_command(label="Redo", command=objEdit.redo, accelerator="Ctrl+Y")
	editmenu.add_command(label="Find", command=objEdit.find, accelerator="Ctrl+F")
	editmenu.add_command(label="Find Next", command=objEdit.find_next, accelerator="F3")
	editmenu.add_separator()
	editmenu.add_command(label="Select All", command=objEdit.select_all, accelerator="Ctrl+A")
	editmenu.add_command(label="Remove Highlights", command=objEdit.unmark_all, accelerator="Esc")
	menubar.add_cascade(label="Edit", menu=editmenu)

	root.bind_all("<Control-z>", objEdit.undo)
	root.bind_all("<Control-y>", objEdit.redo)
	root.bind_all("<Control-f>", objEdit.find)
	root.bind_all("<F3>", objEdit.find_next)
	root.bind_all("Control-a", objEdit.select_all)
	text.bind('<Escape>', objEdit.unmark_all)

	objEdit.rightClick.add_command(label="Copy", command=objEdit.copy)
	objEdit.rightClick.add_command(label="Cut", command=objEdit.cut)
	objEdit.rightClick.add_command(label="Paste", command=objEdit.paste)
	objEdit.rightClick.add_separator()
	objEdit.rightClick.add_command(label="Select All", command=objEdit.select_all)
	objEdit.rightClick.add_command(label="Remove Highlights", command=objEdit.unmark_all)

	text.bind("<Button-3>", objEdit.popup)

	root.config(menu=menubar)

if __name__ == "__main__":
	print("Please run 'main.py'")