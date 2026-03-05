"""
Main application class handling window, events, and main loop
"""
import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import glm
import imgui
from imgui.integrations.glfw import GlfwRenderer
import time
from app.camera import Camera
from app.renderer import Renderer
from app.scene import Scene
from app.input_handler import InputHandler


class PBRApp:
    def __init__(self):
        # Window
        self.window = None
        self.width = 1280
        self.height = 720
        self.window_title = "PBR Renderer - GLFW+GLM+PyOpenGL"
        self.should_close = False
        self.minimized = False
        
        # Components
        self.camera = None
        self.renderer = None
        self.scene = None
        self.input_handler = None
        self.imgui_impl = None
        
        # Time
        self.last_time = 0.0
        self.delta_time = 0.0
        self.fps = 0.0
        self.frame_count = 0
        self.fps_timer = 0.0

    def init(self):
        """Initialize GLFW, OpenGL, ImGui and all components"""
        if not self.init_glfw():
            return False
        
        if not self.init_opengl():
            return False
        
        if not self.init_imgui():
            return False
        
        self.init_components()
        self.setup_callbacks()
        
        # Set camera reference for input handler
        self.input_handler.set_camera(self.camera)
        
        self.last_time = time.time()
        return True

    def init_glfw(self):
        """Initialize GLFW and create window"""
        if not glfw.init():
            print("Failed to initialize GLFW")
            return False
        
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.SAMPLES, 4)
        glfw.window_hint(glfw.RESIZABLE, glfw.TRUE)
        
        self.window = glfw.create_window(
            self.width, self.height, 
            self.window_title, None, None
        )
        
        if not self.window:
            print("Failed to create GLFW window")
            glfw.terminate()
            return False
        
        glfw.make_context_current(self.window)
        glfw.swap_interval(1)
        return True

    def init_opengl(self):
        """Initialize OpenGL settings"""
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        return True

    def init_imgui(self):
        """Initialize ImGui"""
        imgui.create_context()
        self.imgui_impl = GlfwRenderer(self.window)
        imgui.style_colors_dark()
        return True

    def init_components(self):
        """Initialize application components"""
        self.camera = Camera()
        self.scene = Scene()
        self.renderer = Renderer(self.scene)
        self.input_handler = InputHandler(self.window, self.scene)
        
        # Set camera to view the scene
        self.camera.position = glm.vec3(0.0, 3.0, 5.0)
        self.camera.yaw = -90.0

    def setup_callbacks(self):
        """Setup GLFW callbacks"""
        glfw.set_framebuffer_size_callback(self.window, self.on_framebuffer_size)
        glfw.set_window_close_callback(self.window, self.on_window_close)
        glfw.set_window_iconify_callback(self.window, self.on_window_iconify)
        glfw.set_key_callback(self.window, self.on_key)

    def on_framebuffer_size(self, window, width, height):
        """Handle window resize"""
        self.width = width
        self.height = height
        glViewport(0, 0, width, height)
        self.camera.set_aspect(width / height if height > 0 else 1.0)

    def on_window_close(self, window):
        """Handle window close request"""
        self.should_close = True

    def on_window_iconify(self, window, iconified):
        """Handle window minimize/restore"""
        self.minimized = iconified

    def on_key(self, window, key, scancode, action, mods):
        """Handle key input"""
        self.input_handler.handle_key(key, scancode, action, mods)

    def update(self):
        """Update application state"""
        current_time = time.time()
        self.delta_time = current_time - self.last_time
        self.last_time = current_time
        
        # FPS calculation
        self.frame_count += 1
        self.fps_timer += self.delta_time
        if self.fps_timer >= 1.0:
            self.fps = self.frame_count / self.fps_timer
            self.frame_count = 0
            self.fps_timer = 0.0
        
        # Update input
        self.input_handler.update(self.delta_time)
        
        # Update ImGui
        self.imgui_impl.process_inputs()

    def render(self):
        """Render the scene"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Render 3D scene
        self.renderer.render(self.camera)
        
        # Render UI
        self.render_ui()
        
        glfw.swap_buffers(self.window)

    def render_ui(self):
        """Render ImGui UI"""
        imgui.new_frame()
        
        # Main menu bar
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File"):
                if imgui.menu_item("Exit", "Esc")[0]:
                    self.should_close = True
                imgui.end_menu()
            imgui.end_main_menu_bar()
        
        # Control panel
        self.render_control_panel()
        
        imgui.render()
        self.imgui_impl.render(imgui.get_draw_data())

    def render_control_panel(self):
        """Render control panel UI"""
        imgui.set_next_window_size(350, 500, imgui.FIRST_USE_EVER)
        imgui.set_next_window_position(10, 30, imgui.FIRST_USE_EVER)

        imgui.begin("PBR Control Panel", True)
        
        # FPS display
        imgui.text(f"FPS: {self.fps:.1f}")
        imgui.separator()
        
        # Sphere controls
        if imgui.collapsing_header("Sphere Position", True):
            pos = [self.scene.sphere_pos.x, self.scene.sphere_pos.y, self.scene.sphere_pos.z]
            changed, pos = imgui.slider_float3("Position", pos[0], pos[1], pos[2], -10.0, 10.0)
            if changed:
                self.scene.sphere_pos = glm.vec3(pos[0], pos[1], pos[2])

        if imgui.collapsing_header("PBR Material", True):
            albedo = [self.scene.albedo.x, self.scene.albedo.y, self.scene.albedo.z]
            changed, albedo = imgui.color_edit3("Albedo", albedo[0], albedo[1], albedo[2])
            if changed:
                self.scene.albedo = glm.vec3(albedo[0], albedo[1], albedo[2])

            changed, self.scene.metallic = imgui.slider_float("Metallic", self.scene.metallic, 0.0, 1.0)
            changed, self.scene.roughness = imgui.slider_float("Roughness", self.scene.roughness, 0.01, 1.0)
            changed, self.scene.ao = imgui.slider_float("AO", self.scene.ao, 0.0, 1.0)

        # Light controls
        if imgui.collapsing_header("Light", True):
            light_pos = [self.scene.light_pos.x, self.scene.light_pos.y, self.scene.light_pos.z]
            changed, light_pos = imgui.slider_float3("Position", light_pos[0], light_pos[1], light_pos[2], -10.0, 10.0)
            if changed:
                self.scene.light_pos = glm.vec3(light_pos[0], light_pos[1], light_pos[2])

            light_color = [self.scene.light_color.x, self.scene.light_color.y, self.scene.light_color.z]
            changed, light_color = imgui.color_edit3("Color", light_color[0], light_color[1], light_color[2])
            if changed:
                self.scene.light_color = glm.vec3(light_color[0], light_color[1], light_color[2])

            changed, self.scene.light_intensity = imgui.slider_float("Intensity", self.scene.light_intensity, 0.0, 50.0)
            
            imgui.text("Attenuation")
            _, self.scene.light_attenuation_const = imgui.slider_float("Constant", self.scene.light_attenuation_const, 0.0, 2.0)
            _, self.scene.light_attenuation_linear = imgui.slider_float("Linear", self.scene.light_attenuation_linear, 0.0, 1.0)
            _, self.scene.light_attenuation_quad = imgui.slider_float("Quadratic", self.scene.light_attenuation_quad, 0.0, 1.0)
        
        # Camera controls
        if imgui.collapsing_header("Camera", True):
            cam_pos = [self.camera.position.x, self.camera.position.y, self.camera.position.z]
            imgui.text(f"Position: {cam_pos[0]:.2f}, {cam_pos[1]:.2f}, {cam_pos[2]:.2f}")
            
            _, self.camera.fov = imgui.slider_float("FOV", self.camera.fov, 30.0, 120.0)
            _, self.camera.move_speed = imgui.slider_float("Speed", self.camera.move_speed, 0.5, 10.0)
        
        # Instructions
        imgui.separator()
        imgui.text("Controls:")
        imgui.bullet_text("W/S - Move sphere forward/backward")
        imgui.bullet_text("A/D - Move sphere left/right")
        imgui.bullet_text("Q/E - Move sphere up/down")
        imgui.bullet_text("Mouse drag - Rotate camera")
        imgui.bullet_text("Scroll - Zoom")
        
        imgui.end()

    def run(self):
        """Main application loop"""
        while not glfw.window_should_close(self.window) and not self.should_close:
            self.update()

            if not self.minimized:
                self.render()

            glfw.poll_events()

    def cleanup(self):
        """Clean up resources"""
        if self.renderer:
            self.renderer.cleanup()
        if self.imgui_impl:
            self.imgui_impl.shutdown()
        glfw.terminate()
