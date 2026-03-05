"""
Player class representing a character in the game
"""
import glm
import random


class Player:
    def __init__(self, player_id, position=None, color=None, move_speed=5.0):
        self.id = player_id
        self.radius = 1.0
        
        # Position (authoritative on server)
        if position is None:
            # Random position within visible range
            x = random.uniform(-5.0, 5.0)
            y = random.uniform(0.5, 2.5)
            z = random.uniform(-5.0, 5.0)
            self.position = glm.vec3(x, y, z)
        else:
            self.position = glm.vec3(position.x, position.y, position.z)
        
        # Color
        if color is None:
            # Random bright color
            self.color = glm.vec3(
                random.uniform(0.3, 1.0),
                random.uniform(0.3, 1.0),
                random.uniform(0.3, 1.0)
            )
        else:
            self.color = glm.vec3(color.x, color.y, color.z)
        
        # Movement parameters
        self.move_speed = move_speed
        
        # Pending movement (client-side prediction)
        self.pending_movement = None
    
    def set_position(self, position):
        """Set position (from server authority)"""
        self.position = glm.vec3(position.x, position.y, position.z)
    
    def get_position(self):
        """Get position as tuple for serialization"""
        return (self.position.x, self.position.y, self.position.z)
    
    def get_color(self):
        """Get color as tuple for serialization"""
        return (self.color.x, self.color.y, self.color.z)
    
    def to_dict(self):
        """Serialize player to dictionary"""
        return {
            'id': self.id,
            'position': self.get_position(),
            'color': self.get_color(),
            'move_speed': self.move_speed
        }
    
    @staticmethod
    def from_dict(data):
        """Create player from dictionary"""
        pos = glm.vec3(*data['position'])
        color = glm.vec3(*data['color'])
        return Player(
            player_id=data['id'],
            position=pos,
            color=color,
            move_speed=data['move_speed']
        )
