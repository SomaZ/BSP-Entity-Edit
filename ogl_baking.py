from dataclasses import dataclass, field
from OpenGL import GL
from ogl_objects import *
from ogl_fbo import FBO
from ogl_state import OpenGLState
import ogl_shader

bake_vertex_shader = """
in vec3 position;
in vec4 color;
in vec3 vertex_normal;
in vec4 tcs;
out vec4 ws_position;
out vec4 v_color;
out vec3 v_normal;
out vec4 v_tcs;
flat out vec4 v_info;
uniform mat4 u_model_mat;

void main()
{
   ws_position = u_model_mat*(vec4(position, 1.0));
   gl_Position = vec4(tcs.zw * 2.0 - 1.0, 0.0, 1.0);
   v_color = color;
   v_tcs = tcs;
   v_info = vec4(1.0);
   v_normal = mat3(u_model_mat)*vertex_normal;
}
"""

bake_fragment_shader = """
uniform vec4 u_position_radius;
uniform vec4 u_color_radius;
uniform samplerCubeShadow u_cubemap;
uniform sampler2D u_positionmap;
uniform sampler2D u_normalsmap;

out vec4 out_color;

float getLightDepth(in vec3 Vec, in float f)
{
	vec3 AbsVec = abs(Vec);
	float Z = max(AbsVec.x, max(AbsVec.y, AbsVec.z));

	const float n = 1.0;

	float NormZComp = (f + n) / (f - n) - 2 * f*n / (Z* (f - n));

	return ((NormZComp + 1.0) * 0.5);
}

void main()
{
	vec2 texSize = textureSize(u_positionmap, 0);
	vec2 uvCoord = gl_FragCoord.xy / texSize;
	vec4 ws_position = textureLod(u_positionmap, uvCoord, 0);

	if (ws_position.w < 0.1)
		discard;

	vec3 v_normal = textureLod(u_normalsmap, uvCoord, 0).xyz;
	vec3 N = normalize(v_normal);
	vec3 sampleVec = u_position_radius.xyz - (ws_position.xyz + (N * 0.125));
	vec3 L = normalize(sampleVec);

	//float l_depth = getLightDepth(sampleVec, max(u_position_radius.w, 1.1));
	//float shadow = texture(u_cubemap, vec4(L, l_depth));

	float l_depth = 0.0;
	float shadow = 0.0;
	vec2 stepSize = 0.4 / texSize;
	float weight = 0.0;
	for (int i = -2; i < 3; i++)
	{
		for (int j = -2; j < 3; j++)
		{
			vec4 samplePos = textureLod(u_positionmap, uvCoord + vec2(i,j) * stepSize, 0);
			sampleVec = u_position_radius.xyz - (samplePos.xyz + (N * 0.125));
			l_depth = getLightDepth(sampleVec, max(u_position_radius.w, 1.1));
			if (samplePos.a < 1.0)
				continue;
			shadow += texture(u_cubemap, vec4(normalize(sampleVec), l_depth));
			weight += 1.0;
		}
	}
	if (weight > 0.0)
		shadow /= weight;
	else
		shadow = 1.0;

	float dist = distance(ws_position.xyz, u_position_radius.xyz);
	float dist_att = u_position_radius.w / (dist * dist);
	
	float NL = max(0.0, dot(N, L));
	vec3 light = u_color_radius.rgb * NL * dist_att * shadow;

	out_color.rgb = light;
	out_color.a = 1.0;

	if (ws_position.w < 1.0)
		out_color = vec4(1.0, 0.0, 0.0, -1.0);
}
"""

bake_position_shader = """
in vec4 ws_position;
in vec3 v_normal;
in vec4 v_tcs;

out vec4 out_color;

void main()
{
	out_color.rgb = ws_position.xyz;
	out_color.a = 1.0;
}
"""

bake_normal_shader = """
in vec4 ws_position;
in vec3 v_normal;
in vec4 v_tcs;

out vec4 out_color;

void main()
{
	out_color.rgb = v_normal.xyz;
	out_color.a = 1.0;
}
"""

full_screen_vertex_shader = """

void main()
{
	const vec2 pos[] = vec2[3](
		vec2(-1.0, 1.0),
		vec2(-1.0, -3.0),
		vec2(3.0, 1.0)
	);
	gl_Position = vec4(pos[gl_VertexID], 0.0, 1.0);
}
"""

dialation_fragment_shader = """
uniform sampler2D u_lightmap;
out vec4 out_color;

ivec2 samplePoints[] = ivec2[8](
	ivec2(1, 0),
	ivec2(-1, 0),
	ivec2(0, 1),
	ivec2(0, -1),
	ivec2(1, -1),
	ivec2(1, 1),
	ivec2(-1, 1),
	ivec2(-1, -1)
);

void main()
{
	ivec2 pixel = ivec2(gl_FragCoord.xy);
	vec4 sample = texelFetch(u_lightmap, pixel, 0);
	if (sample.a < (128.0 / 255.0))
	{
		vec4 current_sample = vec4(0.0);
		float weight = 0.0;

		for (int i = 0; i < 9; i++)
		{
			current_sample = texelFetch(u_lightmap, pixel + samplePoints[i], 0);

			if (current_sample.a > (128.0 / 255.0))
			{
				vec4 change_sample = texelFetch(u_lightmap, pixel + 2*samplePoints[i], 0);
				vec4 change = vec4(0.0);
				if (change_sample.a > 128.0 / 255.0)
					change = current_sample - change_sample;
				sample = max(current_sample + change, 0.0);
				break;
			}
		}
	}
	out_color = vec4(sample);
}
"""

cube_vertex_shader = """
in vec3 position;
uniform mat4 u_proj_mat;
uniform mat4 u_model_mat;
uniform vec4 u_position_radius;
uniform int u_mode;

const mat4 viewMatrices[] = mat4[6](
	mat4(
		vec4(-1.0, 0.0, 0.0, 0.0),
		vec4(0.0, 0.0, 1.0, 0.0),
		vec4(0.0, 1.0, 0.0, 0.0),
		vec4(0.0, 0.0, 0.0, 1.0)),
	mat4(
		vec4(1.0, 0.0, 0.0, 0.0),
		vec4(0.0, 0.0, 1.0, 0.0),
		vec4(0.0, -1.0, 0.0, 0.0),
		vec4(0.0, 0.0, 0.0, 1.0)),
	mat4(
		vec4(0.0, -1.0, 0.0, 0.0),
		vec4(-1.0, 0.0, 0.0, 0.0),
		vec4(0.0, 0.0, -1.0, 0.0),
		vec4(0.0, 0.0, 0.0, 1.0)),
	mat4(
		vec4(0.0, -1.0, 0.0, 0.0),
		vec4(1.0, 0.0, 0.0, 0.0),
		vec4(0.0, 0.0, 1.0, 0.0),
		vec4(0.0, 0.0, 0.0, 1.0)),
	mat4(
		vec4(0.0, -1.0, 0.0, 0.0),
		vec4(0.0, 0.0, 1.0, 0.0),
		vec4(-1.0, 0.0, 0.0, 0.0),
		vec4(0.0, 0.0, 0.0, 1.0)),
	mat4(
		vec4(0.0, 1.0, 0.0, 0.0),
		vec4(0.0, 0.0, 1.0, 0.0),
		vec4(1.0, 0.0, 0.0, 0.0),
		vec4(0.0, 0.0, 0.0, 1.0))
);

void main()
{
	vec4 pos = (u_model_mat * vec4(position, 1.0)) - vec4(u_position_radius.xyz, 0.0);
	gl_Position = u_proj_mat * viewMatrices[u_mode] * pos;
}
"""

cube_fragment_shader = """
out vec4 out_color;
void main()
{
	out_color = vec4(0.0);
}
"""

BAKE_LIGHTMAP_SIZE = 2048
SHADOWMAP_SIZE = 512


def set_projection_matrix(zfar, shader):
	znear = 1.
	depth = zfar - znear
	height = 2.0 * (znear * numpy.tan(numpy.radians(45.0)))
	width = height
	
	p = numpy.array(
		(
			(0., 2.0 * znear / width, 0, 0),
			(0., 0, 2.0 * znear / height, 0),
			((zfar + znear) / depth, 0, 0, (-2.0 * zfar * znear) / depth),
			(1., 0, 0, 0)
		),
		numpy.float32
	)
	GL.glUniformMatrix4fv(shader.uniform_loc["u_proj_mat"], 1, GL.GL_FALSE, numpy.transpose(p))


class Baking_data():
	def __init__(self, ogl_state_manager):
		self.framebuffer_texture = GL.glGenTextures(1)
		GL.glBindTexture(GL.GL_TEXTURE_2D, self.framebuffer_texture)
		GL.glTexImage2D(
			  GL.GL_TEXTURE_2D,
			  0,
			  GL.GL_RGBA32F,
			  BAKE_LIGHTMAP_SIZE,
			  BAKE_LIGHTMAP_SIZE,
			  0,
			  GL.GL_RGBA,
			  GL.GL_UNSIGNED_BYTE,
			  ctypes.c_void_p(0))
		GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
		GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
		GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

		self.dialation_texture = GL.glGenTextures(1)
		GL.glBindTexture(GL.GL_TEXTURE_2D, self.dialation_texture)
		GL.glTexImage2D(
			  GL.GL_TEXTURE_2D,
			  0,
			  GL.GL_RGBA32F,
			  BAKE_LIGHTMAP_SIZE,
			  BAKE_LIGHTMAP_SIZE,
			  0,
			  GL.GL_RGBA,
			  GL.GL_UNSIGNED_BYTE,
			  ctypes.c_void_p(0))
		GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
		GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
		GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

		self.position_texture = GL.glGenTextures(1)
		GL.glBindTexture(GL.GL_TEXTURE_2D, self.position_texture)
		GL.glTexImage2D(
			  GL.GL_TEXTURE_2D,
			  0,
			  GL.GL_RGBA32F,
			  BAKE_LIGHTMAP_SIZE,
			  BAKE_LIGHTMAP_SIZE,
			  0,
			  GL.GL_RGBA,
			  GL.GL_UNSIGNED_BYTE,
			  ctypes.c_void_p(0))
		GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
		GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
		GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

		self.normal_texture = GL.glGenTextures(1)
		GL.glActiveTexture(GL.GL_TEXTURE2)
		GL.glBindTexture(GL.GL_TEXTURE_2D, self.normal_texture)
		GL.glTexImage2D(
			  GL.GL_TEXTURE_2D,
			  0,
			  GL.GL_RGBA32F,
			  BAKE_LIGHTMAP_SIZE,
			  BAKE_LIGHTMAP_SIZE,
			  0,
			  GL.GL_RGBA,
			  GL.GL_UNSIGNED_BYTE,
			  ctypes.c_void_p(0))
		GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
		GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
		GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
		GL.glActiveTexture(GL.GL_TEXTURE0)

		self.position_fbo = FBO(BAKE_LIGHTMAP_SIZE, BAKE_LIGHTMAP_SIZE, 0, self.position_texture)
		self.normal_fbo = FBO(BAKE_LIGHTMAP_SIZE, BAKE_LIGHTMAP_SIZE, 0, self.normal_texture)
		self.bake_fbo = FBO(BAKE_LIGHTMAP_SIZE, BAKE_LIGHTMAP_SIZE, 0, self.framebuffer_texture)
		self.dialation_fbo = FBO(BAKE_LIGHTMAP_SIZE, BAKE_LIGHTMAP_SIZE, 0, self.dialation_texture)
		self.bake_position_shader = ogl_shader.SHADER(bake_vertex_shader, bake_position_shader)
		self.bake_normal_shader = ogl_shader.SHADER(bake_vertex_shader, bake_normal_shader)
		self.bake_lightmap_shader = ogl_shader.SHADER(full_screen_vertex_shader, bake_fragment_shader)
		self.dialation_shader = ogl_shader.SHADER(full_screen_vertex_shader, dialation_fragment_shader)

		# now all the shadowing setup
		self.depth_cubemap = GL.glGenTextures(1)
		GL.glActiveTexture(GL.GL_TEXTURE2)
		GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, self.depth_cubemap)
		for i in range(6):
			GL.glTexImage2D(
				GL.GL_TEXTURE_CUBE_MAP_POSITIVE_X + i,
				0,
				GL.GL_DEPTH_COMPONENT32,
				SHADOWMAP_SIZE,
				SHADOWMAP_SIZE,
				0,
				GL.GL_DEPTH_COMPONENT,
				GL.GL_FLOAT,
				ctypes.c_void_p(0))
		GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
		GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
		GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
		GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
		GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_R, GL.GL_CLAMP_TO_EDGE)
		GL.glTexParameterf(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_COMPARE_MODE, GL.GL_COMPARE_REF_TO_TEXTURE)
		GL.glTexParameterf(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_COMPARE_FUNC, GL.GL_LEQUAL)
		GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, 0)

		GL.glActiveTexture(GL.GL_TEXTURE0)
		self.cube_fbos=[]
		for i in range(6):
			self.cube_fbos.append(FBO(SHADOWMAP_SIZE, SHADOWMAP_SIZE, 0, None, self.depth_cubemap, i))

		self.cube_shader = ogl_shader.SHADER(cube_vertex_shader, cube_fragment_shader)
		self.state = ogl_state_manager
		self.states = {}
		self.states["GBuffer_Pos"] = OpenGLState(
			framebuffer = self.position_fbo.bind,
			clear_color = (0.0, 0.0, 0.0, 0.0),
			face_culling=False,
			depth_test=False,
			depth_write=False
		)
		self.states["GBuffer_Nor"] = OpenGLState(
			framebuffer = self.normal_fbo.bind,
			clear_color = (0.0, 0.0, 0.0, 0.0),
			face_culling=False,
			depth_test=False,
			depth_write=False
		)
		self.states["Bake"] = OpenGLState(
			framebuffer = self.bake_fbo.bind,
			clear_color = (0.0, 0.0, 0.0, 0.0),
			blend = True,
			blend_func=(GL.GL_ONE, GL.GL_ONE),
			face_culling=False,
			depth_test=False,
			depth_write=False
		)
		self.states["Depth_Cube"] = OpenGLState(
			framebuffer = self.bake_fbo.bind, # wrong fbo, handle manually for now
			clear_color = (0.0, 0.0, 0.0, 0.0),
			cull_face=GL.GL_BACK,
			polygon_offset=(1.0, 1.0),
			offset_filling=True
		)
	
	def reload_cube_shader(self):
		cube_vertex_shader = open("/home/mk/Git/vertex_shader.shader", "r").read()
		self.cube_shader = ogl_shader.SHADER(cube_vertex_shader, cube_fragment_shader)

	def clear_lightmaps(self):
		self.state.change_state(self.states["Bake"])
		self.state.set_viewport(0, 0, BAKE_LIGHTMAP_SIZE, BAKE_LIGHTMAP_SIZE)
		GL.glClearColor(0.15, 0.15, 0.15, 1.0)
		self.state.state.clear_color = (0.15, 0.15, 0.15, 1.0)
		GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

	def bake_gbuffer(self, objects):
		self.state.change_state(self.states["GBuffer_Pos"])
		self.state.set_viewport(0, 0, BAKE_LIGHTMAP_SIZE, BAKE_LIGHTMAP_SIZE)
		GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
		GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
		GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, 0)
		shader = self.bake_position_shader
		GL.glUseProgram(shader.program)
		for obj in objects:
			if not obj.mesh.name.startswith("*") or obj.mesh.blend:
				continue
			GL.glUniformMatrix4fv(shader.uniform_loc["u_model_mat"], 1, GL.GL_FALSE, obj.modelMatrix)
			obj.draw()

		self.state.change_state(self.states["GBuffer_Nor"])
		GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
		shader = self.bake_normal_shader
		GL.glUseProgram(shader.program)
		for obj in objects:
			if not obj.mesh.name.startswith("*") or obj.mesh.blend:
				continue
			GL.glUniformMatrix4fv(shader.uniform_loc["u_model_mat"], 1, GL.GL_FALSE, obj.modelMatrix)
			obj.draw()
	
	def bake_lightmaps(self, objects, lights, bake_settings, refresh_func):
		self.bake_gbuffer(objects)

		self.state.change_state(self.states["Bake"])
		self.state.set_viewport(0, 0, BAKE_LIGHTMAP_SIZE, BAKE_LIGHTMAP_SIZE)
		GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
		GL.glHint(GL.GL_FRAGMENT_SHADER_DERIVATIVE_HINT, GL.GL_NICEST)

		for light_n, light in enumerate(lights):
			GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, 0)

			shader = self.cube_shader
			GL.glUseProgram(shader.program)
			GL.glUniform4f(shader.uniform_loc["u_position_radius"], *light.origin, max(float(light.radius * bake_settings.point_scale), 1.1))
			set_projection_matrix(max(float(light.radius * bake_settings.point_scale), 1.1), shader)

			self.state.change_state(self.states["Depth_Cube"])
			self.state.set_viewport(0, 0, SHADOWMAP_SIZE, SHADOWMAP_SIZE)
			
			for i in range(6):
				GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.cube_fbos[i].bind)
				GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
				GL.glUniform1i(shader.uniform_loc["u_mode"], i)
				for obj in objects:
					if not obj.mesh.name.startswith("*") or obj.mesh.blend:
						continue
					if not obj.cast_shadow:
						continue
					GL.glUniformMatrix4fv(shader.uniform_loc["u_model_mat"], 1, GL.GL_FALSE, obj.modelMatrix)
					obj.draw()
			GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.state.state.framebuffer)
			self.state.change_state(self.states["Bake"])
			self.state.set_viewport(0, 0, BAKE_LIGHTMAP_SIZE, BAKE_LIGHTMAP_SIZE)

			GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
			GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, self.depth_cubemap)

			shader = self.bake_lightmap_shader
			GL.glUseProgram(shader.program)
			GL.glUniform4f(shader.uniform_loc["u_position_radius"], *light.origin, float(light.radius * bake_settings.point_scale))
			GL.glUniform4f(shader.uniform_loc["u_color_radius"], *light.color, float(light.radius * bake_settings.point_scale))
			
			GL.glActiveTexture(GL.GL_TEXTURE0)
			GL.glBindTexture(GL.GL_TEXTURE_2D, self.position_texture)
			GL.glUniform1i(shader.uniform_loc["u_positionmap"], 0)
			GL.glActiveTexture(GL.GL_TEXTURE1)
			GL.glBindTexture(GL.GL_TEXTURE_2D, self.normal_texture)
			GL.glUniform1i(shader.uniform_loc["u_normalsmap"], 1)
			GL.glActiveTexture(GL.GL_TEXTURE2)
			GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, self.depth_cubemap)
			GL.glUniform1i(shader.uniform_loc["u_cubemap"], 2)

			GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)

			GL.glActiveTexture(GL.GL_TEXTURE0)
			GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
			GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, 0)

			if refresh_func is not None and light_n%10 == 0:
				refresh_func(True)
		
		self.state.change_state(self.states["Bake"])
		self.state.set_viewport(0, 0, BAKE_LIGHTMAP_SIZE, BAKE_LIGHTMAP_SIZE)
		GL.glDisable(GL.GL_BLEND)
		self.state.state.blend = False
		for _ in range(8):
			GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.dialation_fbo.bind)
			GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, self.bake_fbo.bind)
			GL.glBlitFramebuffer(0, 0, BAKE_LIGHTMAP_SIZE, BAKE_LIGHTMAP_SIZE, 0, 0, BAKE_LIGHTMAP_SIZE, BAKE_LIGHTMAP_SIZE, GL.GL_COLOR_BUFFER_BIT, GL.GL_NEAREST)
			GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.bake_fbo.bind)
			self.state.state.framebuffer = self.bake_fbo.bind

			GL.glUseProgram(self.dialation_shader.program)
			GL.glBindTexture(GL.GL_TEXTURE_2D, self.dialation_texture)
			GL.glUniform1i(self.dialation_shader.uniform_loc["u_lightmap"], 0)
			GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)
			GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
			

if __name__ == "__main__":
	print("Please run 'main.py'")