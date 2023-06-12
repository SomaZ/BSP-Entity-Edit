# import statements
from tkinter import *
from tkinter import ttk
from tkinter.filedialog import *
from tkinter.messagebox import *
from tkinter.font import Font
from tkinter.scrolledtext import *
import file_menu
import edit_menu
import format_menu
import help_menu
import ogl_frame

# Text line numbers is based on
# https://stackoverflow.com/questions/16369470/tkinter-adding-line-number-to-text-widget
# @Bryan Oakley
class TextLineNumbers(Canvas):
	def __init__(self, *args, **kwargs):
		Canvas.__init__(self, *args, **kwargs)
		self.textwidget = None
		self.bg = '#afeeee'

	def attach(self, text_widget):
		self.textwidget = text_widget
		
	def redraw(self, *args):
		'''redraw line numbers'''
		self.delete("all")

		i = self.textwidget.index("@0,0")
		while True :
			dline= self.textwidget.dlineinfo(i)
			if dline is None: break
			y = dline[1]
			linenum = str(i).split(".")[0]
			self.create_text(25,y,anchor="ne", text=linenum)
			i = self.textwidget.index("%s+1line" % i)
			
	def on_txt_change(self, event):
		self.redraw()
			
class CustomText(ScrolledText):
	def __init__(self, *args, **kwargs):
		ScrolledText.__init__(self, *args, **kwargs)

		# create a proxy for the underlying widget
		self._orig = self._w + "_orig"
		self.tk.call("rename", self._w, self._orig)
		self.tk.createcommand(self._w, self._proxy)

	def _proxy(self, *args):
		# let the actual widget perform the requested action
		cmd = (self._orig,) + args
		try:
			result = self.tk.call(cmd)
		except Exception as e:
			print(e)
			return None

		# generate an event if something was added or deleted,
		# or the cursor position changed
		if (args[0] in ("insert", "replace", "delete") or 
			args[0:3] == ("mark", "set", "insert") or
			args[0:2] == ("xview", "moveto") or
			args[0:2] == ("xview", "scroll") or
			args[0:2] == ("yview", "moveto") or
			args[0:2] == ("yview", "scroll")
		):
			self.event_generate("<<Change>>", when="tail")

		# return what the actual widget returned
		return result

def main():
	# creating a tkinter window
	root = Tk()

	# gives the window a title and dimensions
	root.title("BSP Entity Edit")
	root.geometry("1200x600")
	root.minsize(width=800, height=400)
	
	# frame left
	tabControl = ttk.Notebook(root)
	
	#left_frame = LabelFrame(root, text="Entitys", padx=5, pady=5)
	left_frame = Frame(root, padx=5, pady=5)
	text_frame = Frame(left_frame, width = 1000, padx=0, pady=0)
	text = CustomText(text_frame, state='normal', wrap='word', pady=2, padx=3, undo=True)
	linenumbers = TextLineNumbers(text_frame, width=30)
	linenumbers.attach(text)
	linenumbers.pack(side="left", fill=Y, expand=YES)
	text.pack(fill=BOTH, expand=YES)
	text.bind("<<Change>>", linenumbers.on_txt_change)
	text.bind("<Configure>", linenumbers.on_txt_change)
	text.focus_set()
	
	#shader_frame = LabelFrame(root, text="Shaders", padx=5, pady=5)
	shader_frame = Frame(root, padx=5, pady=5)
	shader_scroll = Scrollbar(shader_frame) 
	shader_scroll.pack(side = RIGHT, fill = Y)
	shader_listbox = Listbox(shader_frame, yscrollcommand = shader_scroll.set)
	shader_listbox.insert(1,"Bread")
	shader_listbox.pack(side="left", fill=BOTH, expand=YES)
	shader_scroll.config(command = shader_listbox.yview) 
	
	tabControl.add(left_frame, text="Entitys")
	tabControl.add(shader_frame, text="Shaders")
	
	# frame right
	right_frame = LabelFrame(root, text="Map Render", padx=5, pady=5)
	model_frame = ogl_frame.main(right_frame, text)
	btn = Button(right_frame, text="Update Entity Render", height = 1)
	
	# creating a menubar
	menubar = Menu(root)

	# adding our menus to the menubar
	file_menu.main(root, text, menubar, model_frame, btn, shader_listbox)
	edit_menu.main(root, text, menubar)
	format_menu.main(root, text, menubar)
	help_menu.main(root, text, menubar)
	
	text_frame.grid(column=0, row=0, sticky=(N, S, W), padx=1, pady=1)
	btn.grid(column=0, row=1, sticky=(S, E, W), padx=1, pady=1)
	tabControl.grid(column=0, row=0, sticky=(N, S, W), padx=1, pady=1)
	right_frame.grid(column=1, row=0, sticky=(N, S, E), padx=1, pady=1)
	model_frame.grid(column=0, row=0, sticky=(N, S, E, W), padx=1, pady=1)
	
	root.columnconfigure(0, weight=4)
	root.columnconfigure(1, weight=20)
	root.rowconfigure(0, weight=1)
	left_frame.columnconfigure(0, weight=1)
	left_frame.rowconfigure(0, weight=1)
	right_frame.columnconfigure(0, weight=1)
	right_frame.rowconfigure(0, weight=100)
	right_frame.rowconfigure(1, weight=1)

	def enter(event):
		text.focus_set()
	def leave(event):
		model_frame.focus_set()
		
	text.bind('<Enter>', enter)
	model_frame.bind('<Enter>', leave)
	
	# running the whole program
	root.mainloop()

if __name__ == "__main__":
	main()