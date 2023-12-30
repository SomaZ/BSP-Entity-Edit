import numpy

def magnitude(v):
	return numpy.sqrt(numpy.sum(v ** 2))

def normalize(v):
	m = magnitude(v)
	if m == 0:
		return v
	return v / m

def translate(xyz):
	x, y, z = xyz
	return numpy.matrix([[1,0,0,x],
					  [0,1,0,y],
					  [0,0,1,z],
					  [0,0,0,1]])

def normal_from_polar(lat, long):
	x = numpy.cos(lat) * numpy.sin(long)
	y = numpy.sin(lat) * numpy.sin(long)
	z = numpy.cos(long)
	return -numpy.array((x, y, z))

def viewPolar( f, s, u, eye ):
	M = numpy.matrix(numpy.identity(4))
	M[:3,:3] = numpy.vstack([f, s, u])
	T = translate(-numpy.array(eye))
	return M * T

class Camera():
	def __init__(self):
		self.origin = numpy.array([0., 0., 0.])
		self.rotation = [0, 0, numpy.deg2rad(90), 0]
		self.forward_vec = numpy.array([0., 0., 0.])
		self.right_vec = numpy.array([0., 0., 0.])
		self.up_vec = numpy.array([0., 0., 0.])
		self.z_near = 4.0
		self.z_far = 40000.0
		self.fov_y = 100.0
		self.key_direction =numpy.array([0.0, 0.0, 0.0])
		self.button_center = (0, 0)
		
	def set_position(self, position):
		self.origin = position
		
	def update_position(self):
		self.origin += normalize(
			self.forward_vec * self.key_direction[0] +
			self.right_vec * self.key_direction[1] +
			numpy.array([0.0, 0.0, 1.0]) * self.key_direction[2]
			) * 30.0
		
	def set_z_planes(self, z_near:float = None, z_far:float = None):
		if z_near is not None:
			self.z_near = z_near
		if z_far is not None:
			self.z_far = z_far
			
	def set_fov(self, fov:float):
		self.fov_y = fov

	def get_view(self):
		F = normal_from_polar(self.rotation[1], self.rotation[2])
		self.forward_vec = normalize(F)
		U = (0.0, 0.0, 1.0)
		self.right_vec = normalize(numpy.cross(self.forward_vec, U))
		self.up_vec = numpy.cross(self.right_vec, self.forward_vec)
		v = viewPolar(
			self.forward_vec,
			self.right_vec,
			self.up_vec,
			self.origin)
		return numpy.transpose(v)
	
	def get_projection(self, aspect_ratio:float = 1.0):
		znear = self.z_near
		zfar = self.z_far
		fov_y = self.fov_y
		depth = zfar - znear
		height = 2.0 * (znear * numpy.tan(numpy.radians(0.5 * fov_y)))
		width = height * aspect_ratio
		
		p = numpy.array(
			(
				(0., 2.0 * znear / width, 0, 0),
				(0., 0, 2.0 * znear / height, 0),
				((zfar + znear) / depth, 0, 0, (-2.0 * zfar * znear) / depth),
				(1., 0, 0, 0)
			),
			numpy.float32
		)
		return numpy.transpose(p)
	
	def bind_camera_ctrl(self, root):
		root.bind("<KeyPress-w>", self.move_fwd)
		root.bind("<KeyRelease-w>", self.move_stop_fwd)
		root.bind("<KeyPress-s>", self.move_bck)
		root.bind("<KeyRelease-s>", self.move_stop_fwd)
		root.bind("<KeyPress-a>", self.move_lft)
		root.bind("<KeyRelease-a>", self.move_stop_side)
		root.bind("<KeyPress-d>", self.move_rgt)
		root.bind("<KeyRelease-d>", self.move_stop_side)
		root.bind("<KeyPress-space>", self.move_up)
		root.bind("<KeyRelease-space>", self.move_stop_up)
		root.bind("<KeyPress-c>", self.move_down)
		root.bind("<KeyRelease-c>", self.move_stop_up)
		root.bind("<B3-Motion>", self.m3drag)
		root.bind("<Button-3>", self.m3click)
		root.bind("<MouseWheel>", self.mwheel)
		
	def stop_movement(self):
		self.key_direction = numpy.array([0.0, 0.0, 0.0])

	def move_fwd(self, event):
		self.key_direction[0] = 1.0

	def move_lft(self, event):
		self.key_direction[1] = -1.0

	def move_rgt(self, event):
		self.key_direction[1] = +1.0

	def move_bck(self, event):
		self.key_direction[0] = -1.0

	def move_up(self, event):
		self.key_direction[2] = 1.0

	def move_down(self, event):
		self.key_direction[2] = -1.0

	def move_stop_fwd(self, event):
		self.key_direction[0] = 0.0

	def move_stop_side(self, event):
		self.key_direction[1] = 0.0
		
	def move_stop_up(self, event):
		self.key_direction[2] = 0.0

	def m3click(self, event):
		self.button_center = (event.x, event.y)

	def m3drag(self, event):
		self.rotation = [
			1.0,
			self.rotation[1] + (-self.button_center[0] + event.x) * 0.003,
			self.rotation[2] + (-self.button_center[1] + event.y) * 0.003,
			0]
		self.rotation[2] = min(self.rotation[2], numpy.deg2rad(175.0))
		self.rotation[2] = max(self.rotation[2], numpy.deg2rad(5.0))
		self.button_center = (event.x, event.y)

	def mwheel(self, event):
		self.origin += event.delta * 0.5 * self.forward_vec