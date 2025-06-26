"""
Testes para Sistema de Coordenadas
==================================

Testes unitários para coordinate_system.py
"""

import pytest
import math
from unittest.mock import patch
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from world.coordinate_system import Coordinate, Direction, Area


class TestDirection:
    """Testes para classe Direction."""
    
    def test_direction_values(self):
        """Testa valores das direções."""
        assert Direction.NORTH.value == 0
        assert Direction.NORTHEAST.value == 1
        assert Direction.EAST.value == 2
        assert Direction.SOUTHEAST.value == 3
        assert Direction.SOUTH.value == 4
        assert Direction.SOUTHWEST.value == 5
        assert Direction.WEST.value == 6
        assert Direction.NORTHWEST.value == 7
    
    def test_from_delta(self):
        """Testa conversão de delta para direção."""
        assert Direction.from_delta(0, -1) == Direction.NORTH
        assert Direction.from_delta(1, -1) == Direction.NORTHEAST
        assert Direction.from_delta(1, 0) == Direction.EAST
        assert Direction.from_delta(1, 1) == Direction.SOUTHEAST
        assert Direction.from_delta(0, 1) == Direction.SOUTH
        assert Direction.from_delta(-1, 1) == Direction.SOUTHWEST
        assert Direction.from_delta(-1, 0) == Direction.WEST
        assert Direction.from_delta(-1, -1) == Direction.NORTHWEST
        assert Direction.from_delta(2, 3) is None  # Delta inválido
    
    def test_to_delta(self):
        """Testa conversão de direção para delta."""
        assert Direction.NORTH.to_delta() == (0, -1)
        assert Direction.NORTHEAST.to_delta() == (1, -1)
        assert Direction.EAST.to_delta() == (1, 0)
        assert Direction.SOUTHEAST.to_delta() == (1, 1)
        assert Direction.SOUTH.to_delta() == (0, 1)
        assert Direction.SOUTHWEST.to_delta() == (-1, 1)
        assert Direction.WEST.to_delta() == (-1, 0)
        assert Direction.NORTHWEST.to_delta() == (-1, -1)
    
    def test_opposite(self):
        """Testa direções opostas."""
        assert Direction.NORTH.opposite() == Direction.SOUTH
        assert Direction.EAST.opposite() == Direction.WEST
        assert Direction.NORTHEAST.opposite() == Direction.SOUTHWEST
        assert Direction.NORTHWEST.opposite() == Direction.SOUTHEAST
    
    def test_is_diagonal(self):
        """Testa verificação de direções diagonais."""
        assert Direction.NORTHEAST.is_diagonal()
        assert Direction.SOUTHEAST.is_diagonal()
        assert Direction.SOUTHWEST.is_diagonal()
        assert Direction.NORTHWEST.is_diagonal()
        
        assert not Direction.NORTH.is_diagonal()
        assert not Direction.EAST.is_diagonal()
        assert not Direction.SOUTH.is_diagonal()
        assert not Direction.WEST.is_diagonal()
    
    def test_to_degrees(self):
        """Testa conversão para graus."""
        assert Direction.NORTH.to_degrees() == 0.0
        assert Direction.EAST.to_degrees() == 90.0
        assert Direction.SOUTH.to_degrees() == 180.0
        assert Direction.WEST.to_degrees() == 270.0
    
    def test_to_radians(self):
        """Testa conversão para radianos."""
        assert Direction.NORTH.to_radians() == 0.0
        assert abs(Direction.EAST.to_radians() - math.pi/2) < 0.001
        assert abs(Direction.SOUTH.to_radians() - math.pi) < 0.001


class TestCoordinate:
    """Testes para classe Coordinate."""
    
    def test_coordinate_creation(self):
        """Testa criação de coordenadas."""
        coord = Coordinate(10, 20)
        assert coord.x == 10
        assert coord.y == 20
    
    def test_coordinate_validation(self):
        """Testa validação de coordenadas."""
        # Coordenadas válidas
        Coordinate(0, 0)
        Coordinate(100, 200)
        
        # Coordenadas inválidas
        with pytest.raises(ValueError):
            Coordinate(-1, 0)
        
        with pytest.raises(ValueError):
            Coordinate(0, -1)
        
        with pytest.raises(ValueError):
            Coordinate("10", 20)  # Tipo inválido
    
    def test_distance_to(self):
        """Testa cálculo de distância euclidiana."""
        coord1 = Coordinate(0, 0)
        coord2 = Coordinate(3, 4)
        
        assert coord1.distance_to(coord2) == 5.0
        assert coord2.distance_to(coord1) == 5.0
        assert coord1.distance_to(coord1) == 0.0
    
    def test_manhattan_distance_to(self):
        """Testa cálculo de distância Manhattan."""
        coord1 = Coordinate(0, 0)
        coord2 = Coordinate(3, 4)
        
        assert coord1.manhattan_distance_to(coord2) == 7
        assert coord2.manhattan_distance_to(coord1) == 7
        assert coord1.manhattan_distance_to(coord1) == 0
    
    def test_chebyshev_distance_to(self):
        """Testa cálculo de distância Chebyshev."""
        coord1 = Coordinate(0, 0)
        coord2 = Coordinate(3, 4)
        
        assert coord1.chebyshev_distance_to(coord2) == 4
        assert coord2.chebyshev_distance_to(coord1) == 4
        assert coord1.chebyshev_distance_to(coord1) == 0
    
    def test_direction_to(self):
        """Testa cálculo de direção."""
        origin = Coordinate(5, 5)
        
        assert origin.direction_to(Coordinate(5, 4)) == Direction.NORTH
        assert origin.direction_to(Coordinate(6, 4)) == Direction.NORTHEAST
        assert origin.direction_to(Coordinate(6, 5)) == Direction.EAST
        assert origin.direction_to(Coordinate(6, 6)) == Direction.SOUTHEAST
        assert origin.direction_to(Coordinate(5, 6)) == Direction.SOUTH
        assert origin.direction_to(Coordinate(4, 6)) == Direction.SOUTHWEST
        assert origin.direction_to(Coordinate(4, 5)) == Direction.WEST
        assert origin.direction_to(Coordinate(4, 4)) == Direction.NORTHWEST
        
        # Mesma coordenada
        assert origin.direction_to(origin) is None
    
    def test_move(self):
        """Testa movimento em direções."""
        coord = Coordinate(5, 5)
        
        # Movimento de 1 passo
        assert coord.move(Direction.NORTH) == Coordinate(5, 4)
        assert coord.move(Direction.EAST) == Coordinate(6, 5)
        assert coord.move(Direction.SOUTH) == Coordinate(5, 6)
        assert coord.move(Direction.WEST) == Coordinate(4, 5)
        
        # Movimento de múltiplos passos
        assert coord.move(Direction.NORTH, 3) == Coordinate(5, 2)
        assert coord.move(Direction.EAST, 2) == Coordinate(7, 5)
        
        # Movimento que resulta em coordenada negativa deve limitar a 0
        coord_edge = Coordinate(1, 1)
        result = coord_edge.move(Direction.NORTHWEST, 5)
        assert result.x == 0
        assert result.y == 0
    
    def test_neighbors(self):
        """Testa obtenção de vizinhos."""
        coord = Coordinate(5, 5)
        
        # Vizinhos incluindo diagonais
        neighbors = coord.neighbors(diagonal=True)
        assert len(neighbors) == 8
        assert Coordinate(4, 4) in neighbors  # Northwest
        assert Coordinate(5, 4) in neighbors  # North
        assert Coordinate(6, 4) in neighbors  # Northeast
        assert Coordinate(6, 5) in neighbors  # East
        assert Coordinate(6, 6) in neighbors  # Southeast
        assert Coordinate(5, 6) in neighbors  # South
        assert Coordinate(4, 6) in neighbors  # Southwest
        assert Coordinate(4, 5) in neighbors  # West
        
        # Vizinhos sem diagonais
        neighbors_no_diag = coord.neighbors(diagonal=False)
        assert len(neighbors_no_diag) == 4
        assert Coordinate(5, 4) in neighbors_no_diag  # North
        assert Coordinate(6, 5) in neighbors_no_diag  # East
        assert Coordinate(5, 6) in neighbors_no_diag  # South
        assert Coordinate(4, 5) in neighbors_no_diag  # West
    
    def test_is_adjacent_to(self):
        """Testa verificação de adjacência."""
        coord = Coordinate(5, 5)
        
        # Adjacentes com diagonal
        assert coord.is_adjacent_to(Coordinate(4, 4), diagonal=True)
        assert coord.is_adjacent_to(Coordinate(5, 4), diagonal=True)
        assert coord.is_adjacent_to(Coordinate(6, 6), diagonal=True)
        
        # Adjacentes sem diagonal
        assert coord.is_adjacent_to(Coordinate(5, 4), diagonal=False)
        assert coord.is_adjacent_to(Coordinate(6, 5), diagonal=False)
        assert not coord.is_adjacent_to(Coordinate(4, 4), diagonal=False)
        
        # Não adjacente
        assert not coord.is_adjacent_to(Coordinate(7, 7), diagonal=True)
        assert not coord.is_adjacent_to(coord, diagonal=True)  # Mesma coordenada
    
    def test_within_range(self):
        """Testa verificação de alcance."""
        coord = Coordinate(5, 5)
        
        assert coord.within_range(Coordinate(5, 5), 0)  # Mesma posição
        assert coord.within_range(Coordinate(6, 6), 1)  # Alcance 1
        assert coord.within_range(Coordinate(7, 7), 2)  # Alcance 2
        assert not coord.within_range(Coordinate(8, 8), 2)  # Fora do alcance
    
    def test_conversions(self):
        """Testa conversões de/para outros formatos."""
        coord = Coordinate(10, 20)
        
        # Para tupla
        assert coord.to_tuple() == (10, 20)
        
        # Para dict
        assert coord.to_dict() == {'x': 10, 'y': 20}
        
        # De tupla
        coord_from_tuple = Coordinate.from_tuple((15, 25))
        assert coord_from_tuple.x == 15
        assert coord_from_tuple.y == 25
        
        # De dict
        coord_from_dict = Coordinate.from_dict({'x': 30, 'y': 40})
        assert coord_from_dict.x == 30
        assert coord_from_dict.y == 40
    
    def test_operators(self):
        """Testa operadores."""
        coord1 = Coordinate(5, 5)
        coord2 = Coordinate(3, 2)
        
        # Adição
        result = coord1 + coord2
        assert result == Coordinate(8, 7)
        
        # Adição com tupla
        result = coord1 + (2, 3)
        assert result == Coordinate(7, 8)
        
        # Subtração
        result = coord1 - coord2
        assert result == Coordinate(2, 3)
        
        # Subtração que resultaria em negativo
        result = coord2 - coord1
        assert result == Coordinate(0, 0)  # Limitado a 0
        
        # Multiplicação por escalar
        result = coord1 * 2
        assert result == Coordinate(10, 10)
        
        # Igualdade
        assert coord1 == Coordinate(5, 5)
        assert coord1 != coord2
        
        # Comparação
        assert coord2 < coord1
    
    def test_string_representations(self):
        """Testa representações string."""
        coord = Coordinate(10, 20)
        
        assert str(coord) == "(10, 20)"
        assert repr(coord) == "Coordinate(x=10, y=20)"
    
    def test_hash(self):
        """Testa função hash."""
        coord1 = Coordinate(5, 5)
        coord2 = Coordinate(5, 5)
        coord3 = Coordinate(10, 10)
        
        # Coordenadas iguais têm mesmo hash
        assert hash(coord1) == hash(coord2)
        
        # Coordenadas diferentes têm hashes diferentes
        assert hash(coord1) != hash(coord3)
        
        # Pode ser usado em set
        coord_set = {coord1, coord2, coord3}
        assert len(coord_set) == 2  # coord1 e coord2 são iguais


class TestArea:
    """Testes para classe Area."""
    
    def test_area_creation(self):
        """Testa criação de área."""
        top_left = Coordinate(0, 0)
        bottom_right = Coordinate(10, 10)
        area = Area(top_left, bottom_right, "test_area")
        
        assert area.top_left == top_left
        assert area.bottom_right == bottom_right
        assert area.name == "test_area"
    
    def test_area_validation(self):
        """Testa validação de área."""
        # Área válida
        Area(Coordinate(0, 0), Coordinate(10, 10))
        
        # Áreas inválidas
        with pytest.raises(ValueError):
            Area(Coordinate(10, 0), Coordinate(0, 10))  # top_left.x > bottom_right.x
        
        with pytest.raises(ValueError):
            Area(Coordinate(0, 10), Coordinate(10, 0))  # top_left.y > bottom_right.y
    
    def test_area_properties(self):
        """Testa propriedades da área."""
        area = Area(Coordinate(5, 10), Coordinate(15, 25))
        
        assert area.width == 11  # 15 - 5 + 1
        assert area.height == 16  # 25 - 10 + 1
        assert area.center == Coordinate(10, 17)  # (5+15)/2, (10+25)/2
    
    def test_contains(self):
        """Testa verificação se coordenada está na área."""
        area = Area(Coordinate(5, 5), Coordinate(15, 15))
        
        assert area.contains(Coordinate(5, 5))   # Canto superior esquerdo
        assert area.contains(Coordinate(15, 15)) # Canto inferior direito
        assert area.contains(Coordinate(10, 10)) # Centro
        
        assert not area.contains(Coordinate(4, 10))  # Fora (esquerda)
        assert not area.contains(Coordinate(16, 10)) # Fora (direita)
        assert not area.contains(Coordinate(10, 4))  # Fora (cima)
        assert not area.contains(Coordinate(10, 16)) # Fora (baixo)
    
    def test_overlaps(self):
        """Testa verificação de sobreposição entre áreas."""
        area1 = Area(Coordinate(0, 0), Coordinate(10, 10))
        area2 = Area(Coordinate(5, 5), Coordinate(15, 15))  # Sobrepõe
        area3 = Area(Coordinate(15, 15), Coordinate(25, 25))  # Não sobrepõe
        area4 = Area(Coordinate(10, 10), Coordinate(20, 20))  # Toca na borda
        
        assert area1.overlaps(area2)
        assert area2.overlaps(area1)
        assert not area1.overlaps(area3)
        assert not area3.overlaps(area1)
        assert not area1.overlaps(area4)  # Apenas toca, não sobrepõe
    
    def test_intersection(self):
        """Testa interseção entre áreas."""
        area1 = Area(Coordinate(0, 0), Coordinate(10, 10))
        area2 = Area(Coordinate(5, 5), Coordinate(15, 15))
        area3 = Area(Coordinate(20, 20), Coordinate(30, 30))
        
        # Interseção que existe
        intersection = area1.intersection(area2)
        assert intersection is not None
        assert intersection.top_left == Coordinate(5, 5)
        assert intersection.bottom_right == Coordinate(10, 10)
        
        # Interseção que não existe
        no_intersection = area1.intersection(area3)
        assert no_intersection is None
    
    def test_all_coordinates(self):
        """Testa obtenção de todas as coordenadas da área."""
        small_area = Area(Coordinate(0, 0), Coordinate(2, 2))
        coords = small_area.all_coordinates()
        
        expected_coords = [
            Coordinate(0, 0), Coordinate(1, 0), Coordinate(2, 0),
            Coordinate(0, 1), Coordinate(1, 1), Coordinate(2, 1),
            Coordinate(0, 2), Coordinate(1, 2), Coordinate(2, 2)
        ]
        
        assert len(coords) == 9
        for coord in expected_coords:
            assert coord in coords
    
    def test_border_coordinates(self):
        """Testa obtenção de coordenadas da borda."""
        area = Area(Coordinate(1, 1), Coordinate(3, 3))
        border = area.border_coordinates()
        
        expected_border = [
            # Borda superior
            Coordinate(1, 1), Coordinate(2, 1), Coordinate(3, 1),
            # Borda inferior
            Coordinate(1, 3), Coordinate(2, 3), Coordinate(3, 3),
            # Borda esquerda (excluindo cantos)
            Coordinate(1, 2),
            # Borda direita (excluindo cantos)
            Coordinate(3, 2)
        ]
        
        assert len(border) == len(expected_border)
        for coord in expected_border:
            assert coord in border
    
    @patch('random.randint')
    def test_random_coordinate(self, mock_randint):
        """Testa geração de coordenada aleatória."""
        mock_randint.side_effect = [7, 8]  # x=7, y=8
        
        area = Area(Coordinate(5, 5), Coordinate(10, 10))
        random_coord = area.random_coordinate()
        
        assert random_coord == Coordinate(7, 8)
        assert area.contains(random_coord)
    
    def test_to_dict(self):
        """Testa conversão para dicionário."""
        area = Area(Coordinate(5, 5), Coordinate(15, 15), "test_area")
        area_dict = area.to_dict()
        
        expected = {
            'name': 'test_area',
            'top_left': {'x': 5, 'y': 5},
            'bottom_right': {'x': 15, 'y': 15},
            'width': 11,
            'height': 11
        }
        
        assert area_dict == expected
    
    def test_string_representations(self):
        """Testa representações string."""
        area = Area(Coordinate(5, 5), Coordinate(15, 15), "test_area")
        
        assert str(area) == "test_area: (5, 5) -> (15, 15)"
        assert repr(area) == "Area('test_area', Coordinate(x=5, y=5), Coordinate(x=15, y=15))"
        
        # Área sem nome
        unnamed_area = Area(Coordinate(0, 0), Coordinate(10, 10))
        assert str(unnamed_area) == "(0, 0) -> (10, 10)"
    
    def test_contains_operator(self):
        """Testa operador 'in'."""
        area = Area(Coordinate(5, 5), Coordinate(15, 15))
        
        assert Coordinate(10, 10) in area
        assert Coordinate(20, 20) not in area 