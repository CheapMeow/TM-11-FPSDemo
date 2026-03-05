"""
Server entry point - authoritative server with network delay simulation
"""
import socket
import threading
import time
import glm
import random
from app.player import Player
from app.network_protocol import (
    MessageTypes,
    pack_move_confirm,
    pack_state_broadcast,
    pack_initial_state,
    pack_player_joined,
    pack_player_left,
    receive_message
)
import imgui
from imgui.integrations.glfw import GlfwRenderer
import glfw
from OpenGL.GL import *


class ServerApp:
    def __init__(self, host='127.0.0.1', port=19999):
        self.host = host
        self.port = port
        self.socket = None
        self.clients = {}
        self.players = {}
        self.running = False
        
        self.next_player_id = 1
        
        # Server UI settings
        self.move_speed = 5.0
        self.client_delay = 0.05  # 50ms simulated delay
        self.process_delay = 0.02  # 20ms process delay
        self.send_delay = 0.03     # 30ms send delay
        self.show_server_ui = True
        
        # ImGui
        self.window = None
        self.imgui_impl = None
        
        # Light position for rendering (UI only)
        self.light_pos = glm.vec3(3.0, 4.0, 3.0)
        self.light_color = glm.vec3(1.0, 1.0, 1.0)
    
    def check_port_available(self):
        """Check if port is available"""
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_socket.bind((self.host, self.port))
            test_socket.close()
            return True
        except:
            return False
    
    def init_ui(self):
        """Initialize minimal UI for server"""
        if not glfw.init():
            print("Failed to initialize GLFW")
            return False
        
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
        
        self.window = glfw.create_window(400, 600, "Server UI", None, None)
        if not self.window:
            glfw.terminate()
            return False
        
        glfw.make_context_current(self.window)
        
        imgui.create_context()
        self.imgui_impl = GlfwRenderer(self.window)
        imgui.style_colors_dark()
        
        glClearColor(0.1, 0.1, 0.1, 1.0)
        
        return True
    
    def start(self):
        """Start server"""
        # Check if port is already in use
        if not self.check_port_available():
            print(f"Port {self.port} is already in use. Server may already be running.")
            return False
        
        # Create server socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(10)
        self.socket.settimeout(0.1)  # Non-blocking
        
        self.running = True
        print(f"Server started on {self.host}:{self.port}")
        
        # Initialize UI (must be on main thread)
        if not self.init_ui():
            print("Failed to initialize server UI")
            return False
        
        # Start accept thread
        accept_thread = threading.Thread(target=self.accept_clients)
        accept_thread.daemon = True
        accept_thread.start()
        
        # Run UI in main thread (OpenGL context must be in main thread)
        return True
    
    def accept_clients(self):
        """Accept client connections"""
        while self.running:
            try:
                client_socket, addr = self.socket.accept()
                print(f"New connection from {addr}")
                
                # Start client handler thread
                handler_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, addr)
                )
                handler_thread.daemon = True
                handler_thread.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error accepting client: {e}")
                break
    
    def handle_client(self, client_socket, addr):
        """Handle client communication"""
        player_id = None
        
        try:
            # Send initial state after join request
            while self.running:
                message = receive_message(client_socket)
                if not message:
                    break
                
                msg_type = message.get('type')
                
                if msg_type == MessageTypes.JOIN_REQUEST:
                    # Use the player_id from the client's join request
                    player_id = message.get('player_id')
                    
                    player = Player(
                        player_id=player_id,
                        move_speed=self.move_speed
                    )
                    self.players[player_id] = player
                    self.clients[player_id] = client_socket
                    
                    print(f"Player {player_id} joined from {addr}")
                    print(f"Player created at position: {player.position}")
                    
                    # Simulate delay
                    time.sleep(self.client_delay)
                    time.sleep(self.process_delay)
                    
                    # Send initial state to new client
                    initial_state = pack_initial_state(list(self.players.values()))
                    print(f"Sending initial state with {len(self.players)} players")
                    client_socket.sendall(initial_state)
                    print(f"Initial state sent successfully")
                    
                    # Broadcast new player to existing clients
                    player_joined = pack_player_joined(player)
                    for pid, sock in self.clients.items():
                        if pid != player_id:
                            try:
                                sock.sendall(player_joined)
                            except:
                                pass
                    
                    time.sleep(self.send_delay)
                
                elif msg_type == MessageTypes.MOVE_REQUEST:
                    player_id = message.get('player_id')
                    dx = message.get('dx', 0)
                    dy = message.get('dy', 0)
                    dz = message.get('dz', 0)
                    
                    if player_id in self.players:
                        player = self.players[player_id]
                        
                        # Update position on server (authoritative)
                        player.position.x += dx
                        player.position.y += dy
                        player.position.z += dz
                        
                        # Simulate delays
                        time.sleep(self.client_delay)
                        time.sleep(self.process_delay)
                        
                        # Send confirmation to requesting client
                        confirm = pack_move_confirm(player_id, player.position)
                        try:
                            client_socket.sendall(confirm)
                        except:
                            break
                        
                        # Broadcast to other clients
                        broadcast = pack_state_broadcast(player_id, player.position)
                        for pid, sock in self.clients.items():
                            if pid != player_id:
                                try:
                                    sock.sendall(broadcast)
                                except:
                                    pass
                        
                        time.sleep(self.send_delay)
                
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            # Clean up
            if player_id and player_id in self.players:
                del self.players[player_id]
            if player_id and player_id in self.clients:
                del self.clients[player_id]
            
            # Broadcast player left
            if player_id:
                player_left = pack_player_left(player_id)
                for pid, sock in self.clients.items():
                    try:
                        sock.sendall(player_left)
                    except:
                        pass
            
            client_socket.close()
            print(f"Player {player_id} disconnected")
    
    def run_ui(self):
        """Run server UI"""
        while self.running and not glfw.window_should_close(self.window):
            glfw.poll_events()
            self.imgui_impl.process_inputs()
            
            glClear(GL_COLOR_BUFFER_BIT)
            imgui.new_frame()
            
            self.render_ui()
            
            imgui.render()
            self.imgui_impl.render(imgui.get_draw_data())
            
            glfw.swap_buffers(self.window)
    
    def render_ui(self):
        """Render server control UI"""
        imgui.set_next_window_size(380, 550)
        imgui.set_next_window_position(10, 10)
        
        imgui.begin("Server Control Panel", True)
        
        imgui.text(f"Server: {self.host}:{self.port}")
        imgui.text(f"Connected Clients: {len(self.clients)}")
        imgui.text(f"Total Players: {len(self.players)}")
        imgui.separator()
        
        # Delay settings
        if imgui.collapsing_header("Network Delay Simulation"):
            _, self.client_delay = imgui.slider_float("Client Delay (ms)", self.client_delay * 1000, 0, 200)
            self.client_delay /= 1000.0
            _, self.process_delay = imgui.slider_float("Process Delay (ms)", self.process_delay * 1000, 0, 100)
            self.process_delay /= 1000.0
            _, self.send_delay = imgui.slider_float("Send Delay (ms)", self.send_delay * 1000, 0, 100)
            self.send_delay /= 1000.0
        
        # Game settings
        if imgui.collapsing_header("Game Settings"):
            _, self.move_speed = imgui.slider_float("Move Speed", self.move_speed, 1.0, 20.0)
            
            # Update all players' speed
            for player in self.players.values():
                player.move_speed = self.move_speed
        
        # Player list
        if imgui.collapsing_header("Players"):
            for pid, player in self.players.items():
                if imgui.tree_node(f"Player {pid}"):
                    pos = player.position
                    imgui.text(f"Position: ({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})")
                    color = player.color
                    imgui.text(f"Color: ({color.x:.2f}, {color.y:.2f}, {color.z:.2f})")
                    imgui.tree_pop()
        
        imgui.separator()
        imgui.text("Press close button to stop server")
        
        imgui.end()
    
    def stop(self):
        """Stop server"""
        self.running = False
        if self.socket:
            self.socket.close()
        print("Server stopped")


def main():
    server = ServerApp()
    if server.start():
        try:
            # Run UI loop in main thread (OpenGL context requirement)
            server.run_ui()
        except KeyboardInterrupt:
            pass
        finally:
            server.stop()


if __name__ == "__main__":
    main()
