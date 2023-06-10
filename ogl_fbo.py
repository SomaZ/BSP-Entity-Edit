from OpenGL import GL

class FBO():
	def __init__(self, width, height, multisample):
		self.width = width
		self.height = height
		self.bind = GL.glGenFramebuffers(1)
		GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.bind)
		
		self.depth_rbo = GL.glGenRenderbuffers(1)
		GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, self.depth_rbo)
		if multisample > 0:
			GL.glRenderbufferStorageMultisample(GL.GL_RENDERBUFFER, multisample, GL.GL_DEPTH24_STENCIL8, width, height)
		else:
			GL.glRenderbufferStorage(GL.GL_RENDERBUFFER, GL.GL_DEPTH24_STENCIL8, width, height)
		GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, 0)
		
		self.color_rbo = GL.glGenRenderbuffers(1)
		GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, self.color_rbo)
		if multisample > 0:
			GL.glRenderbufferStorageMultisample(GL.GL_RENDERBUFFER, 4, GL.GL_RGBA8, width, height)
		else:
			GL.glRenderbufferStorage(GL.GL_RENDERBUFFER, GL.GL_RGBA8, width, height)
		GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, 0)
		
		#self.line_rbo = GL.glGenRenderbuffers(1)
		#GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, self.line_rbo)
		#GL.glRenderbufferStorageMultisample(GL.GL_RENDERBUFFER, 4, GL.GL_RGBA8, width, height)
		#GL.glRenderbufferStorage(GL.GL_RENDERBUFFER, GL.GL_RGBA8, width, height)
		#GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, 0)
		
		GL.glFramebufferRenderbuffer(GL.GL_FRAMEBUFFER, GL.GL_DEPTH_STENCIL_ATTACHMENT, GL.GL_RENDERBUFFER, self.depth_rbo)
		GL.glFramebufferRenderbuffer(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_RENDERBUFFER, self.color_rbo)
		#GL.glFramebufferRenderbuffer(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT1, GL.GL_RENDERBUFFER, self.line_rbo)
		
		GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT0)
		#GL.glDrawBuffers(2, [GL.GL_COLOR_ATTACHMENT0, GL.GL_COLOR_ATTACHMENT1])
		GL.glDrawBuffers(1, [GL.GL_COLOR_ATTACHMENT0])
		
		GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
		
	def __del__(self):
		GL.glDeleteRenderbuffers(1, [self.color_rbo])
		GL.glDeleteRenderbuffers(1, [self.depth_rbo])
		#GL.glDeleteRenderbuffers(1, [self.line_rbo])
		GL.glDeleteFramebuffers(1, [self.bind])

if __name__ == "__main__":
	print("Please run 'main.py'")