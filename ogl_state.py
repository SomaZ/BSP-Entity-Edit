from OpenGL import GL
from dataclasses import dataclass

@dataclass
class OpenGLState():
    depth_write:bool = True
    depth_test:bool = True
    depth_func:int = GL.GL_LEQUAL
    depth_range:tuple() = (0.0, 1.0)
    face_culling:bool = True
    cull_face:int = GL.GL_FRONT
    offset_filling:bool = False
    polygon_offset:tuple() = (-1.0, 1.0)
    blend:bool = False
    blend_func:tuple() = (GL.GL_ONE, GL.GL_ONE)
    framebuffer:int = 0
    clear_color:tuple() = (0.15, 0.15, 0.15, 1.0)
    clear_depth:float = 1.0


class OpenGLStateManager():
    def __init__(self, x, y, width, height):
        self.state = OpenGLState()
        self.view_port = (x, y, width, height)
        GL.glClearColor(0.15, 0.15, 0.15, 1.0)
        GL.glDepthFunc(GL.GL_LEQUAL)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDepthMask(GL.GL_TRUE)

        GL.glEnable(GL.GL_CULL_FACE)
        GL.glCullFace(GL.GL_FRONT)
        
        GL.glDisable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE)

        GL.glPolygonOffset(-1.0, 1.0)
        GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)

        GL.glViewport(*self.view_port)

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    def set_viewport(self, x, y, width, height):
        if self.view_port != (x, y, width, height):
            self.view_port = (x, y, width, height)
            GL.glViewport(*self.view_port)

    def change_state(self, new_state:OpenGLState):
        if self.state.depth_write != new_state.depth_write:
            self.state.depth_write = new_state.depth_write
            GL.glDepthMask(GL.GL_TRUE if self.state.depth_write else GL.GL_FALSE)
        if self.state.depth_test != new_state.depth_test:
            self.state.depth_test = new_state.depth_test
            func = GL.glEnable if self.state.depth_test else GL.glDisable
            func(GL.GL_DEPTH_TEST)
        if self.state.depth_range != new_state.depth_range:
            self.state.depth_range = new_state.depth_range
        if self.state.face_culling != new_state.face_culling:
            self.state.face_culling = new_state.face_culling
            func = GL.glEnable if self.state.face_culling else GL.glDisable
            func(GL.GL_CULL_FACE)
        if self.state.cull_face != new_state.cull_face:
            self.state.cull_face = new_state.cull_face
            GL.glCullFace(self.state.cull_face)
        if self.state.offset_filling != new_state.offset_filling:
            self.state.offset_filling = new_state.offset_filling
            func = GL.glEnable if self.state.offset_filling else GL.glDisable
            func(GL.GL_POLYGON_OFFSET_FILL)
        if self.state.polygon_offset != new_state.polygon_offset:
            self.state.polygon_offset = new_state.polygon_offset
            GL.glPolygonOffset(*self.state.polygon_offset)
        if self.state.blend != new_state.blend:
            self.state.blend = new_state.blend
            func = GL.glEnable if self.state.blend else GL.glDisable
            func(GL.GL_BLEND)
        if self.state.blend_func != new_state.blend_func:
            self.state.blend_func = new_state.blend_func
            GL.glBlendFunc(*self.state.blend_func)
        if self.state.framebuffer != new_state.framebuffer:
            self.state.framebuffer = new_state.framebuffer
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.state.framebuffer)
        if self.state.clear_color != new_state.clear_color:
            self.state.clear_color = new_state.clear_color
            GL.glClearColor(*self.state.clear_color)
        if self.state.clear_depth != new_state.clear_depth:
            self.state.clear_depth = new_state.clear_depth
            GL.glClearDepth(self.state.clear_depth)
