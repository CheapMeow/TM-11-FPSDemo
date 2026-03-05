"""
Sphere Renderer: handles sphere rendering for multiple characters
"""
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import glm


class SphereRenderer:
    def __init__(self, segments=64, rings=64):
        self.segments = segments
        self.rings = rings
        
        # VAO and VBO for sphere geometry (shared by all spheres)
        self.vao = None
        self.vbo = None
        self.ebo = None
        self.index_count = 0
        self.normal_vbo = None
        
        # Shader
        self.shader = None
        
        self.init_shader()
        self.init_geometry()
    
    def init_shader(self):
        """Initialize sphere shader"""
        vs = self.vertex_shader_source()
        fs = self.fragment_shader_source()
        self.shader = compileProgram(
            compileShader(vs, GL_VERTEX_SHADER),
            compileShader(fs, GL_FRAGMENT_SHADER),
        )
    
    def init_geometry(self):
        """Create sphere geometry"""
        positions = []
        normals = []
        indices = []
        radius = 1.0
        
        # Generate vertices
        for r in range(self.rings + 1):
            phi = glm.pi() * r / self.rings
            y = glm.cos(phi) * radius
            ring_radius = glm.sin(phi) * radius
            
            for s in range(self.segments + 1):
                theta = 2 * glm.pi() * s / self.segments
                x = ring_radius * glm.cos(theta)
                z = ring_radius * glm.sin(theta)
                
                positions.extend([x, y, z])
                
                norm = glm.normalize(glm.vec3(x, y, z))
                normals.extend([norm.x, norm.y, norm.z])
        
        # Generate indices
        for r in range(self.rings):
            for s in range(self.segments):
                i0 = r * (self.segments + 1) + s
                i1 = r * (self.segments + 1) + s + 1
                i2 = (r + 1) * (self.segments + 1) + s
                i3 = (r + 1) * (self.segments + 1) + s + 1
                
                indices.extend([i0, i2, i1])
                indices.extend([i1, i2, i3])
        
        self.index_count = len(indices)
        
        # Create VAO
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        # Position VBO
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(
            GL_ARRAY_BUFFER,
            len(positions) * 4,
            np.array(positions, dtype=np.float32),
            GL_STATIC_DRAW,
        )
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        
        # Normal VBO
        self.normal_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.normal_vbo)
        glBufferData(
            GL_ARRAY_BUFFER,
            len(normals) * 4,
            np.array(normals, dtype=np.float32),
            GL_STATIC_DRAW,
        )
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)
        
        # EBO
        self.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(
            GL_ELEMENT_ARRAY_BUFFER,
            len(indices) * 4,
            np.array(indices, dtype=np.uint32),
            GL_STATIC_DRAW,
        )
        
        glBindVertexArray(0)
    
    def render(self, position, radius, color, view, projection, light_pos=None, light_color=None, camera_pos=None):
        """Render a single sphere"""
        glUseProgram(self.shader)
        
        # Model matrix
        model = glm.translate(glm.mat4(1.0), position)
        model = glm.scale(model, glm.vec3(radius, radius, radius))
        
        # Set uniforms
        glUniformMatrix4fv(
            glGetUniformLocation(self.shader, "model"),
            1,
            GL_FALSE,
            glm.value_ptr(model),
        )
        glUniformMatrix4fv(
            glGetUniformLocation(self.shader, "view"),
            1,
            GL_FALSE,
            glm.value_ptr(view),
        )
        glUniformMatrix4fv(
            glGetUniformLocation(self.shader, "projection"),
            1,
            GL_FALSE,
            glm.value_ptr(projection),
        )
        
        glUniform3f(
            glGetUniformLocation(self.shader, "albedo"),
            color.x, color.y, color.z
        )
        
        # Light uniforms
        if light_pos is None:
            light_pos = glm.vec3(3.0, 4.0, 3.0)
        if light_color is None:
            light_color = glm.vec3(1.0, 1.0, 1.0)
        
        glUniform3f(
            glGetUniformLocation(self.shader, "lightPositions[0]"),
            light_pos.x, light_pos.y, light_pos.z
        )
        glUniform3f(
            glGetUniformLocation(self.shader, "lightColors[0]"),
            light_color.x * 10.0, light_color.y * 10.0, light_color.z * 10.0
        )
        
        # Camera position
        if camera_pos is None:
            camera_pos = glm.vec3(0.0, 5.0, 10.0)
        
        glUniform3f(
            glGetUniformLocation(self.shader, "camPos"),
            camera_pos.x, camera_pos.y, camera_pos.z
        )
        
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
    
    def cleanup(self):
        """Clean up OpenGL resources"""
        if self.vao:
            glDeleteVertexArrays(1, [self.vao])
        if self.vbo:
            glDeleteBuffers(1, [self.vbo])
        if self.ebo:
            glDeleteBuffers(1, [self.ebo])
        if self.normal_vbo:
            glDeleteBuffers(1, [self.normal_vbo])
        if self.shader:
            glDeleteProgram(self.shader)
    
    @staticmethod
    def vertex_shader_source():
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
    def fragment_shader_source():
        return """#version 410 core
out vec4 FragColor;

in vec3 WorldPos;
in vec3 Normal;

uniform vec3 albedo;

uniform vec3 lightPositions[1];
uniform vec3 lightColors[1];

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
    
    float metallic = 0.3;
    float roughness = 0.5;
    float ao = 1.0;
    
    vec3 F0 = vec3(0.04);
    F0 = mix(F0, albedo, metallic);
    
    vec3 Lo = vec3(0.0);
    for(int i = 0; i < 1; ++i)
    {
        vec3 L = normalize(lightPositions[i] - WorldPos);
        vec3 H = normalize(V + L);
        float distance = length(lightPositions[i] - WorldPos);
        float attenuation = 1.0 / (1.0 + 0.09 * distance + 0.032 * (distance * distance));
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
