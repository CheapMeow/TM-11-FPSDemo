"""
Grid Renderer for ground plane
"""
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import glm

class GridRenderer:
    def __init__(self, size=20, spacing=1.0):
        self.size = size
        self.spacing = spacing
        self.vao = None
        self.vbo = None
        self.vertex_count = 0
        self.shader = None
        
        self.init_shader()
        self.init_geometry()
    
    def init_shader(self):
        """Initialize grid shader"""
        vs = self.vertex_shader_source()
        fs = self.fragment_shader_source()
        self.shader = compileProgram(
            compileShader(vs, GL_VERTEX_SHADER),
            compileShader(fs, GL_FRAGMENT_SHADER),
        )
    
    def init_geometry(self):
        """Create grid geometry"""
        positions = []
        
        # Create horizontal lines
        for i in range(-self.size, self.size + 1):
            x = i * self.spacing
            positions.extend([x, 0.0, -self.size * self.spacing])
            positions.extend([x, 0.0, self.size * self.spacing])
        
        # Create vertical lines
        for i in range(-self.size, self.size + 1):
            z = i * self.spacing
            positions.extend([-self.size * self.spacing, 0.0, z])
            positions.extend([self.size * self.spacing, 0.0, z])
        
        self.vertex_count = len(positions) // 3
        
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
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
        
        glBindVertexArray(0)
    
    def render(self, view, projection):
        """Render grid"""
        glUseProgram(self.shader)
        
        model = glm.mat4(1.0)
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
        
        glBindVertexArray(self.vao)
        glDrawArrays(GL_LINES, 0, self.vertex_count)
        glBindVertexArray(0)
    
    def cleanup(self):
        """Clean up OpenGL resources"""
        if self.vao:
            glDeleteVertexArrays(1, [self.vao])
        if self.vbo:
            glDeleteBuffers(1, [self.vbo])
        if self.shader:
            glDeleteProgram(self.shader)
    
    @staticmethod
    def vertex_shader_source():
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
    def fragment_shader_source():
        return """#version 410 core
out vec4 FragColor;

void main()
{
    FragColor = vec4(0.3, 0.3, 0.3, 1.0);
}
"""
