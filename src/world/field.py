"""
Field System
============

Sistema de campos/mapas do PythonKore.
Compatível com arquivos .fld/.fld2 do OpenKore.
"""

import gzip
import struct
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass

from coordinate_system import Coordinate, Area


class CellType(Enum):
    """Tipos de célula no mapa."""
    WALKABLE = 0      # Caminhável
    NON_WALKABLE = 1  # Não caminhável (parede, obstáculo)
    WATER = 2         # Água (pode ser caminhável dependendo do contexto)
    SNIPABLE = 3      # Pode ser atacado à distância
    UNKNOWN = 4       # Desconhecido


class FieldType(Enum):
    """Tipos de campo/mapa."""
    TOWN = "town"           # Cidade
    FIELD = "field"         # Campo aberto
    DUNGEON = "dungeon"     # Dungeon
    GUILD = "guild"         # Castelo de guild
    PVP = "pvp"            # Área PvP
    INSTANCE = "instance"   # Instância
    UNKNOWN = "unknown"     # Desconhecido


@dataclass
class FieldInfo:
    """Informações do campo."""
    name: str
    display_name: str
    field_type: FieldType
    width: int
    height: int
    base_exp_rate: float = 1.0
    job_exp_rate: float = 1.0
    drop_rate: float = 1.0
    respawn_rate: float = 1.0
    no_teleport: bool = False
    no_memo: bool = False
    no_return: bool = False
    no_save: bool = False
    pvp_enabled: bool = False
    gvg_enabled: bool = False


class Field:
    """
    Representa um campo/mapa do jogo.
    
    Funcionalidades:
    - Carregamento de arquivos .fld/.fld2
    - Verificação de walkability
    - Pathfinding básico
    - Gerenciamento de objetos no mapa
    """
    
    def __init__(self, name: str, width: int = 0, height: int = 0):
        """
        Inicializa campo.
        
        Args:
            name: Nome do campo
            width: Largura do campo
            height: Altura do campo
        """
        self.name = name
        self.width = width
        self.height = height
        
        # Informações do campo
        self.info = FieldInfo(
            name=name,
            display_name=name,
            field_type=FieldType.UNKNOWN,
            width=width,
            height=height
        )
        
        # Dados do mapa (matriz de células)
        self.cells: List[List[CellType]] = []
        
        # Objetos no mapa
        self.portals: Dict[Coordinate, Any] = {}
        self.npcs: Dict[Coordinate, Any] = {}
        self.monsters: Dict[Coordinate, Any] = {}
        self.items: Dict[Coordinate, Any] = {}
        
        # Cache de pathfinding
        self._distance_cache: Dict[Tuple[Coordinate, Coordinate], int] = {}
        
        # Estado
        self.loaded = False
        self.last_updated = 0.0
        
        # Inicializa células se dimensões foram fornecidas
        if width > 0 and height > 0:
            self._initialize_cells()
    
    def _initialize_cells(self) -> None:
        """Inicializa matriz de células."""
        self.cells = [[CellType.WALKABLE for _ in range(self.width)] 
                     for _ in range(self.height)]
    
    def is_valid_coordinate(self, coord: Coordinate) -> bool:
        """
        Verifica se coordenada é válida no mapa.
        
        Args:
            coord: Coordenada a verificar
            
        Returns:
            True se for válida
        """
        return (0 <= coord.x < self.width and 
                0 <= coord.y < self.height)
    
    def is_walkable(self, coord: Coordinate) -> bool:
        """
        Verifica se coordenada é caminhável.
        
        Args:
            coord: Coordenada a verificar
            
        Returns:
            True se for caminhável
        """
        if not self.is_valid_coordinate(coord):
            return False
        
        if not self.cells or coord.y >= len(self.cells):
            return False
        
        if coord.x >= len(self.cells[coord.y]):
            return False
        
        cell_type = self.cells[coord.y][coord.x]
        return cell_type in [CellType.WALKABLE, CellType.WATER]
    
    def get_cell_type(self, coord: Coordinate) -> CellType:
        """
        Obtém tipo da célula.
        
        Args:
            coord: Coordenada
            
        Returns:
            Tipo da célula
        """
        if not self.is_valid_coordinate(coord):
            return CellType.UNKNOWN
        
        if not self.cells or coord.y >= len(self.cells):
            return CellType.UNKNOWN
        
        if coord.x >= len(self.cells[coord.y]):
            return CellType.UNKNOWN
        
        return self.cells[coord.y][coord.x]
    
    def get_walkable_neighbors(self, coord: Coordinate, diagonal: bool = True) -> List[Coordinate]:
        """
        Obtém vizinhos caminháveis.
        
        Args:
            coord: Coordenada de origem
            diagonal: Incluir movimentos diagonais
            
        Returns:
            Lista de coordenadas caminháveis
        """
        neighbors = []
        
        for neighbor in coord.neighbors(diagonal):
            if self.is_walkable(neighbor):
                neighbors.append(neighbor)
        
        return neighbors
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtém resumo do campo."""
        walkable_count = 0
        total_cells = self.width * self.height
        
        if self.cells:
            for row in self.cells:
                for cell in row:
                    if cell in [CellType.WALKABLE, CellType.WATER]:
                        walkable_count += 1
        
        return {
            'name': self.name,
            'display_name': self.info.display_name,
            'type': self.info.field_type.value,
            'dimensions': f"{self.width}x{self.height}",
            'total_cells': total_cells,
            'walkable_cells': walkable_count,
            'walkable_percent': (walkable_count / total_cells * 100) if total_cells > 0 else 0,
            'loaded': self.loaded,
            'portals': len(self.portals),
            'npcs': len(self.npcs),
            'monsters': len(self.monsters),
            'items': len(self.items)
        }
    
    def __str__(self) -> str:
        """Representação string."""
        return f"Field({self.name}, {self.width}x{self.height})"
    
    def __repr__(self) -> str:
        """Representação para debug."""
        return f"Field(name='{self.name}', width={self.width}, height={self.height}, loaded={self.loaded})" 