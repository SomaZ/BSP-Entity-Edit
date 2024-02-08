from OpenGL import GL
import OpenGL.GL.shaders

UNIFORM_LIST = [
	"u_model_mat",
	"u_view_mat",
	"u_proj_mat",
	"u_gamma",
	"u_compensate",
	"u_obb",
	"u_lightScale",
	"u_color",
	"u_line",
	"u_pick",
	"u_mode",
	"u_position_radius",
	"u_color_radius",
	"u_positionmap",
	"u_normalsmap", # for stored vertex normals
	"u_lightmap",
	"u_cubemap",
	"u_bouncemap"
]

SAMPLER_LIST = {
	"u_positionmap": 0,
	"u_normalsmap": 1,
	"u_lightmap": 0,
	"u_cubemap": 2,
	"u_bouncemap": 1
}

SHADER_HEADER = """#version 130
#define M_PI float(3.1415926535)
"""

vertex_shader = """
in vec3 position;
in vec4 color;
in vec3 vertex_normal;
in vec4 tcs;
in vec4 vertex_info;
out vec4 ws_position;
out vec4 v_color;
out vec3 v_normal;
out vec4 v_tcs;
flat out vec4 v_info;
uniform mat4 u_proj_mat;
uniform mat4 u_view_mat;
uniform mat4 u_model_mat;
uniform int u_mode;

vec4 encode_int(in int value)
{
	float r = ((value & 0x000000FF) ) / 255.0;
	float g = ((value & 0x0000FF00) >>  8) / 255.0;
	float b = ((value & 0x00FF0000) >> 16) / 255.0;
	return vec4(r, g, b, float(value));
}

void main()
{
   ws_position = u_model_mat*(vec4(position, 1.0));
   gl_Position = u_proj_mat*u_view_mat*u_model_mat*(vec4(position, 1.0));
   v_color = color;
   v_tcs = tcs;
   int info[4] = int[4](int(vertex_info.x), int(vertex_info.y), int(vertex_info.z), int(vertex_info.w));
   v_info = encode_int(info[u_mode]);
   // FIXME: use normal matrix instead of model matrix
   v_normal = mat3(u_model_mat)*vertex_normal;
}
"""

fragment_shader = """
in vec4 v_color;
in vec3 v_normal;
in vec4 v_tcs;
uniform vec4 u_color;

out vec4 out_color;

void main()
{
	vec3 color = mix(v_color.rgb, u_color.rgb, u_color.a);
	
	vec3 n = normalize(v_normal.xyz);
	const vec3 test_n = normalize(vec3(-0.4, 0.3, 0.5));
	float shade = clamp(dot(test_n, n) * 0.15, -0.15, 0.15) + 0.85;
	
	out_color.rgb = clamp(color * shade, 0.0, 1.0);
	out_color.a = v_color.a;
}
"""

lightmap_fragment_shader = """
in vec4 v_color;
in vec3 v_normal;
in vec4 v_tcs;
uniform vec4 u_color;
uniform sampler2D u_lightmap;
uniform sampler2D u_bouncemap;
uniform float u_gamma;
uniform float u_compensate;
uniform float u_obb;
uniform float u_lightScale;

out vec4 out_color;

void main()
{
	vec3 color = max(texture(u_lightmap, v_tcs.zw).rgb * u_lightScale, vec3(0.0));
	color += max(texture(u_bouncemap, v_tcs.zw).rgb * u_lightScale, vec3(0.0));

	color = pow(color, vec3(1.0 / u_gamma));

	float max_v = max(color.r, max(color.g, color.b));
	if (max_v > 1.0)
	{
		color /= max_v;
	}

	color *= (pow(2.0, u_obb)) / u_compensate;
	
	vec3 n = normalize(v_normal.xyz);
	const vec3 test_n = normalize(vec3(-0.4, 0.3, 0.5));
	float shade = clamp(dot(test_n, n) * 0.15, -0.15, 0.15) + 0.85;
	
	out_color.rgb = clamp(color * shade, 0.0, 1.0);
	out_color.a = 1.0;
}
"""

fragment_select_shader = """
in vec4 v_color;
in vec3 v_normal;
in vec4 v_tcs;
flat in vec4 v_info;
uniform int u_mode;
uniform int u_pick;

out vec4 out_color;

void main()
{
	vec3 color = mix(v_color.rgb, vec3(1., .01, 1.), float(u_pick == int(v_info.w)) * 0.5);
	
	vec3 n = normalize(v_normal.xyz);
	const vec3 test_n = normalize(vec3(-0.4, 0.3, 0.5));
	float shade = clamp(dot(test_n, n) * 0.15, -0.15, 0.15) + 0.85;
	
	out_color.rgb = clamp(color * shade, 0.0, 1.0);
	out_color.a = v_color.a;
}
"""

pick_fragment_shader = """
in vec4 v_color;
in vec3 v_normal;
in vec4 v_tcs;
flat in vec4 v_info;
uniform vec4 u_line;

out vec4 out_color;

void main()
{
   out_color = u_line;
}
"""

pick_mode_fragment_shader = """
in vec4 v_color;
in vec3 v_normal;
in vec4 v_tcs;
flat in vec4 v_info; // vert, surface, shader, fog
uniform vec4 u_line;

out vec4 out_color;

void main()
{
   out_color = vec4(v_info.rgb, 0.0);
}
"""

SHADER_LIST = [
	["Vertex_Color", vertex_shader, fragment_shader],
	["Vertex_Color_Selection", vertex_shader, fragment_select_shader],
	["Pick_Object", vertex_shader, pick_fragment_shader],
	["Pick_Selection", vertex_shader, pick_mode_fragment_shader],
	["Lightmap_Color", vertex_shader, lightmap_fragment_shader]
]

class SHADER():
	def __init__(self, vertex_shader, fragment_shader):
		self.uniform_loc = {}
		self.program = OpenGL.GL.shaders.compileProgram(
				self.compileShader(vertex_shader, GL.GL_VERTEX_SHADER),
				self.compileShader(fragment_shader, GL.GL_FRAGMENT_SHADER),
				validate = False
				)
		for uniform in UNIFORM_LIST:
			self.uniform_loc[uniform] = GL.glGetUniformLocation(self.program, self.bytestr(uniform))
		GL.glUseProgram(self.program)
		for uniform in UNIFORM_LIST:
			if uniform in SAMPLER_LIST and self.uniform_loc[uniform] > -1:
				GL.glUniform1i(self.uniform_loc[uniform], SAMPLER_LIST[uniform])
		GL.glUseProgram(0)

		self.program.check_validate()
		

	# Avoiding glitches in pyopengl-3.0.x and python3.4
	def bytestr(self, s):
		return s.encode("utf-8") + b"\000"


	# Avoiding glitches in pyopengl-3.0.x and python3.4
	def compileShader(self, source, shaderType):
		"""
		Compile shader source of given type
			source -- GLSL source-code for the shader
		shaderType -- GLenum GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, etc,
			returns GLuint compiled shader reference
		raises RuntimeError when a compilation failure occurs
		"""
		if isinstance(source, str):
			source = [source]
		elif isinstance(source, bytes):
			source = [source.decode('utf-8')]

		shader = GL.glCreateShader(shaderType)
		source = [SHADER_HEADER + source[0]]
		GL.glShaderSource(shader, source)
		GL.glCompileShader(shader)

		result = GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS)
		if not(result):
			# TODO: this will be wrong if the user has
			# disabled traditional unpacking array support.
			raise RuntimeError(
				"""Shader compile failure (%s): %s""" % (
					result,
					GL.glGetShaderInfoLog(shader),
				),
				source,
				shaderType,
			)
		return shader
	
	#TODO: check if python OpenGL deletes the buffers correcly

if __name__ == "__main__":
	print("Please run 'main.py'")