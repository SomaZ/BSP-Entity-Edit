from OpenGL import GL

class FBO():
	def __init__(
			self,
			width,
			height,
			multisample,
			texture = None,
			depth_texture = None,
			cubeface = None,
			):
		self.width = width
		self.height = height
		self.texture = texture
		self.depth_texture = depth_texture
		self.target = (GL.GL_TEXTURE_2D if cubeface is None else GL.GL_TEXTURE_CUBE_MAP_POSITIVE_X + cubeface)
		self.bind = GL.glGenFramebuffers(1)
		GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.bind)
		
		if self.depth_texture is None:
			self.depth_rbo = GL.glGenRenderbuffers(1)
			GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, self.depth_rbo)
			if multisample > 0:
				GL.glRenderbufferStorageMultisample(GL.GL_RENDERBUFFER, multisample, GL.GL_DEPTH24_STENCIL8, width, height)
			else:
				GL.glRenderbufferStorage(GL.GL_RENDERBUFFER, GL.GL_DEPTH24_STENCIL8, width, height)
			GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, 0)
			GL.glFramebufferRenderbuffer(GL.GL_FRAMEBUFFER, GL.GL_DEPTH_STENCIL_ATTACHMENT, GL.GL_RENDERBUFFER, self.depth_rbo)
		else:
			GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER,
							 GL.GL_DEPTH_ATTACHMENT,
							 self.target,
							 self.depth_texture,
							 0)

		if self.texture is None:
			if self.depth_texture is None:
				self.color_rbo = GL.glGenRenderbuffers(1)
				GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, self.color_rbo)
				if multisample > 0:
					GL.glRenderbufferStorageMultisample(GL.GL_RENDERBUFFER, multisample, GL.GL_RGBA8, width, height)
				else:
					GL.glRenderbufferStorage(GL.GL_RENDERBUFFER, GL.GL_RGBA8, width, height)
				GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, 0)
				GL.glFramebufferRenderbuffer(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_RENDERBUFFER, self.color_rbo)
		else:
			GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER,
							 GL.GL_COLOR_ATTACHMENT0,
							 self.target,
							 self.texture,
							 0)
		
		if self.texture is None and self.depth_texture is not None:
			GL.glReadBuffer(GL.GL_NONE)
			GL.glDrawBuffer(GL.GL_NONE)
		else:
			GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT0)
			GL.glDrawBuffers(1, [GL.GL_COLOR_ATTACHMENT0])

		if (GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER) != GL.GL_FRAMEBUFFER_COMPLETE):
			print("Framebuffer not complete sucker!!")
		
		GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
		
	def __del__(self):
		if hasattr(self, "color_rbo"):
			GL.glDeleteRenderbuffers(1, [self.color_rbo])
		if hasattr(self, "depth_rbo"):
			GL.glDeleteRenderbuffers(1, [self.depth_rbo])
		GL.glDeleteFramebuffers(1, [self.bind])

if __name__ == "__main__":
	print("Please run 'main.py'")