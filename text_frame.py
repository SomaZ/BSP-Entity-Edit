from tkinter import *
from tkinter.scrolledtext import *

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
			elif (current_line_text.startswith("\"light\"")
				  or current_line_text.startswith("\"_color\"")):
				if self.needs_rebuild:
					self.event_generate("<<Rebuild>>", when="tail")
					self.needs_rebuild = False
					return result
				self.event_generate("<<Light_Modified>>", when="tail")

		if (args[0] == "mark"):
			if int(self.index(INSERT).split('.')[0]) != self.current_line:
				self.event_generate("<<Current_Line_Changed>>", when="tail")
				self.current_line = int(self.index(INSERT).split('.')[0])

		# return what the actual widget returned
		return result
	
class Text_frame():
	def __init__(self, root):
		text_frame = Frame(root, padx=0, pady=0)
		text = CustomText(text_frame, state='normal', wrap='word', pady=2, padx=3, undo=True)
		linenumbers = TextLineNumbers(text_frame, width=30)
		linenumbers.attach(text)
		linenumbers.pack(side="left", fill=Y, expand=NO)
		text.pack(fill=BOTH, expand=YES)
		text.bind("<<Change>>", linenumbers.on_txt_change)
		text.bind("<Configure>", linenumbers.on_txt_change)
		text.focus_set()
		
		self.frame = text_frame
		self.focus = text
		self.text = text

if __name__ == "__main__":
	print("Please run 'main.py'")