"""
Camera class for view and projection matrices
"""
import glm


class Camera:
    def __init__(self):
        self.position = glm.vec3(0.0, 0.0, 3.0)
        self.front = glm.vec3(0.0, 0.0, -1.0)
        self.up = glm.vec3(0.0, 1.0, 0.0)
        self.right = glm.vec3(1.0, 0.0, 0.0)
        self.world_up = glm.vec3(0.0, 1.0, 0.0)
        
        # Euler angles
        self.yaw = -90.0
        self.pitch = 0.0
        
        # Options
        self.fov = 45.0
        self.aspect = 1280.0 / 720.0
        self.near = 0.1
        self.far = 100.0
        self.move_speed = 2.5
        self.mouse_sensitivity = 0.1
        
        self.update_camera_vectors()

    def get_view_matrix(self):
        """Get view matrix using GLM"""
        return glm.lookAt(self.position, self.position + self.front, self.up)

    def get_projection_matrix(self):
        """Get projection matrix using GLM"""
        return glm.perspective(glm.radians(self.fov), self.aspect, self.near, self.far)

    def set_aspect(self, aspect):
        """Set aspect ratio"""
        self.aspect = aspect

    def update_camera_vectors(self):
        """Update camera vectors based on Euler angles"""
        front = glm.vec3(0.0, 0.0, 0.0)
        front.x = glm.cos(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        front.y = glm.sin(glm.radians(self.pitch))
        front.z = glm.sin(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        
        self.front = glm.normalize(front)
        self.right = glm.normalize(glm.cross(self.front, self.world_up))
        self.up = glm.normalize(glm.cross(self.right, self.front))

    def process_mouse_movement(self, xoffset, yoffset, constrain_pitch=True):
        """Process mouse movement"""
        xoffset *= self.mouse_sensitivity
        yoffset *= self.mouse_sensitivity
        
        self.yaw += xoffset
        self.pitch += yoffset
        
        if constrain_pitch:
            if self.pitch > 89.0:
                self.pitch = 89.0
            if self.pitch < -89.0:
                self.pitch = -89.0
        
        self.update_camera_vectors()

    def process_mouse_scroll(self, yoffset):
        """Process mouse scroll for zoom"""
        self.fov -= yoffset
        if self.fov < 1.0:
            self.fov = 1.0
        if self.fov > 120.0:
            self.fov = 120.0
