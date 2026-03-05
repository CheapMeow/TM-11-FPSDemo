"""
Input handling for keyboard and mouse
"""

import glfw
import glm
from OpenGL.GL import *
from app.camera import Camera
from app.scene import Scene


class InputHandler:
    def __init__(self, window, scene):
        self.window = window
        self.scene = scene

        # Mouse state
        self.mouse_last_x = 0.0
        self.mouse_last_y = 0.0
        self.mouse_first = True
        self.mouse_dragging = False
        self.mouse_button_state = [False, False, False]

        # Camera reference (will be set externally)
        self.camera = None

    def set_camera(self, camera):
        """Set camera reference"""
        self.camera = camera

    def handle_key(self, key, scancode, action, mods):
        """Handle keyboard input"""
        pass

    def update(self, delta_time):
        """Update input state"""
        # Check if any mouse button is pressed
        if glfw.get_mouse_button(self.window, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS:
            self.mouse_button_state[0] = True
        else:
            self.mouse_button_state[0] = False

        if glfw.get_mouse_button(self.window, glfw.MOUSE_BUTTON_RIGHT) == glfw.PRESS:
            self.mouse_button_state[1] = True
        else:
            self.mouse_button_state[1] = False

        # Handle sphere movement
        move_speed = self.scene.sphere_radius * 3.0  # Scale speed by sphere size
        if glfw.get_key(self.window, glfw.KEY_W) == glfw.PRESS:
            self.scene.move_sphere(0.0, 0.0, -move_speed * delta_time)
        if glfw.get_key(self.window, glfw.KEY_S) == glfw.PRESS:
            self.scene.move_sphere(0.0, 0.0, move_speed * delta_time)
        if glfw.get_key(self.window, glfw.KEY_A) == glfw.PRESS:
            self.scene.move_sphere(-move_speed * delta_time, 0.0, 0.0)
        if glfw.get_key(self.window, glfw.KEY_D) == glfw.PRESS:
            self.scene.move_sphere(move_speed * delta_time, 0.0, 0.0)
        if glfw.get_key(self.window, glfw.KEY_Q) == glfw.PRESS:
            self.scene.move_sphere(0.0, -move_speed * delta_time, 0.0)
        if glfw.get_key(self.window, glfw.KEY_E) == glfw.PRESS:
            self.scene.move_sphere(0.0, move_speed * delta_time, 0.0)

        # Handle camera rotation with mouse drag
        if self.camera:
            mouse_x, mouse_y = glfw.get_cursor_pos(self.window)

            if self.mouse_first:
                self.mouse_last_x = mouse_x
                self.mouse_last_y = mouse_y
                self.mouse_first = False

            xoffset = mouse_x - self.mouse_last_x
            yoffset = (
                self.mouse_last_y - mouse_y
            )  # Reversed since y-coordinates go from bottom to top

            self.mouse_last_x = mouse_x
            self.mouse_last_y = mouse_y

            # Rotate camera when mouse button is pressed
            if self.mouse_button_state[0] or self.mouse_button_state[1]:
                self.camera.process_mouse_movement(xoffset, yoffset)
