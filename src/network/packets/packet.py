"""
Packet Base Classes
===================

Classes base para sistema de packets.
"""

import struct
from enum import Enum
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field


class PacketType(Enum):
    """Tipos de packets RO."""
    # Login Server
    ACCOUNT_LOGIN = 0x0064
    LOGIN_RESPONSE = 0x0069
    SERVER_LIST = 0x0069
    
    # Character Server  
    CHAR_LOGIN = 0x0065
    CHAR_LIST = 0x006B
    CHAR_SELECT = 0x0066
    CHAR_CREATE = 0x0067
    CHAR_DELETE = 0x0068
    
    # Map Server
    MAP_LOGIN = 0x0072
    MAP_LOADED = 0x007D
    WALK = 0x0085
    STOP_WALKING = 0x0088
    
    # Game Data
    ACTOR_DISPLAY = 0x0078
    ACTOR_MOVE = 0x007B
    ACTOR_SPAWN = 0x007C
    ACTOR_DIED = 0x0080
    ACTOR_DISAPPEARED = 0x0080
    
    # Chat
    PUBLIC_CHAT = 0x008C
    PRIVATE_CHAT = 0x0096
    GUILD_CHAT = 0x017E
    
    # Status
    STAT_INFO = 0x00B0
    STAT_INFO2 = 0x00B1
    SKILL_INFO = 0x010F
    
    # Items
    INVENTORY_LIST = 0x01EE
    ITEM_PICKUP = 0x009F
    ITEM_DROP = 0x00A2
    
    # Misc
    KEEP_ALIVE = 0x007E
    DISCONNECT = 0x018B
    
    # Custom/Unknown
    UNKNOWN = 0xFFFF


@dataclass
class PacketField:
    """Campo de um packet."""
    name: str
    format: str
    size: int
    description: str = ""
    default: Any = None


@dataclass
class Packet:
    """
    Classe base para packets RO.
    
    Representa um packet com:
    - Tipo/ID do packet
    - Dados binários
    - Campos estruturados
    - Metadados
    """
    
    packet_type: PacketType
    data: bytes = b''
    size: int = 0
    fields: Dict[str, Any] = field(default_factory=dict)
    raw_data: bytes = b''
    timestamp: float = 0.0
    
    def __post_init__(self):
        """Inicialização pós-criação."""
        if self.data and not self.size:
            self.size = len(self.data)
        
        if not self.raw_data:
            self.raw_data = self.data
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'Packet':
        """
        Cria packet a partir de dados binários.
        
        Args:
            data: Dados binários do packet
            
        Returns:
            Instância do packet
        """
        if len(data) < 2:
            raise ValueError("Dados insuficientes para packet")
        
        # Lê o tipo do packet (primeiros 2 bytes, little endian)
        packet_id = struct.unpack('<H', data[:2])[0]
        
        # Tenta mapear para enum
        try:
            packet_type = PacketType(packet_id)
        except ValueError:
            packet_type = PacketType.UNKNOWN
        
        return cls(
            packet_type=packet_type,
            data=data[2:],  # Remove header
            size=len(data),
            raw_data=data
        )
    
    def to_bytes(self) -> bytes:
        """
        Converte packet para bytes.
        
        Returns:
            Dados binários do packet
        """
        # Constrói header (tipo do packet)
        header = struct.pack('<H', self.packet_type.value)
        
        return header + self.data
    
    def get_field(self, name: str, default: Any = None) -> Any:
        """
        Obtém valor de um campo.
        
        Args:
            name: Nome do campo
            default: Valor padrão
            
        Returns:
            Valor do campo
        """
        return self.fields.get(name, default)
    
    def set_field(self, name: str, value: Any) -> None:
        """
        Define valor de um campo.
        
        Args:
            name: Nome do campo
            value: Valor do campo
        """
        self.fields[name] = value
    
    def has_field(self, name: str) -> bool:
        """
        Verifica se tem um campo.
        
        Args:
            name: Nome do campo
            
        Returns:
            True se tem o campo
        """
        return name in self.fields
    
    def get_packet_id(self) -> int:
        """
        Obtém ID do packet.
        
        Returns:
            ID numérico do packet
        """
        return self.packet_type.value
    
    def get_packet_name(self) -> str:
        """
        Obtém nome do packet.
        
        Returns:
            Nome do packet
        """
        return self.packet_type.name
    
    def is_valid(self) -> bool:
        """
        Verifica se o packet é válido.
        
        Returns:
            True se válido
        """
        return (self.packet_type != PacketType.UNKNOWN and 
                self.size >= 2 and 
                len(self.raw_data) >= 2)
    
    def __str__(self) -> str:
        """Representação string do packet."""
        return f"Packet({self.get_packet_name()}, size={self.size})"
    
    def __repr__(self) -> str:
        """Representação detalhada do packet."""
        return (f"Packet(type={self.packet_type.name}, "
                f"id=0x{self.packet_type.value:04X}, "
                f"size={self.size}, "
                f"fields={len(self.fields)})")


class PacketDefinition:
    """
    Definição de estrutura de um packet.
    
    Define como parsear e construir packets específicos.
    """
    
    def __init__(self, 
                 packet_type: PacketType,
                 name: str,
                 size: int = -1,
                 fields: Optional[list] = None):
        """
        Inicializa definição de packet.
        
        Args:
            packet_type: Tipo do packet
            name: Nome descritivo
            size: Tamanho fixo (-1 para variável)
            fields: Lista de campos
        """
        self.packet_type = packet_type
        self.name = name
        self.size = size
        self.fields = fields or []
        self.is_variable_length = size == -1
    
    def add_field(self, name: str, format: str, description: str = "") -> None:
        """
        Adiciona um campo à definição.
        
        Args:
            name: Nome do campo
            format: Formato struct
            description: Descrição do campo
        """
        size = struct.calcsize(format)
        field = PacketField(
            name=name,
            format=format,
            size=size,
            description=description
        )
        self.fields.append(field)
    
    def get_total_size(self) -> int:
        """
        Calcula tamanho total dos campos.
        
        Returns:
            Tamanho total em bytes
        """
        if self.is_variable_length:
            return -1
        
        total = 2  # Header (packet ID)
        for field in self.fields:
            total += field.size
        
        return total 