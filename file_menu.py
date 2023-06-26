# import statements
from tkinter import *
from tkinter.filedialog import *
from tkinter.messagebox import *

from pyidtech3lib import BSP_READER as BSP
from pyidtech3lib import Q3VFS, Import_Settings, Surface_Type, Preset
from copy import deepcopy

bsp_file_types = [("BSP files","*.bsp"), ("Entity files","*.ent")]

def parse_line(line):
	try:
		key, value = line.split(' ', 1)
		key = key.strip("\t ")
		value = value.strip("\t ")
	except Exception:
		key = line
		value = ""
	value = value.replace("\"", "").strip()
	return key, value

# creating File
class File():

	def __init__(self, text, root, opengl_frame):#, shader_frame):
		self.filename = None
		self.bsp = None
		self.text = text
		self.root = root
		self.gl = opengl_frame
		#self.shaders = shader_frame

	def saveFile(self):
		if self.filename is None:
			showerror(title="Error", message="Open a .bsp file first")
			return
		try:
			t = self.text.get(0.0, END).rstrip()

			if t.endswith("\0"):
				t = t[:-1]

			if not t.endswith("\n"):
				t = t + "\n"

			if self.filename.endswith(".ent"):
				f = open(self.filename, "w")
				f.write(t)
				f.close()
				self.root.title("BSP Entity Edit - " + self.bsp.map_name)
				return

			t = t + "\0"

			if self.bsp is None:
				raise Exception("No bsp file opened, tried writing: " + self.filename)
			self.bsp.set_entity_lump(t)

			bsp_bytes = self.bsp.to_bytes()

			f = open(self.filename, "wb")
			f.write(bsp_bytes)
			f.close()
		except Exception as e:
			print(e)
			self.saveAs()
		self.root.title("BSP Entity Edit - " + self.bsp.map_name)

	def saveAs(self):
		if self.filename is None:
			showerror(title="Error", message="Open a .bsp file first")
			return

		if self.bsp is None:
			raise Exception("No bsp file opened, tried writing: " + self.filename)

		f = asksaveasfile(mode='wb', filetypes = bsp_file_types)
		if f is None:
			return

		t = self.text.get(0.0, END).rstrip()

		if f.name.endswith(".bsp"):
			if t.endswith("\0"):
				t = t[:-1]

			if not t.endswith("\n"):
				t = t + "\n"
			t = t + "\0"

			self.bsp.set_entity_lump(t)
			bsp_bytes = self.bsp.to_bytes()

			try:
				f.write(bsp_bytes)
				f.close()
			except Exception as e:
				print(e)
				showerror(title="Oops!", message="Unable to save file...")
		else:
			try:
				f.write(t.encode("latin-1"))
				f.close()
			except Exception as e:
				print(e)
				showerror(title="Oops!", message="Unable to save file...")
		self.root.title("BSP Entity Edit - " + self.bsp.map_name)

	def openFile(self):
		f = askopenfile(mode='r', filetypes = bsp_file_types)
		if f is None:
			return
		self.filename = f.name

		if f.name.endswith(".bsp"):
			vfs = Q3VFS()
			vfs.build_index()

			import_settings = Import_Settings(
				file=self.filename,
				surface_types=Surface_Type.ALL,
				subdivisions=0,
				preset=Preset.EDITING.value
			)

			bsp = BSP(vfs, import_settings)

			self.gl.clear_meshes()
			self.gl.add_bsp_models(deepcopy(bsp).get_bsp_models())

			lump = bsp.lumps["entities"]
			stringdata = []
			for i in lump:
				stringdata.append(i.char.decode("latin-1"))
			entities_string = "".join(stringdata)

			self.root.title("BSP Entity Edit - " + bsp.map_name)
			self.bsp = bsp
		elif self.bsp is None:
			showerror(title="Error", message="Open a bsp file first")
			return
		else:
			entities_string = f.read().rstrip()
			self.bsp.set_entity_lump(entities_string)

		self.text.delete(0.0, END)
		self.text.insert(0.0, entities_string)
		self.text.edit_reset()

		f.close()

		self.update_gl_entity_objects()
		#self.reload_shaders()

	def update_bsp_entity_lump(self):
		t = self.text.get(0.0, END).rstrip()
		self.bsp.set_entity_lump(t)

	def update_gl_entity_objects(self):
		self.gl.clear_objects()
		bsp_objects = self.bsp.get_bsp_entity_objects()
		for object_name in bsp_objects:
			self.gl.add_gl_object(
				object_name,
				bsp_objects[object_name]
			)
		self.gl.update_object_indexes()

	def reload_entities(self, *args):
		if self.bsp is None:
			return
		self.update_bsp_entity_lump()
		self.update_gl_entity_objects()

	def reload_shaders(self):
		if self.bsp is None:
			return

		#self.shaders.delete(0, END)
		
		#for shader in self.bsp.lumps["shaders"]:
		#	self.shaders.insert(END, shader.name)

	def pick_object_per_current_line(self, *args):
		current_line = int(self.text.index(INSERT).split('.')[0]) - 1
		self.gl.pick_object_per_line(current_line)
		
	def update_position_current_object(self, *args):
		self.pick_object_per_current_line()
		current_line_text = self.text.get('insert linestart', 'insert lineend')
		key, value = parse_line(current_line_text)
		values = value.split(" ")
		if len(values) != 3:
			return
		try:
			values[0] = float(values[0])
			values[1] = float(values[1])
			values[2] = float(values[2])
		except Exception:
			return
		self.gl.set_selected_object_position(values)
		
	def update_rotation_current_object(self, *args):
		self.pick_object_per_current_line()
		current_line_text = self.text.get('insert linestart', 'insert lineend')
		key, value = parse_line(current_line_text)
		values = value.split(" ")
		try:
			values[0] = float(values[2])
			values[1] = float(values[0])
			values[2] = float(values[1])
		except Exception:
			try:
				values = [0.0, 0.0, float(values[0])]
			except Exception:
				return
		self.gl.set_selected_object_rotation(values)
		
	def update_scale_current_object(self, *args):
		self.pick_object_per_current_line()
		current_line_text = self.text.get('insert linestart', 'insert lineend')
		key, value = parse_line(current_line_text)
		values = value.split(" ")
		try:
			values[0] = float(values[0])
			values[1] = float(values[1])
			values[2] = float(values[2])
		except Exception:
			try:
				values = [float(values[0]), float(values[0]), float(values[0])]
			except Exception:
				return
		self.gl.set_selected_object_scale(values)

	def quit(self):
		entry = askyesno(title="Quit", message="Are you sure you want to quit?")
		if entry == True:
			self.root.destroy()


def main(root, text, menubar, opengl_frame, refresh_btn):#, shader_frame):
	filemenu = Menu(menubar)
	objFile = File(text, root, opengl_frame)#, shader_frame)
	filemenu.add_command(label="Open", command=objFile.openFile)
	filemenu.add_command(label="Save", command=objFile.saveFile)
	filemenu.add_command(label="Save As...", command=objFile.saveAs)
	filemenu.add_separator()
	filemenu.add_command(label="Quit", command=objFile.quit)
	menubar.add_cascade(label="File", menu=filemenu)
	root.config(menu=menubar)
	
	refresh_btn.bind("<Button-1>", objFile.reload_entities)
	text.bind("<<Current_Line_Changed>>", objFile.pick_object_per_current_line)
	text.bind("<<Rebuild>>", objFile.reload_entities)
	text.bind("<<Origin_Modified>>", objFile.update_position_current_object)
	text.bind("<<Rotation_Modified>>", objFile.update_rotation_current_object)
	text.bind("<<Scale_Modified>>", objFile.update_scale_current_object)

if __name__ == "__main__":
	print("Please run 'main.py'")