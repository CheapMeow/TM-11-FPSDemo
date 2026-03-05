"""
Network protocol definitions for client-server communication
"""
import struct
import json


class MessageTypes:
    """Message type identifiers"""
    # Client -> Server
    MOVE_REQUEST = 0x01
    JOIN_REQUEST = 0x02
    
    # Server -> Client
    MOVE_CONFIRM = 0x10
    STATE_BROADCAST = 0x11
    INITIAL_STATE = 0x12
    PLAYER_JOINED = 0x13
    PLAYER_LEFT = 0x14


def pack_move_request(player_id, dx, dy, dz):
    """Pack movement request"""
    data = json.dumps({
        'type': MessageTypes.MOVE_REQUEST,
        'player_id': player_id,
        'dx': dx, 'dy': dy, 'dz': dz
    }).encode('utf-8')
    length = struct.pack('!I', len(data))
    return length + data


def pack_join_request(player_id):
    """Pack join request"""
    data = json.dumps({
        'type': MessageTypes.JOIN_REQUEST,
        'player_id': player_id
    }).encode('utf-8')
    length = struct.pack('!I', len(data))
    return length + data


def pack_move_confirm(player_id, new_position):
    """Pack movement confirmation"""
    data = json.dumps({
        'type': MessageTypes.MOVE_CONFIRM,
        'player_id': player_id,
        'position': (new_position.x, new_position.y, new_position.z)
    }).encode('utf-8')
    length = struct.pack('!I', len(data))
    return length + data


def pack_state_broadcast(player_id, position):
    """Pack state broadcast to other clients"""
    data = json.dumps({
        'type': MessageTypes.STATE_BROADCAST,
        'player_id': player_id,
        'position': (position.x, position.y, position.z)
    }).encode('utf-8')
    length = struct.pack('!I', len(data))
    return length + data


def pack_initial_state(players):
    """Pack initial state for new client"""
    players_data = [p.to_dict() for p in players]
    data = json.dumps({
        'type': MessageTypes.INITIAL_STATE,
        'players': players_data
    }).encode('utf-8')
    length = struct.pack('!I', len(data))
    return length + data


def pack_player_joined(player):
    """Pack player joined notification"""
    data = json.dumps({
        'type': MessageTypes.PLAYER_JOINED,
        'player': player.to_dict()
    }).encode('utf-8')
    length = struct.pack('!I', len(data))
    return length + data


def pack_player_left(player_id):
    """Pack player left notification"""
    data = json.dumps({
        'type': MessageTypes.PLAYER_LEFT,
        'player_id': player_id
    }).encode('utf-8')
    length = struct.pack('!I', len(data))
    return length + data


def receive_message(sock):
    """Receive and parse a message from socket"""
    # Read length prefix
    length_data = sock.recv(4)
    if len(length_data) < 4:
        return None
    
    length = struct.unpack('!I', length_data)[0]
    
    # Read message data
    data = b''
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            return None
        data += chunk
    
    # Parse JSON
    try:
        message = json.loads(data.decode('utf-8'))
        return message
    except:
        return None
