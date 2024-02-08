# import statements
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import file_menu, edit_menu, format_menu, render_menu, help_menu
import ogl_frame
from data_frame import Data_frame, Data_variable
from lighting_frame import Lighting_frame
from text_frame import Text_frame


SHADER_VARIABLES = (
	Data_variable("Shader Name", "name", str, 1),
	Data_variable("Surface Flags", "flags", int, 1),
	Data_variable("Content Flags", "contents", int, 1),
)

FOG_VARIABLES = (
	Data_variable("Shader Name", "name", str, 1),
	Data_variable("Brush", "brush", int, 1),
	Data_variable("Plane", "visibleSide", int, 1)
)

SURFACE_VARIABLES = (
	Data_variable("Shader", "texture", int, 1),
	Data_variable("Fog", "effect", int, 1),
	Data_variable("Type", "type", int, 1),
)

def main():
	# creating a tkinter window
	root = Tk()

	# gives the window a title and dimensions
	root.title("BSP Entity Edit")
	root.geometry("1200x600")
	root.minsize(width=800, height=400)

	main_frame = PanedWindow(root)
	main_frame.pack(fill=BOTH, expand=YES)
	
	# frame left
	tabControl = ttk.Notebook(main_frame)
	
	data_frame_text = Text_frame(main_frame)
	data_frame_shaders = Data_frame(main_frame, SHADER_VARIABLES)
	data_frame_fogs = Data_frame(main_frame, FOG_VARIABLES)
	data_frame_surfaces = Data_frame(main_frame, SURFACE_VARIABLES)
	data_frame_lighting = Lighting_frame(main_frame)
	
	tabControl.add(data_frame_text.frame, text="Entities")
	tabControl.add(data_frame_shaders.frame, text="Shaders")
	tabControl.add(data_frame_fogs.frame, text="Fogs")
	tabControl.add(data_frame_surfaces.frame, text="Surfaces")
	tabControl.add(data_frame_lighting.frame, text="Lighting")
	tabControl.hide(data_frame_lighting.frame)
	tabs_dict = {
		"Entities" : data_frame_text,
		"Shaders" : data_frame_shaders,
		"Fogs" : data_frame_fogs,
		"Surfaces" : data_frame_surfaces,
		"Lighting" : data_frame_lighting,
	}
	
	# frame right
	right_frame = Frame(main_frame, padx=5, pady=5)
	model_frame = ogl_frame.main(
		right_frame,
		data_frame_text.text,
		data_frame_shaders.listbox,
		data_frame_fogs.listbox,
		data_frame_surfaces.listbox,
		data_frame_lighting
		)
	btn = Button(right_frame, text="Update Entity Render", height = 1)
	
	# creating a menubar
	menubar = Menu(root)

	# adding our menus to the menubar
	bfi = file_menu.main(
		root,
		data_frame_text.text,
		menubar,
		model_frame,
		btn,
		data_frame_shaders.listbox,
		data_frame_fogs.listbox,
		data_frame_surfaces.listbox
		)
	edit_menu.main(root, data_frame_text.text, menubar)
	format_menu.main(root, data_frame_text.text, menubar)
	render_menu.main(root, menubar, model_frame)
	help_menu.main(root, data_frame_text.text, menubar, tabControl, data_frame_lighting.frame)
	
	btn.grid(column=0, row=1, sticky=(S, E, W), padx=1, pady=1)
	main_frame.add(tabControl)
	main_frame.add(right_frame)
	model_frame.grid(column=0, row=0, sticky=(N, S, E, W), padx=1, pady=1)
	
	right_frame.columnconfigure(0, weight=1)
	right_frame.rowconfigure(0, weight=100)
	right_frame.rowconfigure(1, weight=1)

	current_tab = data_frame_text
	def enter(event):
		data_frame_text.focus.focus_set()
		model_frame.camera.stop_movement()
	def leave(event):
		data_frame_text.text.add_rebuild_event()
		model_frame.focus_set()
	def tab_change(event):
		new_tab = event.widget.tab('current')['text']
		current_tab = tabs_dict[new_tab]
		model_frame.set_mode(new_tab)
	def set_shader_ui_data(event = None):
		if len(data_frame_shaders.listbox.curselection()) > 0:
			index = data_frame_shaders.listbox.curselection()[0]
			model_frame.set_selected_data(index)
			data_frame_shaders.update_data_ui(bfi.bsp.lumps["shaders"][index])
	def set_fog_ui_data(event = None):
		if len(data_frame_fogs.listbox.curselection()) > 0:
			index = data_frame_fogs.listbox.curselection()[0]
			model_frame.set_selected_data(index)
			data_frame_fogs.update_data_ui(bfi.bsp.lumps["fogs"][index])	
	def set_surface_ui_data(event = None):
		if len(data_frame_surfaces.listbox.curselection()) > 0:
			index = data_frame_surfaces.listbox.curselection()[0]
			model_frame.set_selected_data(index)
			data_frame_surfaces.update_data_ui(bfi.bsp.lumps["surfaces"][index])	
	def set_selected_shader_data(event = None):
		index = model_frame.selected_data
		data_frame_shaders.update_data_bsp(bfi.bsp.lumps["shaders"][index])
		bfi.reload_shaders()
		data_frame_shaders.listbox.select_set(index)
		data_frame_shaders.listbox.see(index)
	def set_selected_fog_data(event = None):
		index = model_frame.selected_data
		data_frame_fogs.update_data_bsp(bfi.bsp.lumps["fogs"][index])
		bfi.reload_fogs()
		data_frame_fogs.listbox.select_set(index)
		data_frame_fogs.listbox.see(index)
	def set_selected_surface_data(event = None):
		index = model_frame.selected_data
		data_frame_surfaces.update_data_bsp(bfi.bsp.lumps["surfaces"][index])
		shader = data_frame_surfaces.entries["texture"].get()
		fog = data_frame_surfaces.entries["effect"].get()
		model_frame.update_shader_and_fog_data(index, shader, fog)
		bfi.reload_surfaces()
		data_frame_surfaces.listbox.select_set(index)
		data_frame_surfaces.listbox.see(index)

	def copy_location(event):
		pos = model_frame.trace_mouse_location(event.x, event.y)
		root.clipboard_clear()
		root.clipboard_append('"{} {} {}"'.format(*pos))
	
	model_frame.bind('<Leave>', enter)
	model_frame.bind('<Enter>', leave)

	model_frame.bind('<Button-2>', copy_location)

	tabControl.bind('<<NotebookTabChanged>>', tab_change)
	data_frame_shaders.listbox.bind('<<ListboxSelect>>', set_shader_ui_data)
	data_frame_shaders.btn_discard.configure(command=set_shader_ui_data)
	data_frame_shaders.btn_apply.configure(command=set_selected_shader_data)

	data_frame_fogs.listbox.bind('<<ListboxSelect>>', set_fog_ui_data)
	data_frame_fogs.btn_discard.configure(command=set_fog_ui_data)
	data_frame_fogs.btn_apply.configure(command=set_selected_fog_data)

	data_frame_surfaces.listbox.bind('<<ListboxSelect>>', set_surface_ui_data)
	data_frame_surfaces.btn_discard.configure(command=set_surface_ui_data)
	data_frame_surfaces.btn_apply.configure(command=set_selected_surface_data)

	def update_lightmap_bake():
		bfi.reload_entities()
		model_frame.update_lightmap_bake()

	def update_lightmap_bounce():
		bfi.reload_entities()
		model_frame.update_lightmap_bounce()

	def pack_lightmap_bake():
		messagebox.showinfo(title="Sorry", message="This feature is not implemented yet. Stay tuned.")

	data_frame_lighting.btn_bake.configure(command=update_lightmap_bake)
	data_frame_lighting.btn_pack.configure(command=pack_lightmap_bake)
	data_frame_lighting.btn_bounce.configure(command=update_lightmap_bounce)
	
	# running the whole program
	root.mainloop()

if __name__ == "__main__":
	main()