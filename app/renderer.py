"""
Renderer: handles shader compilation, geometry creation, and rendering
"""

from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import glm
from app.scene import Scene
from app.camera import Camera


class Renderer:
    def __init__(self, scene):
        self.scene = scene

        # Shaders
        self.pbr_shader = None
        self.grid_shader = None
        self.light_shader = None

        # VAOs and VBOs
        self.sphere_vao = None
        self.sphere_vbo = None
        self.sphere_ebo = None
        self.sphere_index_count = 0

        self.grid_vao = None
        self.grid_vbo = None
        self.grid_vertex_count = 0

        self.light_vao = None
        self.light_vbo = None
        self.light_ebo = None
        self.light_index_count = 0

        self.init_shaders()
        self.init_geometry()

    def init_shaders(self):
        """Initialize all shaders"""
        pbr_vs = self.pbr_vertex_shader_source()
        pbr_fs = self.pbr_fragment_shader_source()
        self.pbr_shader = compileProgram(
            compileShader(pbr_vs, GL_VERTEX_SHADER),
            compileShader(pbr_fs, GL_FRAGMENT_SHADER),
        )

        grid_vs = self.grid_vertex_shader_source()
        grid_fs = self.grid_fragment_shader_source()
        self.grid_shader = compileProgram(
            compileShader(grid_vs, GL_VERTEX_SHADER),
            compileShader(grid_fs, GL_FRAGMENT_SHADER),
        )

        light_vs = self.light_vertex_shader_source()
        light_fs = self.light_fragment_shader_source()
        self.light_shader = compileProgram(
            compileShader(light_vs, GL_VERTEX_SHADER),
            compileShader(light_fs, GL_FRAGMENT_SHADER),
        )

    def init_geometry(self):
        """Initialize geometry buffers"""
        self.create_sphere()
        self.create_grid()
        self.create_light_sphere()

    def create_sphere(self):
        """Create sphere geometry"""
        positions = []
        normals = []
        indices = []

        rings = self.scene.sphere_rings
        segments = self.scene.sphere_segments
        radius = self.scene.sphere_radius

        # Generate vertices
        for r in range(rings + 1):
            phi = glm.pi() * r / rings
            y = glm.cos(phi) * radius

            ring_radius = glm.sin(phi) * radius

            for s in range(segments + 1):
                theta = 2 * glm.pi() * s / segments
                x = ring_radius * glm.cos(theta)
                z = ring_radius * glm.sin(theta)

                positions.extend([x, y, z])

                # Normal is the normalized position (for a sphere centered at origin)
                norm = glm.normalize(glm.vec3(x, y, z))
                normals.extend([norm.x, norm.y, norm.z])

        # Generate indices
        for r in range(rings):
            for s in range(segments):
                # Current ring indices
                i0 = r * (segments + 1) + s
                i1 = r * (segments + 1) + s + 1
                i2 = (r + 1) * (segments + 1) + s
                i3 = (r + 1) * (segments + 1) + s + 1

                # Two triangles per quad
                indices.extend([i0, i2, i1])
                indices.extend([i1, i2, i3])

        self.sphere_index_count = len(indices)

        # Create VAO
        self.sphere_vao = glGenVertexArrays(1)
        glBindVertexArray(self.sphere_vao)

        # Position VBO
        self.sphere_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.sphere_vbo)
        glBufferData(
            GL_ARRAY_BUFFER,
            len(positions) * 4,
            np.array(positions, dtype=np.float32),
            GL_STATIC_DRAW,
        )
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

        # Normal VBO
        normal_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, normal_vbo)
        glBufferData(
            GL_ARRAY_BUFFER,
            len(normals) * 4,
            np.array(normals, dtype=np.float32),
            GL_STATIC_DRAW,
        )
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)

        # EBO
        self.sphere_ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.sphere_ebo)
        glBufferData(
            GL_ELEMENT_ARRAY_BUFFER,
            len(indices) * 4,
            np.array(indices, dtype=np.uint32),
            GL_STATIC_DRAW,
        )

        glBindVertexArray(0)

    def create_grid(self):
        """Create grid geometry"""
        positions = []
        size = self.scene.grid_size
        spacing = self.scene.grid_spacing

        # Create horizontal lines
        for i in range(-size, size + 1):
            x = i * spacing
            positions.extend([x, 0.0, -size * spacing])
            positions.extend([x, 0.0, size * spacing])

        # Create vertical lines
        for i in range(-size, size + 1):
            z = i * spacing
            positions.extend([-size * spacing, 0.0, z])
            positions.extend([size * spacing, 0.0, z])

        self.grid_vertex_count = len(positions) // 3

        # Create VAO
        self.grid_vao = glGenVertexArrays(1)
        glBindVertexArray(self.grid_vao)

        self.grid_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.grid_vbo)
        glBufferData(
            GL_ARRAY_BUFFER,
            len(positions) * 4,
            np.array(positions, dtype=np.float32),
            GL_STATIC_DRAW,
        )
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

        glBindVertexArray(0)

    def create_light_sphere(self):
        """Create a small sphere for representing the light position"""
        positions = []
        indices = []

        rings = 16
        segments = 16
        radius = self.scene.light_radius

        for r in range(rings + 1):
            phi = glm.pi() * r / rings
            y = glm.cos(phi) * radius
            ring_radius = glm.sin(phi) * radius

            for s in range(segments + 1):
                theta = 2 * glm.pi() * s / segments
                x = ring_radius * glm.cos(theta)
                z = ring_radius * glm.sin(theta)
                positions.extend([x, y, z])

        for r in range(rings):
            for s in range(segments):
                i0 = r * (segments + 1) + s
                i1 = r * (segments + 1) + s + 1
                i2 = (r + 1) * (segments + 1) + s
                i3 = (r + 1) * (segments + 1) + s + 1
                indices.extend([i0, i2, i1])
                indices.extend([i1, i2, i3])

        self.light_index_count = len(indices)

        self.light_vao = glGenVertexArrays(1)
        glBindVertexArray(self.light_vao)

        self.light_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.light_vbo)
        glBufferData(
            GL_ARRAY_BUFFER,
            len(positions) * 4,
            np.array(positions, dtype=np.float32),
            GL_STATIC_DRAW,
        )
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

        self.light_ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.light_ebo)
        glBufferData(
            GL_ELEMENT_ARRAY_BUFFER,
            len(indices) * 4,
            np.array(indices, dtype=np.uint32),
            GL_STATIC_DRAW,
        )

        glBindVertexArray(0)

    def render(self, camera):
        """Render the scene"""
        view = camera.get_view_matrix()
        projection = camera.get_projection_matrix()

        # Render grid
        self.render_grid(view, projection)

        # Render PBR sphere
        self.render_pbr_sphere(view, projection, camera)

        # Render light sphere
        self.render_light_sphere(view, projection)

    def render_grid(self, view, projection):
        """Render the grid"""
        glUseProgram(self.grid_shader)

        model = glm.mat4(1.0)
        glUniformMatrix4fv(
            glGetUniformLocation(self.grid_shader, "model"),
            1,
            GL_FALSE,
            glm.value_ptr(model),
        )
        glUniformMatrix4fv(
            glGetUniformLocation(self.grid_shader, "view"),
            1,
            GL_FALSE,
            glm.value_ptr(view),
        )
        glUniformMatrix4fv(
            glGetUniformLocation(self.grid_shader, "projection"),
            1,
            GL_FALSE,
            glm.value_ptr(projection),
        )

        glBindVertexArray(self.grid_vao)
        glDrawArrays(GL_LINES, 0, self.grid_vertex_count)
        glBindVertexArray(0)

    def render_pbr_sphere(self, view, projection, camera):
        """Render PBR sphere"""
        glUseProgram(self.pbr_shader)

        # Model matrix
        model = glm.translate(glm.mat4(1.0), self.scene.sphere_pos)

        # Set uniforms
        glUniformMatrix4fv(
            glGetUniformLocation(self.pbr_shader, "model"),
            1,
            GL_FALSE,
            glm.value_ptr(model),
        )
        glUniformMatrix4fv(
            glGetUniformLocation(self.pbr_shader, "view"),
            1,
            GL_FALSE,
            glm.value_ptr(view),
        )
        glUniformMatrix4fv(
            glGetUniformLocation(self.pbr_shader, "projection"),
            1,
            GL_FALSE,
            glm.value_ptr(projection),
        )

        # Material uniforms
        glUniform3f(
            glGetUniformLocation(self.pbr_shader, "albedo"),
            self.scene.albedo.x,
            self.scene.albedo.y,
            self.scene.albedo.z,
        )
        glUniform1f(
            glGetUniformLocation(self.pbr_shader, "metallic"), self.scene.metallic
        )
        glUniform1f(
            glGetUniformLocation(self.pbr_shader, "roughness"), self.scene.roughness
        )
        glUniform1f(glGetUniformLocation(self.pbr_shader, "ao"), self.scene.ao)

        # Light uniforms
        glUniform3f(
            glGetUniformLocation(self.pbr_shader, "lightPositions[0]"),
            self.scene.light_pos.x,
            self.scene.light_pos.y,
            self.scene.light_pos.z,
        )
        glUniform3f(
            glGetUniformLocation(self.pbr_shader, "lightColors[0]"),
            self.scene.light_color.x * self.scene.light_intensity,
            self.scene.light_color.y * self.scene.light_intensity,
            self.scene.light_color.z * self.scene.light_intensity,
        )

        # Attenuation
        glUniform1f(
            glGetUniformLocation(self.pbr_shader, "lightConstant"),
            self.scene.light_attenuation_const,
        )
        glUniform1f(
            glGetUniformLocation(self.pbr_shader, "lightLinear"),
            self.scene.light_attenuation_linear,
        )
        glUniform1f(
            glGetUniformLocation(self.pbr_shader, "lightQuadratic"),
            self.scene.light_attenuation_quad,
        )

        # Camera position
        glUniform3f(
            glGetUniformLocation(self.pbr_shader, "camPos"),
            camera.position.x,
            camera.position.y,
            camera.position.z,
        )

        glBindVertexArray(self.sphere_vao)
        glDrawElements(GL_TRIANGLES, self.sphere_index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    def render_light_sphere(self, view, projection):
        """Render light position indicator"""
        glUseProgram(self.light_shader)

        model = glm.translate(glm.mat4(1.0), self.scene.light_pos)

        glUniformMatrix4fv(
            glGetUniformLocation(self.light_shader, "model"),
            1,
            GL_FALSE,
            glm.value_ptr(model),
        )
        glUniformMatrix4fv(
            glGetUniformLocation(self.light_shader, "view"),
            1,
            GL_FALSE,
            glm.value_ptr(view),
        )
        glUniformMatrix4fv(
            glGetUniformLocation(self.light_shader, "projection"),
            1,
            GL_FALSE,
            glm.value_ptr(projection),
        )
        glUniform3f(
            glGetUniformLocation(self.light_shader, "lightColor"),
            self.scene.light_color.x,
            self.scene.light_color.y,
            self.scene.light_color.z,
        )

        glBindVertexArray(self.light_vao)
        glDrawElements(GL_TRIANGLES, self.light_index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    def cleanup(self):
        """Clean up OpenGL resources"""
        if self.sphere_vao:
            glDeleteVertexArrays(1, [self.sphere_vao])
        if self.sphere_vbo:
            glDeleteBuffers(1, [self.sphere_vbo])
        if self.sphere_ebo:
            glDeleteBuffers(1, [self.sphere_ebo])
        if self.grid_vao:
            glDeleteVertexArrays(1, [self.grid_vao])
        if self.grid_vbo:
            glDeleteBuffers(1, [self.grid_vbo])
        if self.light_vao:
            glDeleteVertexArrays(1, [self.light_vao])
        if self.light_vbo:
            glDeleteBuffers(1, [self.light_vbo])
        if self.light_ebo:
            glDeleteBuffers(1, [self.light_ebo])
        if self.pbr_shader:
            glDeleteProgram(self.pbr_shader)
        if self.grid_shader:
            glDeleteProgram(self.grid_shader)
        if self.light_shader:
            glDeleteProgram(self.light_shader)

    # Shader sources
    @staticmethod
    def pbr_vertex_shader_source():
        return """#version 410 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;

out vec3 WorldPos;
out vec3 Normal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    WorldPos = vec3(model * vec4(aPos, 1.0));
    Normal = mat3(transpose(inverse(model))) * aNormal;
    gl_Position = projection * view * vec4(WorldPos, 1.0);
}
"""

    @staticmethod
    def pbr_fragment_shader_source():
        return """#version 410 core
out vec4 FragColor;

in vec3 WorldPos;
in vec3 Normal;

uniform vec3 albedo;
uniform float metallic;
uniform float roughness;
uniform float ao;

uniform vec3 lightPositions[1];
uniform vec3 lightColors[1];
uniform float lightConstant;
uniform float lightLinear;
uniform float lightQuadratic;

uniform vec3 camPos;

const float PI = 3.14159265359;

float DistributionGGX(vec3 N, vec3 H, float roughness)
{
    float a = roughness*roughness;
    float a2 = a*a;
    float NdotH = max(dot(N, H), 0.0);
    float NdotH2 = NdotH*NdotH;
    
    float nom   = a2;
    float denom = (NdotH2 * (a2 - 1.0) + 1.0);
    denom = PI * denom * denom;
    
    return nom / denom;
}

float GeometrySchlickGGX(float NdotV, float roughness)
{
    float r = (roughness + 1.0);
    float k = (r*r) / 8.0;
    
    float nom   = NdotV;
    float denom = NdotV * (1.0 - k) + k;
    
    return nom / denom;
}

float GeometrySmith(vec3 N, vec3 V, vec3 L, float roughness)
{
    float NdotV = max(dot(N, V), 0.0);
    float NdotL = max(dot(N, L), 0.0);
    float ggx2 = GeometrySchlickGGX(NdotV, roughness);
    float ggx1 = GeometrySchlickGGX(NdotL, roughness);
    
    return ggx1 * ggx2;
}

vec3 fresnelSchlick(float cosTheta, vec3 F0)
{
    return F0 + (1.0 - F0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}

void main()
{
    vec3 N = normalize(Normal);
    vec3 V = normalize(camPos - WorldPos);
    
    vec3 F0 = vec3(0.04);
    F0 = mix(F0, albedo, metallic);
    
    vec3 Lo = vec3(0.0);
    for(int i = 0; i < 1; ++i)
    {
        vec3 L = normalize(lightPositions[i] - WorldPos);
        vec3 H = normalize(V + L);
        float distance = length(lightPositions[i] - WorldPos);
        float attenuation = 1.0 / (lightConstant + lightLinear * distance + lightQuadratic * (distance * distance));
        vec3 radiance = lightColors[i] * attenuation;
        
        float NDF = DistributionGGX(N, H, roughness);
        float G   = GeometrySmith(N, V, L, roughness);
        vec3 F    = fresnelSchlick(max(dot(H, V), 0.0), F0);
        
        vec3 numerator    = NDF * G * F;
        float denominator = 4.0 * max(dot(N, V), 0.0) * max(dot(N, L), 0.0) + 0.0001;
        vec3 specular = numerator / denominator;
        
        vec3 kS = F;
        vec3 kD = vec3(1.0) - kS;
        kD *= 1.0 - metallic;
        
        float NdotL = max(dot(N, L), 0.0);
        Lo += (kD * albedo / PI + specular) * radiance * NdotL;
    }
    
    vec3 ambient = vec3(0.03) * albedo * ao;
    vec3 color = ambient + Lo;
    
    color = color / (color + vec3(1.0));
    color = pow(color, vec3(1.0/2.2));
    
    FragColor = vec4(color, 1.0);
}
"""

    @staticmethod
    def grid_vertex_shader_source():
        return """#version 410 core
layout (location = 0) in vec3 aPos;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    gl_Position = projection * view * model * vec4(aPos, 1.0);
}
"""

    @staticmethod
    def grid_fragment_shader_source():
        return """#version 410 core
out vec4 FragColor;

void main()
{
    FragColor = vec4(0.3, 0.3, 0.3, 1.0);
}
"""

    @staticmethod
    def light_vertex_shader_source():
        return """#version 410 core
layout (location = 0) in vec3 aPos;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    gl_Position = projection * view * model * vec4(aPos, 1.0);
}
"""

    @staticmethod
    def light_fragment_shader_source():
        return """#version 410 core
out vec4 FragColor;

uniform vec3 lightColor;

void main()
{
    FragColor = vec4(lightColor, 1.0);
}
"""
