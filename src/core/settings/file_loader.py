"""
File Loader
===========

Carregador de arquivos de configuração.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from config_parser import ConfigParser


class FileLoader:
    """Carregador de arquivos de configuração."""
    
    def __init__(self):
        """Inicializa o carregador."""
        self.parser = ConfigParser()
        self.encodings = ['utf-8', 'latin-1', 'cp1252']
    
    def load_file(self, file_path: Path, loader_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Carrega um arquivo de configuração.
        
        Args:
            file_path: Caminho do arquivo
            loader_type: Tipo de loader a usar
            
        Returns:
            Dados carregados do arquivo
        """
        content = self._read_file(file_path)
        
        if loader_type == "config_parser":
            return self.parser.parse_config_file(content)
        elif loader_type == "data_parser":
            return self.parser.parse_data_file(content)
        elif loader_type == "sectioned_parser":
            return self.parser.parse_sectioned_file(content)
        elif loader_type == "responses_parser":
            return {"responses": self.parser.parse_responses_file(content)}
        elif loader_type == "timeouts_parser":
            return self.parser.parse_timeouts_file(content)
        elif loader_type == "shop_parser":
            return {"items": self.parser.parse_shop_file(content)}
        else:
            # Auto-detecta o tipo baseado no nome do arquivo
            return self._auto_detect_and_parse(file_path, content)
    
    def _read_file(self, file_path: Path) -> str:
        """
        Lê o conteúdo de um arquivo tentando diferentes encodings.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Conteúdo do arquivo como string
        """
        for encoding in self.encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        # Se nenhum encoding funcionou, usa o último com errors='ignore'
        with open(file_path, 'r', encoding=self.encodings[-1], errors='ignore') as f:
            return f.read()
    
    def _auto_detect_and_parse(self, file_path: Path, content: str) -> Dict[str, Any]:
        """
        Auto-detecta o tipo do arquivo e faz o parse apropriado.
        
        Args:
            file_path: Caminho do arquivo
            content: Conteúdo do arquivo
            
        Returns:
            Dados parseados
        """
        filename = file_path.name.lower()
        
        if filename in ['config.txt', 'sys.txt']:
            return self.parser.parse_config_file(content)
        elif filename in ['responses.txt', 'chat_resp.txt']:
            return {"responses": self.parser.parse_responses_file(content)}
        elif filename == 'timeouts.txt':
            return self.parser.parse_timeouts_file(content)
        elif filename in ['shop.txt', 'buyer_shop.txt']:
            return {"items": self.parser.parse_shop_file(content)}
        elif filename == 'consolecolors.txt':
            return self.parser.parse_sectioned_file(content)
        else:
            # Default para data parser
            return self.parser.parse_data_file(content) 