from OpenGL import GL
import numpy
import ctypes
import types
import sys

# from https://www.meccanismocomplesso.org/en/3d-rotations-and-euler-angles-in-python/
def Rx(theta):
	return numpy.matrix([[ 1, 0           , 0           ],
                   [ 0, numpy.cos(theta),-numpy.sin(theta)],
                   [ 0, numpy.sin(theta), numpy.cos(theta)]])
  
def Ry(theta):
	return numpy.matrix([[ numpy.cos(theta), 0, numpy.sin(theta)],
                   [ 0           , 1, 0           ],
                   [-numpy.sin(theta), 0, numpy.cos(theta)]])
  
def Rz(theta):
	return numpy.matrix([[ numpy.cos(theta), -numpy.sin(theta), 0 ],
                   [ numpy.sin(theta), numpy.cos(theta) , 0 ],
                   [ 0           , 0            , 1 ]])
				   
def m_translate(xyz):
	x, y, z = xyz
	return numpy.matrix(
		[[1,0,0,x],
		[0,1,0,y],
		[0,0,1,z],
		[0,0,0,1]])
					  
def m_scale(xyz):
	x, y, z = xyz
	return numpy.matrix(
		[[x,0,0,0],
		[0,y,0,0],
		[0,0,z,0],
		[0,0,0,1]])

class OpenGLObject():
	def __init__(self, mesh, position, rotation, scale):
		self.mesh = mesh
		self.position = position
		self.rotation = rotation
		self.scale = scale
		
		rotation_m = (
			Rz(rotation[2]) * 
			Ry(rotation[1]) * 
			Rx(rotation[0])
		)
		R = numpy.matrix(numpy.identity(4))
		R[:3,:3] = numpy.vstack(
			[rotation_m[0],
			rotation_m[1],
			rotation_m[2]]
		)
		T = m_translate(position)
		S = m_scale(scale)
		
		self.modelMatrix = numpy.transpose(T * R * S)
		self.new_line = 0
		self.encoded_object_index = [0.0, 0.0, 0.0, 0.0]
		self.selected = False
		self.hidden = False
		
	def draw(self, type = None):
		GL.glBindVertexArray(self.mesh.vertex_array_object)
		
		if self.mesh.num_indices != None:
			if type is None:
				GL.glDrawElements(
					self.mesh.render_type,
					self.mesh.num_indices,
					GL.GL_UNSIGNED_INT,
					ctypes.c_void_p(0))
			else:
				GL.glDrawElements(
					type,
					self.mesh.num_indices,
					GL.GL_UNSIGNED_INT,
					ctypes.c_void_p(0))
		else:
			GL.glDrawArrays(self.mesh.render_type, 0, self.mesh.num_vertices)

		GL.glBindVertexArray(0)
		
	
class OpenGLMesh():
	def __init__(self, positions, indices = None, colors = None, blend = None):
		if positions is None:
			raise Exception("Could not create OpenGL Object")
			
		self.render_type = GL.GL_POINTS
		self.blend = blend
		
		# Create a new VAO (Vertex Array Object) and bind it
		self.vertex_array_object = GL.glGenVertexArrays(1)
		GL.glBindVertexArray(self.vertex_array_object)
		
		# Generate buffers to hold our vertices
		self.vertex_buffer = GL.glGenBuffers(1)
		GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vertex_buffer)
		
		# Send the data over to the buffer (bytes)
		vs = positions
		GL.glBufferData(GL.GL_ARRAY_BUFFER, len(vs) * ctypes.sizeof(ctypes.c_float), vs, GL.GL_STATIC_DRAW)
		
		self.num_vertices = len(vs)
		
		# Describe the position data layout in the buffer
		GL.glEnableVertexAttribArray(0)
		GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, False,
								 0, ctypes.c_void_p(0))
								 
		if colors is not None:
			self.color_buffer = GL.glGenBuffers(1)
			GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.color_buffer)		
			vs = colors
			GL.glBufferData(GL.GL_ARRAY_BUFFER, len(vs), vs, GL.GL_STATIC_DRAW)	
			# Describe the position data layout in the buffer
			GL.glEnableVertexAttribArray(1)
			GL.glVertexAttribPointer(1, 4, GL.GL_UNSIGNED_BYTE, True,
									 0, ctypes.c_void_p(0))
		
		if indices is not None:
			# Generate buffers to hold our indices
			self.index_buffer = GL.glGenBuffers(1)
			GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)
			GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, len(indices) * ctypes.sizeof(ctypes.c_uint), indices, GL.GL_STATIC_DRAW)
			self.num_indices = len(indices)
			self.render_type = GL.GL_TRIANGLES
								 
		# Unbind the VAO first (Important)
		GL.glBindVertexArray(0)
		GL.glDisableVertexAttribArray(0)
		GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
		GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
		print("created mesh			")
		
	def __del__(self):
		GL.glDeleteVertexArrays(1, [self.vertex_array_object])
		GL.glDeleteBuffers(1, [self.vertex_buffer])
		print("deleted mesh			 ")
		
		
box_verts = ((-8.0, -8.0, -8.0),
         (-8.0, -8.0, 8.0),
         (-8.0, 8.0, -8.0),
         (-8.0, 8.0, 8.0),
         (8.0, -8.0, -8.0),
         (8.0, -8.0, 8.0),
         (8.0, 8.0, -8.0),
         (8.0, 8.0, 8.0))
		 
red_box_colors = ((255.0, 10.0, 10.0, 255.0),
         (255.0, 10.0, 10.0, 255.0),
         (255.0, 10.0, 10.0, 255.0),
         (255.0, 10.0, 10.0, 255.0),
         (10.0, 10.0, 10.0, 255.0),
         (10.0, 10.0, 10.0, 255.0),
         (10.0, 10.0, 10.0, 255.0),
         (10.0, 10.0, 10.0, 255.0))
		 
blue_box_colors = ((10.0, 10.0, 255.0, 255.0),
         (10.0, 10.0, 255.0, 255.0),
         (10.0, 10.0, 255.0, 255.0),
         (10.0, 10.0, 255.0, 255.0),
         (10.0, 10.0, 10.0, 255.0),
         (10.0, 10.0, 10.0, 255.0),
         (10.0, 10.0, 10.0, 255.0),
         (10.0, 10.0, 10.0, 255.0))
		 
cyan_box_colors = ((10.0, 128.0, 255.0, 255.0),
         (10.0, 128.0, 255.0, 255.0),
         (10.0, 128.0, 255.0, 255.0),
         (10.0, 128.0, 255.0, 255.0),
         (10.0, 10.0, 10.0, 255.0),
         (10.0, 10.0, 10.0, 255.0),
         (10.0, 10.0, 10.0, 255.0),
         (10.0, 10.0, 10.0, 255.0))
		 
green_box_colors = ((10.0, 255.0, 10.0, 255.0),
         (10.0, 255.0, 10.0, 255.0),
         (10.0, 255.0, 10.0, 255.0),
         (10.0, 255.0, 10.0, 255.0),
         (10.0, 10.0, 10.0, 255.0),
         (10.0, 10.0, 10.0, 255.0),
         (10.0, 10.0, 10.0, 255.0),
         (10.0, 10.0, 10.0, 255.0))

box_indices = ((0, 1, 3, 2),
         (2, 3, 7, 6),
         (6, 7, 5, 4),
         (4, 5, 1, 0),
         (2, 6, 4, 0),
         (7, 3, 1, 5))

if __name__ == "__main__":
	print("Please run 'main.py'")