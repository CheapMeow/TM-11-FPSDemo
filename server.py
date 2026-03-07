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
    pack_delay_update,
    pack_move_speed_update,
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
        self.clients = {}  # player_id -> socket
        self.players = {}  # player_id -> Player
        self.client_delays = {}  # player_id -> delay in seconds
        self.running = False
        
        self.next_player_id = 1
        
        # Server UI settings
        self.move_speed = 5.0
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
                    # Set default delay for new client (50ms)
                    self.client_delays[player_id] = 0.05
                    
                    print(f"Player {player_id} joined from {addr}")
                    print(f"Player created at position: {player.position}")
                    
                    # Simulate delay for this client
                    time.sleep(self.client_delays[player_id])
                    
                    # Send initial state to new client
                    initial_state = pack_initial_state(list(self.players.values()))
                    print(f"Sending initial state with {len(self.players)} players")
                    client_socket.sendall(initial_state)
                    print(f"Initial state sent successfully")
                    
                    # Broadcast new player to existing clients
                    player_joined = pack_player_joined(player)
                    for pid, sock in self.clients.items():
                        if pid != player_id:
                            # Simulate delay for each target client
                            time.sleep(self.client_delays[pid])
                            try:
                                sock.sendall(player_joined)
                            except:
                                pass
                
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
                        
                        # Simulate delay from client to server
                        time.sleep(self.client_delays[player_id])
                        
                        # Send confirmation to requesting client
                        confirm = pack_move_confirm(player_id, player.position)
                        try:
                            # Simulate delay from server to this client
                            time.sleep(self.client_delays[player_id])
                            client_socket.sendall(confirm)
                        except:
                            break
                        
                        # Broadcast to other clients
                        broadcast = pack_state_broadcast(player_id, player.position)
                        for pid, sock in self.clients.items():
                            if pid != player_id:
                                # Simulate delay from server to each target client
                                time.sleep(self.client_delays[pid])
                                try:
                                    sock.sendall(broadcast)
                                except:
                                    pass
                
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            # Clean up
            if player_id and player_id in self.players:
                del self.players[player_id]
            if player_id and player_id in self.clients:
                del self.clients[player_id]
            if player_id and player_id in self.client_delays:
                del self.client_delays[player_id]
            
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
        
        # Game settings
        if imgui.collapsing_header("Game Settings"):
            speed_changed, new_move_speed = imgui.slider_float("Move Speed", self.move_speed, 1.0, 20.0)
            
            if speed_changed:
                self.move_speed = new_move_speed
                # Update all players' speed
                for player in self.players.values():
                    player.move_speed = self.move_speed
                
                # Broadcast move speed update to all clients
                move_speed_update = pack_move_speed_update(self.move_speed)
                for pid, sock in self.clients.items():
                    try:
                        # Simulate delay before sending
                        time.sleep(self.client_delays[pid])
                        sock.sendall(move_speed_update)
                        print(f"Sent move speed update ({self.move_speed}) to player {pid}")
                    except Exception as e:
                        print(f"Failed to send move speed update to player {pid}: {e}")
        
        # Client delay settings
        if imgui.collapsing_header("Client Delays (ms)"):
            imgui.text("Enter delay for each client:")
            imgui.separator()
            
            for pid in sorted(self.players.keys()):
                current_delay_ms = int(self.client_delays.get(pid, 0.05) * 1000)
                imgui.text(f"Player {pid}:")
                imgui.same_line()
                
                # Create unique ID for input field
                imgui.push_id(f"delay_{pid}")
                delay_changed, new_delay_ms = imgui.input_int("##delay_input", current_delay_ms)
                imgui.pop_id()
                
                if delay_changed:
                    # Ensure delay is non-negative
                    new_delay_ms = max(0, new_delay_ms)
                    self.client_delays[pid] = new_delay_ms / 1000.0
                    print(f"Updated delay for player {pid} to {new_delay_ms}ms")
                    
                    # Send delay update to the client
                    if pid in self.clients:
                        try:
                            delay_update = pack_delay_update(pid, new_delay_ms)
                            # Simulate delay before sending
                            time.sleep(self.client_delays[pid])
                            self.clients[pid].sendall(delay_update)
                            print(f"Sent delay update to player {pid}")
                        except Exception as e:
                            print(f"Failed to send delay update to player {pid}: {e}")
        
        # Player list
        if imgui.collapsing_header("Players"):
            for pid, player in self.players.items():
                if imgui.tree_node(f"Player {pid}"):
                    pos = player.position
                    delay_ms = int(self.client_delays.get(pid, 0.05) * 1000)
                    imgui.text(f"Position: ({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})")
                    imgui.text(f"Delay: {delay_ms}ms")
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
