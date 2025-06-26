"""
Configuration File Parser
==========================

Parser para arquivos de configuração no formato OpenKore.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Union


class ConfigParser:
    """Parser para arquivos de configuração."""
    
    def __init__(self):
        """Inicializa o parser."""
        self.comment_pattern = re.compile(r'^\s*#.*$')
        self.empty_pattern = re.compile(r'^\s*$')
        self.config_pattern = re.compile(r'^(\S+)\s+(.+)$')
    
    def parse_config_file(self, content: str) -> Dict[str, Any]:
        """
        Parse um arquivo de configuração no formato config.txt.
        
        Args:
            content: Conteúdo do arquivo
            
        Returns:
            Dicionário com as configurações
        """
        config = {}
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Ignora comentários e linhas vazias
            if self.comment_pattern.match(line) or self.empty_pattern.match(line):
                continue
            
            # Parse da linha de configuração
            match = self.config_pattern.match(line)
            if match:
                key = match.group(1)
                value = match.group(2).strip()
                
                # Converte valores especiais
                config[key] = self._convert_value(value)
            else:
                print(f"Linha inválida {line_num}: {line}")
        
        return config
    
    def parse_data_file(self, content: str) -> Dict[str, str]:
        """
        Parse um arquivo de dados simples (chave valor).
        
        Args:
            content: Conteúdo do arquivo
            
        Returns:
            Dicionário com os dados
        """
        data = {}
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Ignora comentários e linhas vazias
            if self.comment_pattern.match(line) or self.empty_pattern.match(line):
                continue
            
            # Parse da linha
            parts = line.split(None, 1)
            if len(parts) >= 2:
                key = parts[0]
                value = parts[1] if len(parts) > 1 else ""
                data[key] = value
            elif len(parts) == 1:
                # Linha apenas com chave
                data[parts[0]] = ""
        
        return data
    
    def parse_sectioned_file(self, content: str) -> Dict[str, Dict[str, str]]:
        """
        Parse um arquivo com seções (como consolecolors.txt).
        
        Args:
            content: Conteúdo do arquivo
            
        Returns:
            Dicionário com seções e configurações
        """
        data = {}
        current_section = "default"
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Ignora comentários e linhas vazias
            if self.comment_pattern.match(line) or self.empty_pattern.match(line):
                continue
            
            # Verifica se é uma seção
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                if current_section not in data:
                    data[current_section] = {}
                continue
            
            # Parse da linha de configuração
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if current_section not in data:
                    data[current_section] = {}
                
                data[current_section][key] = value
        
        return data
    
    def parse_responses_file(self, content: str) -> List[Dict[str, str]]:
        """
        Parse um arquivo de respostas (responses.txt).
        
        Args:
            content: Conteúdo do arquivo
            
        Returns:
            Lista de respostas
        """
        responses = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Ignora comentários e linhas vazias
            if self.comment_pattern.match(line) or self.empty_pattern.match(line):
                continue
            
            # Parse da resposta (formato: trigger response)
            parts = line.split(None, 1)
            if len(parts) >= 2:
                responses.append({
                    'trigger': parts[0],
                    'response': parts[1]
                })
        
        return responses
    
    def parse_timeouts_file(self, content: str) -> Dict[str, float]:
        """
        Parse um arquivo de timeouts.
        
        Args:
            content: Conteúdo do arquivo
            
        Returns:
            Dicionário com timeouts
        """
        timeouts = {}
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Ignora comentários e linhas vazias
            if self.comment_pattern.match(line) or self.empty_pattern.match(line):
                continue
            
            # Parse da linha (formato: timeout_name value)
            parts = line.split(None, 1)
            if len(parts) >= 2:
                key = parts[0]
                try:
                    value = float(parts[1])
                    timeouts[key] = value
                except ValueError:
                    print(f"Valor inválido para timeout {key}: {parts[1]}")
        
        return timeouts
    
    def parse_shop_file(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse um arquivo de shop.
        
        Args:
            content: Conteúdo do arquivo
            
        Returns:
            Lista de itens do shop
        """
        items = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Ignora comentários e linhas vazias
            if self.comment_pattern.match(line) or self.empty_pattern.match(line):
                continue
            
            # Parse do item (formato: item quantidade preço)
            parts = line.split()
            if len(parts) >= 3:
                try:
                    items.append({
                        'item': parts[0],
                        'quantity': int(parts[1]),
                        'price': int(parts[2])
                    })
                except ValueError:
                    print(f"Linha inválida no shop: {line}")
        
        return items
    
    def _convert_value(self, value: str) -> Union[str, int, float, bool]:
        """
        Converte um valor string para o tipo apropriado.
        
        Args:
            value: Valor como string
            
        Returns:
            Valor convertido
        """
        # Remove aspas se existirem
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        
        # Tenta converter para número
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Converte booleanos
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Retorna como string
        return value 