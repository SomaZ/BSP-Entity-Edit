# import statements
from tkinter import *
from tkinter.filedialog import *
from tkinter.messagebox import *

from pyidtech3lib import BSP_READER as BSP
from pyidtech3lib import Q3VFS, Import_Settings, Surface_Type, Preset

bsp_file_types = [("BSP files","*.bsp"), ("Entity files","*.ent")]

# creating File
class File():

	def __init__(self, text, root, opengl_frame, shader_frame):
		self.filename = None
		self.bsp = None
		self.text = text
		self.root = root
		self.gl = opengl_frame
		self.shaders = shader_frame

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
			
			surface_types = (Surface_Type.BRUSH |
                             Surface_Type.PLANAR |
                             Surface_Type.PATCH |
                             Surface_Type.TRISOUP |
                             Surface_Type.FAKK_TERRAIN)

			import_settings = Import_Settings(
				file=self.filename,
				surface_types=surface_types,
				subdivisions=0,
				preset=Preset.EDITING.value
			)

			bsp = BSP(vfs, import_settings)
			
			bsp.lightmap_size = bsp.compute_packed_lightmap_size()
			
			self.gl.clear_meshes()
			for index, mesh in enumerate(bsp.get_bsp_models()):
				blend = None
				if mesh.vertex_colors.get("Color") is None:
					vcolors = [(0.0, 255.0, 0.0, 63.0) for i in range(len(mesh.positions.get_indexed()))]
					blend = "ADD"
				else:
					vcolors = mesh.vertex_colors["Color"].get_indexed()
				self.gl.add_bsp_mesh(
					mesh.name,
					mesh.positions.get_indexed(),
					mesh.indices,
					vcolors,
					mesh.vertex_normals.get_indexed(),
					blend)
			
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
		self.reload_shaders()
		
	def update_bsp_entity_lump(self):
		t = self.text.get(0.0, END).rstrip()
		self.bsp.set_entity_lump(t)
		
	def update_gl_entity_objects(self):
		self.gl.clear_objects()
		bsp_objects = self.bsp.get_bsp_entity_objects()
		for object_name in bsp_objects:
			self.gl.add_bsp_object(
				object_name,
				bsp_objects[object_name]
			)
			
	def reload_entities(self, *args):
		if self.bsp is None:
			return
		self.update_bsp_entity_lump()
		self.update_gl_entity_objects()
		
	def reload_shaders(self):
		if self.bsp is None:
			return
			
		self.shaders.delete(0, END)
		
		for shader in self.bsp.lumps["shaders"]:
			self.shaders.insert(END, shader.name)

	def quit(self):
		entry = askyesno(title="Quit", message="Are you sure you want to quit?")
		if entry == True:
			self.root.destroy()


def main(root, text, menubar, opengl_frame, refresh_btn, shader_frame):
	filemenu = Menu(menubar)
	objFile = File(text, root, opengl_frame, shader_frame)
	filemenu.add_command(label="Open", command=objFile.openFile)
	filemenu.add_command(label="Save", command=objFile.saveFile)
	filemenu.add_command(label="Save As...", command=objFile.saveAs)
	filemenu.add_separator()
	filemenu.add_command(label="Quit", command=objFile.quit)
	menubar.add_cascade(label="File", menu=filemenu)
	root.config(menu=menubar)
	
	refresh_btn.bind("<Button-1>", objFile.reload_entities)

if __name__ == "__main__":
	print("Please run 'main.py'")