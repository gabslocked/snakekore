"""
String Utils
============

Utilidades de manipulação de strings para o PythonKore.
"""

import re
import unicodedata
from typing import List, Dict, Optional, Union


class StringUtils:
    """
    Utilidades de string.
    
    Funcionalidades:
    - Limpeza e formatação
    - Validação
    - Conversões
    - Parsing específico do RO
    """
    
    @staticmethod
    def clean_string(text: str) -> str:
        """
        Limpa string removendo caracteres especiais.
        
        Args:
            text: Texto a limpar
            
        Returns:
            Texto limpo
        """
        if not text:
            return ""
        
        # Remove caracteres de controle
        cleaned = ''.join(char for char in text if not unicodedata.category(char).startswith('C'))
        
        # Remove espaços extras
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """
        Normaliza nome de jogador/NPC/monstro.
        
        Args:
            name: Nome a normalizar
            
        Returns:
            Nome normalizado
        """
        if not name:
            return ""
        
        # Remove espaços e converte para lowercase
        normalized = name.strip().lower()
        
        # Remove caracteres especiais mas mantém espaços e números
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Remove espaços extras
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    @staticmethod
    def is_valid_player_name(name: str) -> bool:
        """
        Valida nome de jogador.
        
        Args:
            name: Nome a validar
            
        Returns:
            True se válido
        """
        if not name or len(name) < 4 or len(name) > 23:
            return False
        
        # Deve começar com letra
        if not name[0].isalpha():
            return False
        
        # Apenas letras, números e espaços
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9\s]*$', name):
            return False
        
        # Não pode ter espaços consecutivos
        if '  ' in name:
            return False
        
        return True
    
    @staticmethod
    def format_number(number: Union[int, float], thousands_sep: str = ",") -> str:
        """
        Formata número com separador de milhares.
        
        Args:
            number: Número a formatar
            thousands_sep: Separador de milhares
            
        Returns:
            Número formatado
        """
        if isinstance(number, float):
            return f"{number:,.2f}".replace(",", thousands_sep)
        else:
            return f"{number:,}".replace(",", thousands_sep)
    
    @staticmethod
    def format_time(seconds: int) -> str:
        """
        Formata tempo em segundos para string legível.
        
        Args:
            seconds: Tempo em segundos
            
        Returns:
            Tempo formatado (ex: "1h 30m 45s")
        """
        if seconds < 60:
            return f"{seconds}s"
        
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        
        if minutes < 60:
            return f"{minutes}m {remaining_seconds}s"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if hours < 24:
            return f"{hours}h {remaining_minutes}m {remaining_seconds}s"
        
        days = hours // 24
        remaining_hours = hours % 24
        
        return f"{days}d {remaining_hours}h {remaining_minutes}m"
    
    @staticmethod
    def parse_time_string(time_str: str) -> int:
        """
        Converte string de tempo para segundos.
        
        Args:
            time_str: String de tempo (ex: "1h 30m", "45s")
            
        Returns:
            Tempo em segundos
        """
        if not time_str:
            return 0
        
        total_seconds = 0
        
        # Procura padrões de tempo
        patterns = {
            r'(\d+)d': 24 * 60 * 60,  # dias
            r'(\d+)h': 60 * 60,       # horas
            r'(\d+)m': 60,            # minutos
            r'(\d+)s': 1              # segundos
        }
        
        for pattern, multiplier in patterns.items():
            matches = re.findall(pattern, time_str.lower())
            for match in matches:
                total_seconds += int(match) * multiplier
        
        return total_seconds
    
    @staticmethod
    def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
        """
        Trunca string se exceder comprimento máximo.
        
        Args:
            text: Texto a truncar
            max_length: Comprimento máximo
            suffix: Sufixo para texto truncado
            
        Returns:
            Texto truncado
        """
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def pad_string(text: str, width: int, char: str = " ", align: str = "left") -> str:
        """
        Preenche string até largura especificada.
        
        Args:
            text: Texto a preencher
            width: Largura desejada
            char: Caractere de preenchimento
            align: Alinhamento ("left", "right", "center")
            
        Returns:
            Texto preenchido
        """
        if len(text) >= width:
            return text
        
        if align == "right":
            return text.rjust(width, char)
        elif align == "center":
            return text.center(width, char)
        else:  # left
            return text.ljust(width, char)
    
    @staticmethod
    def extract_numbers(text: str) -> List[int]:
        """
        Extrai números de uma string.
        
        Args:
            text: Texto a processar
            
        Returns:
            Lista de números encontrados
        """
        if not text:
            return []
        
        numbers = re.findall(r'-?\d+', text)
        return [int(num) for num in numbers]
    
    @staticmethod
    def contains_any(text: str, keywords: List[str], case_sensitive: bool = False) -> bool:
        """
        Verifica se texto contém alguma das palavras-chave.
        
        Args:
            text: Texto a verificar
            keywords: Lista de palavras-chave
            case_sensitive: Se deve considerar maiúsculas/minúsculas
            
        Returns:
            True se contém alguma palavra-chave
        """
        if not text or not keywords:
            return False
        
        search_text = text if case_sensitive else text.lower()
        
        for keyword in keywords:
            search_keyword = keyword if case_sensitive else keyword.lower()
            if search_keyword in search_text:
                return True
        
        return False
    
    @staticmethod
    def similarity(text1: str, text2: str) -> float:
        """
        Calcula similaridade entre duas strings (Levenshtein simplificado).
        
        Args:
            text1: Primeira string
            text2: Segunda string
            
        Returns:
            Similaridade (0.0 a 1.0)
        """
        if not text1 and not text2:
            return 1.0
        
        if not text1 or not text2:
            return 0.0
        
        # Normaliza strings
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()
        
        if t1 == t2:
            return 1.0
        
        # Calcula distância de Levenshtein simplificada
        len1, len2 = len(t1), len(t2)
        max_len = max(len1, len2)
        
        if max_len == 0:
            return 1.0
        
        # Conta caracteres diferentes
        differences = 0
        for i in range(max_len):
            c1 = t1[i] if i < len1 else ''
            c2 = t2[i] if i < len2 else ''
            if c1 != c2:
                differences += 1
        
        return 1.0 - (differences / max_len)
    
    # Funções específicas do RO
    @staticmethod
    def parse_item_name(item_string: str) -> Dict[str, Union[str, int]]:
        """
        Faz parse de string de item do RO.
        
        Args:
            item_string: String do item (ex: "Red Potion [5]")
            
        Returns:
            Dicionário com dados do item
        """
        result = {
            'name': '',
            'quantity': 1,
            'slots': 0,
            'refined': 0,
            'broken': False
        }
        
        if not item_string:
            return result
        
        # Remove espaços extras
        clean_string = item_string.strip()
        
        # Extrai quantidade (ex: "5x Red Potion")
        quantity_match = re.match(r'(\d+)x\s*(.+)', clean_string, re.IGNORECASE)
        if quantity_match:
            result['quantity'] = int(quantity_match.group(1))
            clean_string = quantity_match.group(2)
        
        # Extrai slots (ex: "Red Potion [2]")
        slots_match = re.search(r'\[(\d+)\]', clean_string)
        if slots_match:
            result['slots'] = int(slots_match.group(1))
            clean_string = re.sub(r'\[\d+\]', '', clean_string).strip()
        
        # Extrai refinamento (ex: "+7 Sword")
        refine_match = re.match(r'\+(\d+)\s*(.+)', clean_string)
        if refine_match:
            result['refined'] = int(refine_match.group(1))
            clean_string = refine_match.group(2)
        
        # Verifica se está quebrado
        if 'broken' in clean_string.lower():
            result['broken'] = True
            clean_string = re.sub(r'\bbroken\b', '', clean_string, flags=re.IGNORECASE).strip()
        
        result['name'] = clean_string.strip()
        return result
    
    @staticmethod
    def format_chat_message(message: str, player: str, chat_type: str = "public") -> str:
        """
        Formata mensagem de chat.
        
        Args:
            message: Mensagem
            player: Nome do jogador
            chat_type: Tipo do chat
            
        Returns:
            Mensagem formatada
        """
        timestamp = StringUtils.format_time(0)  # TODO: usar tempo real
        
        if chat_type == "private":
            return f"[PM] {player}: {message}"
        elif chat_type == "guild":
            return f"[Guild] {player}: {message}"
        elif chat_type == "party":
            return f"[Party] {player}: {message}"
        else:
            return f"{player}: {message}"
    
    @staticmethod
    def escape_regex(text: str) -> str:
        """
        Escapa caracteres especiais de regex.
        
        Args:
            text: Texto a escapar
            
        Returns:
            Texto escapado
        """
        return re.escape(text)
    
    @staticmethod
    def to_snake_case(text: str) -> str:
        """
        Converte texto para snake_case.
        
        Args:
            text: Texto a converter
            
        Returns:
            Texto em snake_case
        """
        # Substitui espaços e hífens por underscores
        text = re.sub(r'[\s\-]+', '_', text)
        
        # Insere underscore antes de maiúsculas
        text = re.sub(r'([a-z])([A-Z])', r'\1_\2', text)
        
        return text.lower()
    
    @staticmethod
    def to_camel_case(text: str) -> str:
        """
        Converte texto para camelCase.
        
        Args:
            text: Texto a converter
            
        Returns:
            Texto em camelCase
        """
        words = re.split(r'[\s\-_]+', text.lower())
        if not words:
            return ""
        
        return words[0] + ''.join(word.capitalize() for word in words[1:])
    
    @staticmethod
    def generate_random_string(length: int, chars: str = "abcdefghijklmnopqrstuvwxyz0123456789") -> str:
        """
        Gera string aleatória.
        
        Args:
            length: Comprimento da string
            chars: Caracteres permitidos
            
        Returns:
            String aleatória
        """
        import random
        return ''.join(random.choice(chars) for _ in range(length)) 