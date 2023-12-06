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
import render_menu
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

		self.num_lines = 1
		self.current_line = 1
		self.needs_rebuild = False
		
	def add_rebuild_event(self, *args):
		if self.needs_rebuild:
			self.event_generate("<<Rebuild>>", when="tail")
			self.needs_rebuild = False

	def _proxy(self, *args):

		num_lines = self.num_lines

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

		if (args[0] in ("insert", "replace", "delete")):
			current_line_text = self.get('insert linestart', 'insert lineend')
			if int(self.index('end-1c').split('.')[0]) != num_lines:
				self.needs_rebuild = True
				self.num_lines = int(self.index('end-1c').split('.')[0])
			elif current_line_text.startswith("\"origin\""):
				if self.needs_rebuild:
					self.event_generate("<<Rebuild>>", when="tail")
					self.needs_rebuild = False
					return result
				self.event_generate("<<Origin_Modified>>", when="tail")
			elif (current_line_text.startswith("\"angle\"") 
				  or current_line_text.startswith("\"angles\"")):
				if self.needs_rebuild:
					self.event_generate("<<Rebuild>>", when="tail")
					self.needs_rebuild = False
					return result
				self.event_generate("<<Rotation_Modified>>", when="tail")
			elif (current_line_text.startswith("\"modelscale\"")
				  or current_line_text.startswith("\"modelscale_vec\"")):
				if self.needs_rebuild:
					self.event_generate("<<Rebuild>>", when="tail")
					self.needs_rebuild = False
					return result
				self.event_generate("<<Scale_Modified>>", when="tail")

		if (args[0] == "mark"):
			if int(self.index(INSERT).split('.')[0]) != self.current_line:
				self.event_generate("<<Current_Line_Changed>>", when="tail")
				self.current_line = int(self.index(INSERT).split('.')[0])

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
	
	shader_frame = Frame(root, padx = 5, pady = 5)

	shader_list_frame = Frame(shader_frame)
	shader_list_frame.grid(row = 0, column = 0, sticky=(N, E, W, S), padx=1, pady=1)
	shader_scroll = Scrollbar(shader_list_frame)
	shader_scroll.pack(side = RIGHT, fill = Y)
	shader_listbox = Listbox(shader_list_frame, yscrollcommand = shader_scroll.set)
	shader_listbox.pack(side=LEFT, fill = BOTH, expand = YES)
	shader_scroll.config(command=shader_listbox.yview)

	shader_data_frame = Frame(shader_frame)
	shader_data_frame.grid(row = 1, column = 0, sticky=(S, E, W), padx=1, pady=1, columnspan=2)
	shader_label = Label(shader_data_frame, text="Shader Name")
	shader_label.grid(row = 0, column= 0)
	shader_name = Entry(shader_data_frame)
	shader_name.grid(row = 0, column= 1, sticky="we")
	shader_surf_label = Label(shader_data_frame, text="Surface Flags")
	shader_surf_label.grid(row = 1, column= 0)
	shader_surf_flag = Entry(shader_data_frame)
	shader_surf_flag.grid(row = 1, column= 1, sticky="we")
	shader_content_label = Label(shader_data_frame, text = "Content Flags")
	shader_content_label.grid(row = 2, column= 0)
	shader_content_flag = Entry(shader_data_frame)
	shader_content_flag.grid(row = 2, column= 1, sticky="we")
	btn_discard = Button(shader_data_frame, text="Discard", height = 1)
	btn_discard.grid(row = 3, column= 0)
	btn_apply = Button(shader_data_frame, text="Apply", height = 1)
	btn_apply.grid(row = 3, column= 1, sticky="we")

	shader_data_frame.columnconfigure(0, weight=1)
	shader_data_frame.columnconfigure(1, weight=100)

	shader_frame.columnconfigure(0, weight=1)
	shader_frame.rowconfigure(0, weight=100)
	shader_frame.rowconfigure(1, weight=1)
	
	tabControl.add(left_frame, text="Entities")
	tabControl.add(shader_frame, text="Shaders")
	
	# frame right
	right_frame = LabelFrame(root, text="Map Render", padx=5, pady=5)
	model_frame = ogl_frame.main(right_frame, text, shader_listbox)
	btn = Button(right_frame, text="Update Entity Render", height = 1)
	
	# creating a menubar
	menubar = Menu(root)

	# adding our menus to the menubar
	bfi = file_menu.main(root, text, menubar, model_frame, btn, shader_listbox)
	edit_menu.main(root, text, menubar)
	format_menu.main(root, text, menubar)
	render_menu.main(root, menubar, model_frame)
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
		model_frame.stop_movement()
	def leave(event):
		text.add_rebuild_event()
		model_frame.focus_set()
	def tab_change(event):
		new_tab = event.widget.tab('current')['text']
		model_frame.set_mode(new_tab)
	def set_shader_ui_data(event = None):
		if len(shader_listbox.curselection()) > 0:
			index = shader_listbox.curselection()[0]
			model_frame.set_selected_data(index)
			shader_name.delete(0,END)
			shader_name.insert(0,bfi.bsp.lumps["shaders"][index].name)
			shader_surf_flag.delete(0,END)
			shader_surf_flag.insert(0,bfi.bsp.lumps["shaders"][index].flags)
			shader_content_flag.delete(0,END)
			shader_content_flag.insert(0,bfi.bsp.lumps["shaders"][index].contents)		
	def set_selected_shader_data(event = None):
		bfi.set_shader_data(
			model_frame.selected_data,
			name = shader_name.get(),
			surface_flags=int(shader_surf_flag.get()),
			content_flags=int(shader_content_flag.get())
			)
		bfi.reload_shaders()
		shader_listbox.select_set(model_frame.selected_data)
		shader_listbox.see(model_frame.selected_data)
	
	text.bind('<Enter>', enter)
	model_frame.bind('<Enter>', leave)
	tabControl.bind('<<NotebookTabChanged>>', tab_change)
	shader_listbox.bind('<<ListboxSelect>>', set_shader_ui_data)
	btn_discard.configure(command=set_shader_ui_data)
	btn_apply.configure(command=set_selected_shader_data)
	
	# running the whole program
	root.mainloop()

if __name__ == "__main__":
	main()