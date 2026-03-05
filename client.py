"""
Client entry point - renders and controls character
"""
import socket
import threading
import time
import glfw
from OpenGL.GL import *
import glm
import imgui
from imgui.integrations.glfw import GlfwRenderer
import random

from app.camera import Camera
from app.player import Player
from app.sphere_renderer import SphereRenderer
from app.grid_renderer import GridRenderer
from app.network_protocol import (
    MessageTypes,
    pack_move_request,
    pack_join_request,
    receive_message
)


class ClientApp:
    def __init__(self, server_host='127.0.0.1', server_port=19999):
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
        self.connected = False
        self.running = False
        
        # Window
        self.window = None
        self.width = 1280
        self.height = 720
        self.window_title = "FPS Demo Client"
        self.should_close = False
        self.window_focused = False
        
        # Components
        self.camera = None
        self.sphere_renderer = None
        self.grid_renderer = None
        self.imgui_impl = None
        
        # Local players (dictionary of player_id -> Player)
        self.players = {}
        self.local_player_id = None
        
        # Light for rendering
        self.light_pos = glm.vec3(3.0, 4.0, 3.0)
        self.light_color = glm.vec3(1.0, 1.0, 1.0)
        self.light_intensity = 10.0
        
        # Pending movement
        self.move_direction = glm.vec3(0.0, 0.0, 0.0)
        self.can_move = True
        
        # Time
        self.last_time = 0.0
        self.delta_time = 0.0
        self.fps = 0.0
        self.frame_count = 0
        self.fps_timer = 0.0
        
        # Mouse state
        self.mouse_last_x = 0.0
        self.mouse_last_y = 0.0
        self.mouse_first = True
    
    def check_server_available(self):
        """Check if server is available"""
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(1.0)
            test_socket.connect((self.server_host, self.server_port))
            test_socket.close()
            return True
        except:
            return False
    
    def connect_to_server(self):
        """Connect to server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            
            # Send join request
            import uuid
            self.local_player_id = int(uuid.uuid4().int % 1000000)
            join_request = pack_join_request(self.local_player_id)
            self.socket.sendall(join_request)
            
            self.connected = True
            print(f"Connected to server as player {self.local_player_id}")
            
            # Start network receive thread
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            return True
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            return False
    
    def init(self):
        """Initialize client"""
        if not self.init_glfw():
            return False
        
        if not self.init_opengl():
            return False
        
        if not self.init_imgui():
            return False
        
        self.init_components()
        self.setup_callbacks()
        
        self.last_time = time.time()
        return True
    
    def init_glfw(self):
        """Initialize GLFW"""
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
        """Initialize OpenGL"""
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.1, 0.1, 0.15, 1.0)
        return True
    
    def init_imgui(self):
        """Initialize ImGui"""
        imgui.create_context()
        self.imgui_impl = GlfwRenderer(self.window)
        imgui.style_colors_dark()
        return True
    
    def init_components(self):
        """Initialize components"""
        self.camera = Camera()
        self.sphere_renderer = SphereRenderer()
        self.grid_renderer = GridRenderer()
        
        # Position camera to see the scene
        self.camera.position = glm.vec3(0.0, 5.0, 10.0)
        self.camera.yaw = -90.0
        self.camera.pitch = -30.0
        self.camera.update_camera_vectors()
    
    def setup_callbacks(self):
        """Setup callbacks"""
        glfw.set_framebuffer_size_callback(self.window, self.on_framebuffer_size)
        glfw.set_window_close_callback(self.window, self.on_window_close)
        glfw.set_window_focus_callback(self.window, self.on_window_focus)
        glfw.set_key_callback(self.window, self.on_key)
        glfw.set_cursor_pos_callback(self.window, self.on_cursor_pos)
    
    def on_framebuffer_size(self, window, width, height):
        """Handle resize"""
        self.width = width
        self.height = height
        glViewport(0, 0, width, height)
        self.camera.set_aspect(width / height if height > 0 else 1.0)
    
    def on_window_close(self, window):
        """Handle close"""
        self.should_close = True
    
    def on_window_focus(self, window, focused):
        """Handle focus change"""
        self.window_focused = focused
    
    def on_key(self, window, key, scancode, action, mods):
        """Handle key press"""
        pass
    
    def on_cursor_pos(self, window, x, y):
        """Handle mouse movement"""
        if self.mouse_first:
            self.mouse_last_x = x
            self.mouse_last_y = y
            self.mouse_first = False
        
        xoffset = x - self.mouse_last_x
        yoffset = self.mouse_last_y - y
        
        self.mouse_last_x = x
        self.mouse_last_y = y
        
        # Rotate camera with mouse drag
        if glfw.get_mouse_button(self.window, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS:
            self.camera.process_mouse_movement(xoffset, yoffset)
    
    def receive_messages(self):
        """Receive messages from server"""
        print(f"Receive thread started, connected={self.connected}, running={self.running}")
        while self.connected and self.running:
            try:
                message = receive_message(self.socket)
                if not message:
                    print("Received empty message, breaking")
                    break
                
                msg_type = message.get('type')
                print(f"Received message type: {msg_type}")
                
                if msg_type == MessageTypes.INITIAL_STATE:
                    # Load initial state
                    players_data = message.get('players', [])
                    print(f"Initial state contains {len(players_data)} players")
                    for p_data in players_data:
                        player = Player.from_dict(p_data)
                        self.players[player.id] = player
                        print(f"Added player {player.id} at position {player.position}")
                    print(f"Received initial state with {len(self.players)} players")
                
                elif msg_type == MessageTypes.MOVE_CONFIRM:
                    # Receive confirmation for our movement
                    player_id = message.get('player_id')
                    pos = message.get('position')
                    if player_id == self.local_player_id:
                        self.can_move = True
                        if player_id in self.players:
                            self.players[player_id].set_position(glm.vec3(*pos))
                
                elif msg_type == MessageTypes.STATE_BROADCAST:
                    # Receive position update for other player
                    player_id = message.get('player_id')
                    pos = message.get('position')
                    if player_id in self.players:
                        self.players[player_id].set_position(glm.vec3(*pos))
                
                elif msg_type == MessageTypes.PLAYER_JOINED:
                    # New player joined
                    player_data = message.get('player')
                    player = Player.from_dict(player_data)
                    self.players[player.id] = player
                    print(f"Player {player.id} joined")
                
                elif msg_type == MessageTypes.PLAYER_LEFT:
                    # Player left
                    player_id = message.get('player_id')
                    if player_id in self.players:
                        del self.players[player_id]
                        print(f"Player {player_id} left")
                
            except Exception as e:
                if self.connected:
                    print(f"Error receiving message: {e}")
                break
        
        self.connected = False
    
    def update(self):
        """Update client state"""
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
        
        # Check for input only if window is focused and connected
        if self.window_focused and self.connected and self.can_move and self.local_player_id in self.players:
            player = self.players[self.local_player_id]
            
            # Calculate move direction
            move_vec = glm.vec3(0.0, 0.0, 0.0)
            if glfw.get_key(self.window, glfw.KEY_W) == glfw.PRESS:
                move_vec.z -= 1.0
            if glfw.get_key(self.window, glfw.KEY_S) == glfw.PRESS:
                move_vec.z += 1.0
            if glfw.get_key(self.window, glfw.KEY_A) == glfw.PRESS:
                move_vec.x -= 1.0
            if glfw.get_key(self.window, glfw.KEY_D) == glfw.PRESS:
                move_vec.x += 1.0
            if glfw.get_key(self.window, glfw.KEY_Q) == glfw.PRESS:
                move_vec.y -= 1.0
            if glfw.get_key(self.window, glfw.KEY_E) == glfw.PRESS:
                move_vec.y += 1.0
            
            if glm.length(move_vec) > 0:
                move_vec = glm.normalize(move_vec)
                distance = player.move_speed * self.delta_time
                dx = move_vec.x * distance
                dy = move_vec.y * distance
                dz = move_vec.z * distance
                
                # Send movement request to server
                move_request = pack_move_request(self.local_player_id, dx, dy, dz)
                try:
                    self.socket.sendall(move_request)
                    self.can_move = False  # Wait for confirmation
                except:
                    pass
        
        # Update ImGui
        self.imgui_impl.process_inputs()
    
    def render(self):
        """Render scene"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        view = self.camera.get_view_matrix()
        projection = self.camera.get_projection_matrix()
        
        # Render grid
        self.grid_renderer.render(view, projection)
        
        # Render all players
        for player in self.players.values():
            self.sphere_renderer.render(
                player.position,
                player.radius,
                player.color,
                view,
                projection,
                self.light_pos,
                self.light_color,
                self.camera.position
            )
        
        # Render UI
        self.render_ui()
        
        glfw.swap_buffers(self.window)
    
    def render_ui(self):
        """Render UI"""
        imgui.new_frame()
        
        # Info panel
        imgui.set_next_window_size(300, 200)
        imgui.set_next_window_position(10, 10)
        
        imgui.begin("Client Info", True)
        imgui.text(f"FPS: {self.fps:.1f}")
        imgui.text(f"Connected: {'Yes' if self.connected else 'No'}")
        imgui.text(f"Local Player ID: {self.local_player_id}")
        imgui.text(f"Total Players: {len(self.players)}")
        imgui.text(f"Window Focused: {'Yes' if self.window_focused else 'No'}")
        imgui.separator()
        imgui.text("Controls (when focused):")
        imgui.bullet_text("W/S - Move forward/backward")
        imgui.bullet_text("A/D - Move left/right")
        imgui.bullet_text("Q/E - Move up/down")
        imgui.bullet_text("Mouse drag - Rotate camera")
        
        # Player positions (read-only)
        if imgui.collapsing_header("Player Positions"):
            for pid, player in self.players.items():
                is_local = pid == self.local_player_id
                pos = player.position
                imgui.text(f"Player {pid} {'(You)' if is_local else ''}")
                imgui.same_line()
                imgui.text(f"  ({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})")
        
        imgui.end()
        imgui.render()
        self.imgui_impl.render(imgui.get_draw_data())
    
    def run(self):
        """Run client loop"""
        self.running = True
        while not glfw.window_should_close(self.window) and not self.should_close:
            self.update()
            self.render()
            glfw.poll_events()
    
    def cleanup(self):
        """Clean up"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.sphere_renderer:
            self.sphere_renderer.cleanup()
        if self.grid_renderer:
            self.grid_renderer.cleanup()
        if self.imgui_impl:
            self.imgui_impl.shutdown()
        glfw.terminate()


def wait_for_server():
    """Wait for server to be available"""
    client = ClientApp()
    
    print("Waiting for server...")
    while True:
        try:
            if client.check_server_available():
                print("Server found!")
                return client
        except KeyboardInterrupt:
            print("Interrupted")
            return None
        
        time.sleep(1.0)


def main():
    # Wait for server
    client = wait_for_server()
    if client is None:
        return
    
    # Initialize and connect
    if not client.init():
        print("Failed to initialize client")
        return
    
    if not client.connect_to_server():
        print("Failed to connect to server")
        client.cleanup()
        return
    
    # Run client
    try:
        client.run()
    except KeyboardInterrupt:
        pass
    finally:
        client.cleanup()


if __name__ == "__main__":
    main()
