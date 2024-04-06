from tkinter import *
from OpenGL import GL

import numpy
import ctypes
import types
import sys
from dataclasses import dataclass
from pyopengltk import OpenGLFrame
from ogl_camera import Camera
from ogl_objects import *
from ogl_fbo import FBO
from ogl_baking import Baking_data
from ogl_state import OpenGLState, OpenGLStateManager
import ogl_shader
if sys.version_info[0] > 2:
	import tkinter as tk
else:
	import Tkinter as tk


@dataclass
class Light():
	origin = [0.0, 0.0, 0.0]
	color = [1.0, 0.0, 0.0]
	radius = 300
	direction = [0.0, 0.0, -1.0]
	angle = 90


SHADERMODE = {
	"Vertices" : 0,
	"Surfaces" : 1,
	"Shaders" : 2,
	"Fogs" : 3,
	"Lighting" : 1
}


class AppOgl(OpenGLFrame):
	
	camera = Camera()
	last_clicked_pixel = [0, 0]
	multisample = 4
	hdr = False
	obb = 0
	gamma = 1.0
	compensate = 1.0
	render_fbo = None
	pick_fbo = None
	bake_data = None

	mode = "Entities"
	selected_data = -2
	
	opengl_meshes = {}
	opengl_objects = []
	opengl_lights = []
	
	def initgl(self):

		if not hasattr(self, "state"):
			self.state = OpenGLStateManager(0, 0, self.width, self.height)
		
		GL.glEnable(GL.GL_PROGRAM_POINT_SIZE)
		if not hasattr(self, "shaders"):
			self.shaders = {}
			for shader_name, vertex_shader, fragment_shader in ogl_shader.SHADER_LIST:
				self.shaders[shader_name] = ogl_shader.SHADER(vertex_shader, fragment_shader)
		
		if self.render_fbo is not None:
			if self.width != self.render_fbo.width or self.height != self.render_fbo.height:
				del self.render_fbo
				del self.pick_fbo
				self.render_fbo = FBO(self.width, self.height, self.multisample)
				self.pick_fbo = FBO(self.width, self.height, 0)
		else:
			self.render_fbo = FBO(self.width, self.height, self.multisample)
			self.pick_fbo = FBO(self.width, self.height, 0)
			self.bake_data = Baking_data(self.state)

		self.states = {
			"Default" : OpenGLState(
				framebuffer=self.render_fbo.bind),
			"Blend" : OpenGLState(
				framebuffer=self.render_fbo.bind,
				blend=True,
				blend_func=(GL.GL_SRC_ALPHA, GL.GL_ONE),
				face_culling=False,
				offset_filling=True,
				depth_write=False),
			"Default_pick" : OpenGLState(
				framebuffer=self.pick_fbo.bind),
			"Blend_pick" : OpenGLState(
				framebuffer=self.pick_fbo.bind,
				face_culling=False),
		}
			
		self.is_picking = False
		
		
	def redraw(self, force_swapping = False):
		if not hasattr(self, "shaders"):
			return
		new_settings = self.lighting_frame.get_render_settings()
		self.gamma = new_settings.gamma
		self.obb = new_settings.overbrightbits
		self.hdr = new_settings.hdr
		self.compensate = new_settings.compensate
		self.light_scale = new_settings.light_scale

		if self.mode == "Entities":
			shader = self.shaders.get("Vertex_Color")
		else:
			shader = self.shaders.get("Vertex_Color_Selection")
			if self.mode == "Lighting":
				shader = self.shaders.get("Lightmap_Color")

		if shader is None:
			return
		if self.is_picking:
			if self.mode == "Entities":
				shader = self.shaders["Pick_Object"]
			else:
				shader = self.shaders["Pick_Selection"]

		self.state.change_state(
			self.states["Default_pick"] if self.is_picking else self.states["Default"])
		self.state.set_viewport(0, 0, self.width, self.height)
		GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

		GL.glUseProgram(shader.program)
		self.camera.update_position()
		GL.glUniformMatrix4fv(
			shader.uniform_loc["u_view_mat"],
			1,
			GL.GL_FALSE,
			self.camera.get_view())
		GL.glUniformMatrix4fv(
			shader.uniform_loc["u_proj_mat"],
			1,
			GL.GL_FALSE,
			self.camera.get_projection(self.width / self.height))
		
		for obj in self.opengl_objects:
			if obj.hidden:
				continue

			if self.mode != "Entities":
				if not obj.mesh.name.startswith("*") or obj.mesh.blend:
					continue
				
			if obj.mesh.blend:
				if self.is_picking:
					self.state.change_state(self.states["Blend_pick"])
				else:
					self.state.change_state(self.states["Blend"])
			else:
				if self.is_picking:
					self.state.change_state(self.states["Default_pick"])
				else:
					self.state.change_state(self.states["Default"])
				
			GL.glUniformMatrix4fv(shader.uniform_loc["u_model_mat"], 1, GL.GL_FALSE, obj.modelMatrix)
			if (shader.uniform_loc["u_line"] != -1):
				GL.glUniform4f(shader.uniform_loc["u_line"], *obj.encoded_object_index)
			if (shader.uniform_loc["u_gamma"] != -1):
				GL.glUniform1f(shader.uniform_loc["u_gamma"], self.gamma)
			if (shader.uniform_loc["u_obb"] != -1):
				GL.glUniform1f(shader.uniform_loc["u_obb"], self.obb)
			if (shader.uniform_loc["u_compensate"] != -1):
				GL.glUniform1f(shader.uniform_loc["u_compensate"], self.compensate)
			if (shader.uniform_loc["u_lightScale"] != -1):
				GL.glUniform1f(shader.uniform_loc["u_lightScale"], self.light_scale)
			if (shader.uniform_loc["u_pick"] != -1):
				GL.glUniform1i(shader.uniform_loc["u_pick"], self.selected_data)
			if (shader.uniform_loc["u_mode"] != -1):
				GL.glUniform1i(shader.uniform_loc["u_mode"], SHADERMODE[self.mode])
			if (shader.uniform_loc["u_lightmap"] != -1):
				GL.glUniform1i(shader.uniform_loc["u_lightmap"], 0)
				GL.glActiveTexture(GL.GL_TEXTURE0)
				GL.glBindTexture(GL.GL_TEXTURE_2D, self.bake_data.framebuffer_texture)
			if (shader.uniform_loc["u_bouncemap"] != -1):
				GL.glUniform1i(shader.uniform_loc["u_bouncemap"], 1)
				GL.glActiveTexture(GL.GL_TEXTURE1)
				GL.glBindTexture(GL.GL_TEXTURE_2D, self.bake_data.bounce_texture)

			if obj.selected and not self.is_picking:
				if obj.mesh.blend:
					mix_factor = 1.0
				else:
					mix_factor = 0.7
				GL.glUniform4f(shader.uniform_loc["u_color"], 1., .01, 1., mix_factor)
				obj.draw()
				GL.glUniform4f(shader.uniform_loc["u_color"], 1., 1., 1., 0.)
			else:
				obj.draw()

		GL.glBindVertexArray(0)
		GL.glUseProgram(0)
		
		if not self.is_picking:
			GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, 0)
			GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, self.render_fbo.bind)
			GL.glDrawBuffer(GL.GL_BACK)
			GL.glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL.GL_COLOR_BUFFER_BIT, GL.GL_NEAREST)
		
			if self.mode == "Lighting":
				GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, self.bake_data.bake_fbo.bind)
				GL.glBlitFramebuffer(0, 0, 2048, 2048, 0, 0, self.width//4, self.width//4, GL.GL_COLOR_BUFFER_BIT, GL.GL_NEAREST)

			GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.state.state.framebuffer)
		self.is_picking = False

		if force_swapping:
			self.tkSwapBuffers()

	def update_lightmap_bake(self, test = None):
		self.bake_data.bake_lightmaps(
			self.opengl_objects,
			self.opengl_lights,
			self.lighting_frame.get_bake_settings(),
			self.redraw)
		
	def update_lightmap_bounce(self, test = None):
		self.bake_data.bake_lightbounce(
			self.redraw
		)
		
	def clear_lightmap_bake(self):
		self.bake_data.clear_lightmaps()

	def set_selected_data(self, data):
		self.selected_data = data

	def update_shader_and_fog_data(self, surface, shader = 0, fog = -1):
		for mesh in self.opengl_meshes:
			self.opengl_meshes[mesh].update_surface_data(surface, shader, fog)

	def set_mode(self, mode):
		self.mode = mode
		
	def set_msaa(self, multisample):
		if self.multisample == multisample:
			return
		self.multisample = multisample
		del self.render_fbo
		try:
			self.render_fbo = FBO(self.width, self.height, self.multisample)
		except Exception:
			self.render_fbo = FBO(self.width, self.height, 0)

	def trace_mouse_location(self, x, y):
		self.is_picking = True
		self.redraw()

		GL.glFlush()
		GL.glFinish()
		
		GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.pick_fbo.bind)
		GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, self.pick_fbo.bind)
		GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, self.pick_fbo.bind)
		
		depth = GL.glReadPixels(x, self.height - y, 1, 1, GL.GL_DEPTH_COMPONENT, GL.GL_FLOAT, None)
		
		GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, 0)
		GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, 0)
		GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

		half_clip = numpy.array([ x / self.width, (self.height - y) / self.height, depth[0][0], 1.0])
		clip_position = half_clip * 2.0 - numpy.array([1.0, 1.0, 1.0, 1.0])

		view_mat = self.camera.get_view()
		proj_mat = self.camera.get_projection(self.width / self.height)
		inverse_proj = numpy.linalg.inv(numpy.transpose(proj_mat))
		view_position = numpy.matmul(inverse_proj, clip_position)
		view_position = view_position / view_position[3]

		inverse_view = numpy.linalg.inv(numpy.transpose(view_mat))

		position = numpy.array(numpy.matmul(inverse_view, view_position))[0]
		
		if self.mode == "Entities":
			for object in self.opengl_objects:
				if object.selected and not object.mesh.name.startswith("*0"):
					position -= numpy.array([*object.mesh.center_radius[0], 0.0])
					break
			position = numpy.round(position, 1)
			self.set_selected_object_position(position[:3])
			self.update_selected_object_origin_text(position[:3])
		else:
			position = numpy.round(position, 1)

		return position

	def get_current_ent_line(self, x, y):
		self.is_picking = True
		
		self.redraw()
		
		GL.glFlush()
		GL.glFinish()
		
		GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.pick_fbo.bind)
		GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, self.pick_fbo.bind)
		GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, self.pick_fbo.bind)
		
		GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT0)
		data = GL.glReadPixels(x, self.height - y, 1, 1, GL.GL_RGB, GL.GL_UNSIGNED_BYTE, None)
		GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT0)
		
		GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, 0)
		GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, 0)
		GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
		picked_data = int.from_bytes(data, "little")
		if self.mode == "Entities":
			self.unselect_all()
			try:
				picked_line = self.opengl_objects[picked_data].new_line
			except:
				return
			self.opengl_objects[picked_data].selected = True
			# return to text instead of setting text here
			self.text.tag_remove("found", '1.0', END)
			idx = self.text.search("}", str(picked_line + 1)+".0", nocase=0, stopindex=END)
			try:
				line, char = idx.split(".")
			except:
				return
			self.text.tag_add('found', str(picked_line + 1)+".0", str(int(line)+1)+"."+char)
			self.text.tag_config('found', foreground='white', background='green')
			self.text.see(str(picked_line + 1)+".0")
			self.text.mark_set(INSERT, str(picked_line + 1)+".0")
			self.text.mark_unset(INSERT)
		else :
			MODE_PICK = {
				"Shaders" : self.shader_listbox,
				"Fogs" : self.fogs_listbox,
				"Surfaces" : self.surfaces_listbox,
				"Lighting" : self.surfaces_listbox,
			}
			self.set_selected_data(picked_data)
			# return to listbox instead of setting data here
			listbox = MODE_PICK[self.mode]
			listbox.selection_clear(0, END)
			listbox.select_set(picked_data)
			listbox.see(picked_data)
			listbox.event_generate("<<ListboxSelect>>", when="tail")

	def unselect_all(self, *args):
		for obj in self.opengl_objects:
			obj.selected = False
		self.set_selected_data(-2)
			
	def hide_selected(self, *args):
		for obj in self.opengl_objects:
			if obj.selected:
				obj.hidden = True
				
	def unhide_all(self, *args):
		for obj in self.opengl_objects:
			obj.hidden = False

	def add_gl_object(self, name, bsp_object):
		if bsp_object is None:
			return
		mesh = None
		cast_shadow = False
		if bsp_object.mesh_name == "worldspawn":
			mesh = self.opengl_meshes.get("*0")
			cast_shadow = True
		else:
			mesh = self.opengl_meshes.get(
				bsp_object.mesh_name)
			if "_cs" in bsp_object.custom_parameters:
				if bsp_object.custom_parameters["_cs"] == "1":
					cast_shadow = True
			if bsp_object.mesh_name == "*0":
				cast_shadow = True
			
		if mesh is None:
			new_mesh_name = ""
			colors = None
			if bsp_object.name.startswith("info_n") or bsp_object.name.startswith("light"):
				new_mesh_name = "box_green"
				colors = green_box_colors
			elif bsp_object.name.startswith("ammo") or bsp_object.name.startswith("holocron"):
				new_mesh_name = "box_cyan"
				colors = cyan_box_colors
			elif (
				 bsp_object.name.startswith("misc_") or
				 bsp_object.name.startswith("emplaced_") or
				 bsp_object.name.startswith("fx_")):
				new_mesh_name = "box_blue"
				colors = blue_box_colors
			else:
				new_mesh_name = "box_red"
				colors = red_box_colors
			
			mesh = self.opengl_meshes.get(new_mesh_name)
			if mesh is None:
				self.add_bsp_mesh(new_mesh_name, box_verts, box_indices, colors, box_normals)
				mesh = self.opengl_meshes.get(new_mesh_name)
			
		if bsp_object.mesh_name is not None and bsp_object.mesh_name.startswith("*"):
			rotation = numpy.array((0.0, 0.0, 0.0))
		else:
			rotation = bsp_object.rotation

		new_object = OpenGLObject(
			mesh,
			bsp_object.position,
			rotation,
			bsp_object.scale,
			cast_shadow
			)
		new_object.new_line = int(bsp_object.custom_parameters["first_line"])

		if bsp_object.custom_parameters["classname"] == "light":
			new_light = Light()
			new_light.origin = bsp_object.position
			try:
				new_light.radius = float(bsp_object.custom_parameters["light"]) * (7500.0 / 255.0)
			except:
				new_light.radius = 300.0 * (7500.0 / 255.0)
			try:
				new_light.color = list(map(float, bsp_object.custom_parameters["_color"]))
			except:
				new_light.color = [1.0, 1.0, 1.0]
			if "scale" in bsp_object.custom_parameters:
				new_light.radius *= float(bsp_object.custom_parameters["scale"])

			self.opengl_lights.append(new_light)
		
		if mesh.blend is None:
			self.opengl_objects.insert(0, new_object)
		else:
			self.opengl_objects.append(new_object)
			
	def update_object_indexes(self):
		for index, object in enumerate(self.opengl_objects):
			r = (index & 0x000000FF) >>  0
			g = (index & 0x0000FF00) >>  8
			b = (index & 0x00FF0000) >> 16
			object.encoded_object_index = float(r)/255.0, float(g)/255.0, float(b)/255.0, 0.0
		
	def add_bsp_mesh(
			self,
			name,
			vertices,
			indices=None,
			colors=None,
			normals=None,
			blend=None,
			vertex_info=None,
			tc0=None,
			tc1=None,
			center_radius=([0.0, 0.0, 0.0], 120.0)):

		new_indices = []
		mode = GL.GL_TRIANGLES
		for surface in indices:
			if len(surface) > 3:
				last_index = surface[1]
				for index in surface[2:]:
					new_indices.append(surface[0])
					new_indices.append(last_index)
					new_indices.append(index)
					last_index = index
				continue
			for index in surface:
				new_indices.append(index)

		new_positions = []
		for vert in vertices:
			new_positions.append(vert[0])
			new_positions.append(vert[1])
			new_positions.append(vert[2])
		new_colors = []
		for color in colors:
			if (color[0] + color[1] + color[2]) < 30:
				new_colors.append(color[0] + 30)
				new_colors.append(color[1] + 30)
				new_colors.append(color[2] + 30)
				new_colors.append(color[3])
				continue
			new_colors.append(color[0])
			new_colors.append(color[1])
			new_colors.append(color[2])
			new_colors.append(color[3])
		new_normals = []
		for normal in normals:
			new_normals.append(normal[0])
			new_normals.append(normal[1])
			new_normals.append(normal[2])
		if vertex_info is not None:
			new_vertex_info = []
			for info in vertex_info:
				new_vertex_info.append(info[0])
				new_vertex_info.append(info[1])
				new_vertex_info.append(info[2])
				new_vertex_info.append(info[3])
		else:
			new_vertex_info = [-2 for _ in range(len(normals)*4)]

		if tc0 is not None and tc1 is not None:
			new_tcs = []
			for st, lm in zip(tc0, tc1):
				new_tcs.append(st[0])
				new_tcs.append(st[1])
				new_tcs.append(lm[0])
				new_tcs.append(lm[1])
		else:
			new_tcs = [0.0 for _ in range(len(normals)*4)]

		self.opengl_meshes[name] = (
			OpenGLMesh(
				name,
				numpy.array(new_positions).astype(numpy.float32),
				numpy.array(new_indices).astype(numpy.uint32),
				numpy.array(new_colors).astype(numpy.uint8),
				numpy.array(new_normals).astype(numpy.float32),
				numpy.array(new_tcs).astype(numpy.float32),
				numpy.array(new_vertex_info).astype(numpy.float32),
				blend
				)
			)
		self.opengl_meshes[name].render_type = mode
		self.opengl_meshes[name].center_radius = center_radius
		
	def add_bsp_models(self, bsp_models):
		for index, mesh in enumerate(bsp_models):
			blend = None
			if mesh.vertex_colors.get("Color") is None:
				vcolors = [(0.0, 255.0, 0.0, 63.0) for i in range(len(mesh.positions.get_indexed()))]
				blend = "ADD"
			else:
				vcolors = mesh.vertex_colors["Color"].get_indexed()

			vertex_info = None
			if "BSP_VERT_INDEX" in mesh.vertex_data_layers:
				vertex_info = zip(
					mesh.vertex_data_layers["BSP_VERT_INDEX"].get_indexed(),
					mesh.vertex_data_layers["BSP_SURFACE_INDEX"].get_indexed(),
					mesh.vertex_data_layers["BSP_SHADER_INDEX"].get_indexed(),
					mesh.vertex_data_layers["BSP_FOG_INDEX"].get_indexed(),
					)
			else:
				vertex_info = [(-2, -2, -2, -2) for _ in range(len(vcolors))]

			if "LightmapUV" in mesh.uv_layers:
				lightmap_uvs = mesh.uv_layers["LightmapUV"].get_indexed()
			else:
				lightmap_uvs = mesh.uv_layers["UVMap"].get_indexed()

			mins = numpy.array([99999999.9, 99999999.9, 99999999.9])
			maxs = numpy.array([-99999999.9, -99999999.9, -99999999.9])

			positions = mesh.positions.get_indexed()
			mins[0] = min([pos[0] for pos in positions])
			mins[1] = min([pos[1] for pos in positions])
			mins[2] = min([pos[2] for pos in positions])
			maxs[0] = max([pos[0] for pos in positions])
			maxs[1] = max([pos[1] for pos in positions])
			maxs[2] = max([pos[2] for pos in positions])
			center = mins + ((maxs - mins) * 0.5)
			radius = max((maxs - mins) * 0.5)

			self.add_bsp_mesh(
				mesh.name,
				mesh.positions.get_indexed(),
				mesh.indices,
				vcolors,
				mesh.vertex_normals.get_indexed(),
				blend,
				vertex_info,
				mesh.uv_layers["UVMap"].get_indexed(),
				lightmap_uvs,
				(center, radius)
				)

	def pick_object_per_line(self, line):
		picked_obj = None
		closest_line = 0
		for object in self.opengl_objects:
			obj_line = object.new_line
			if obj_line > line:
				continue
			if obj_line > closest_line:
				closest_line = obj_line
				picked_obj = object

		if picked_obj is None:
			return
		self.unselect_all(line)
		picked_obj.selected = True
		
	def set_selected_object_position(self, vector):
		for object in self.opengl_objects:
			if object.selected:
				if object.mesh.name.startswith("*0"):
					return
				object.set_position(vector)
				return
			
	def update_selected_object_origin_text(self, vector):
		for object in self.opengl_objects:
			if object.selected:
				if object.mesh.name.startswith("*0"):
					return
				obj_end = self.text.search('}', str(object.new_line + 1)+".0", nocase=0, stopindex=END)
				idx = self.text.search('"origin"', str(object.new_line + 1)+".0", nocase=0, stopindex=obj_end)
				new_origin = ' "{} {} {}"'.format(*vector)
				try:
					line, char = idx.split(".")
				except:
					self.text.insert(str(object.new_line + 2)+".0", '"origin" ' + new_origin+"\n")
					self.text.needs_rebuild = True
					self.text.add_rebuild_event()
					return
				self.text.insert(line + ".8", new_origin)
				self.text.delete(line + "." + str(8+len(new_origin)), line + ".8" + " lineend")
				return
				
	def set_selected_object_rotation(self, vector):
		rotation = numpy.array([
			numpy.deg2rad(vector[0]),
			numpy.deg2rad(vector[1]),
			numpy.deg2rad(vector[2])
			])
		for object in self.opengl_objects:
			if object.selected:
				if object.mesh.name.startswith("*"):
					return
				object.set_rotation(rotation)
				return
				
	def set_selected_object_scale(self, vector):
		for object in self.opengl_objects:
			if object.selected:
				if object.mesh.name.startswith("*"):
					return
				object.set_scale(vector)
				return

	def clear_objects(self):
		self.opengl_lights.clear()
		self.opengl_objects.clear()
	
	def clear_meshes(self):
		self.opengl_meshes.clear()
		
	def __del__(self):
		self.opengl_lights.clear()
		self.opengl_objects.clear()
		self.opengl_meshes.clear()
		
	def append(self, text, shader_listbox, fogs_listbox, surfaces_listbox, lighting_frame):
		self.text = text
		self.shader_listbox = shader_listbox
		self.fogs_listbox = fogs_listbox
		self.surfaces_listbox = surfaces_listbox
		self.lighting_frame = lighting_frame

	def click_event(self, event):
		self.last_clicked_pixel = (event.x, event.y)
		self.get_current_ent_line(event.x, event.y)

	def drag_event(self, event):
		distance = numpy.sqrt(
			pow(event.x - self.last_clicked_pixel[0], 2.0) + 
			pow(event.x - self.last_clicked_pixel[0], 2.0))
		if distance < 7.0:
			return
		for object in self.opengl_objects:
			if object.selected:
				print(object.position, object.mesh.name)
				view_mat = numpy.transpose(self.camera.get_view())
				proj_mat = numpy.transpose(self.camera.get_projection(self.width / self.height))

				position = numpy.array(object.position) + numpy.array(object.mesh.center_radius[0])
				obj_view_pos = numpy.array(numpy.matmul(view_mat, numpy.array([*position, 1.0])))[0]
				obj_clip_pos = numpy.array(numpy.matmul(proj_mat, obj_view_pos))
				obj_clip_pos /= obj_clip_pos[3]

				half_clip = numpy.array([ event.x / self.width, (self.height - event.y) / self.height, obj_clip_pos[2] * 0.5 + 0.5, 1.0])
				clip_position = half_clip * 2.0 - numpy.array([1.0, 1.0, 1.0, 1.0])

				inverse_proj = numpy.linalg.inv(proj_mat)
				view_position = numpy.matmul(inverse_proj, clip_position)
				view_position = view_position / view_position[3]

				inverse_view = numpy.linalg.inv(view_mat)

				position = numpy.array(numpy.matmul(inverse_view, view_position))[0]
				position -= numpy.array([*object.mesh.center_radius[0], 0.0])
				position = numpy.round(position, 1)

				if self.mode == "Entities":
					self.set_selected_object_position(position[:3])
					self.update_selected_object_origin_text(position[:3])

				return position
			
	def jump_to_selected_object(self, event = None):
		for object in self.opengl_objects:
			if object.selected:
				new_pos = object.position + object.mesh.center_radius[0]
				new_pos -= self.camera.forward_vec * object.mesh.center_radius[1]
				self.camera.set_position(new_pos)

def main(root, text, shader_listbox, fog_listbox, surface_listbox, light_frame):
	app = AppOgl(root, width = 2000, height = 400)
	app.animate = 8
	app.after(200, app.printContext)
	app.append(text, shader_listbox, fog_listbox, surface_listbox, light_frame)
	app.camera.bind_camera_ctrl(app)

	app.bind("h", app.hide_selected)
	root.bind_all("<Alt-h>", app.unhide_all)
	app.bind("j", app.jump_to_selected_object)
	app.bind("<B1-Motion>", app.drag_event)
	app.bind("<Button-1>", app.click_event)
	app.bind('<Escape>', app.unselect_all)
	
	return app

if __name__ == "__main__":
	print("Please run 'main.py'")