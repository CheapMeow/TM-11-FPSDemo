"""
Scene data: sphere, light, PBR material parameters
"""
import glm


class Scene:
    def __init__(self):
        # Sphere (controllable object)
        self.sphere_pos = glm.vec3(0.0, 1.0, 0.0)
        self.sphere_radius = 1.0
        self.sphere_segments = 64
        self.sphere_rings = 64
        
        # Light
        self.light_pos = glm.vec3(3.0, 4.0, 3.0)
        self.light_color = glm.vec3(1.0, 1.0, 1.0)
        self.light_intensity = 10.0
        self.light_attenuation_const = 1.0
        self.light_attenuation_linear = 0.09
        self.light_attenuation_quad = 0.032
        
        # PBR Material
        self.albedo = glm.vec3(0.8, 0.2, 0.2)
        self.metallic = 0.5
        self.roughness = 0.5
        self.ao = 1.0
        
        # Grid
        self.grid_size = 20
        self.grid_spacing = 1.0
        
        # Light sphere size
        self.light_radius = 0.2

    def move_sphere(self, dx, dy, dz):
        """Move the sphere by the given delta"""
        self.sphere_pos.x += dx
        self.sphere_pos.y += dy
        self.sphere_pos.z += dz
