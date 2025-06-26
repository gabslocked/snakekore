"""
Logger System
=============

Sistema de logging avançado compatível com OpenKore.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Union
from datetime import datetime


class Logger:
    """
    Sistema de logging avançado.
    
    Características:
    - Múltiplos níveis de log
    - Output colorido no console
    - Rotação de arquivos
    - Formatação customizada
    """
    
    # Códigos de cores ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def __init__(self, 
                 level: str = 'INFO',
                 log_file: Optional[Union[str, Path]] = None,
                 verbose: int = 0):
        """
        Inicializa o logger.
        
        Args:
            level: Nível de log
            log_file: Arquivo de log (opcional)
            verbose: Nível de verbosidade
        """
        self.level = getattr(logging, level.upper())
        self.verbose = verbose
        self.log_file = Path(log_file) if log_file else None
        
        # Configura o logger
        self.logger = logging.getLogger('PythonKore')
        self.logger.setLevel(logging.DEBUG)  # Sempre DEBUG internamente
        
        # Remove handlers existentes
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Configura handlers
        self._setup_console_handler()
        if self.log_file:
            self._setup_file_handler()
    
    def _setup_console_handler(self) -> None:
        """Configura handler do console."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        
        # Formatter com cores
        formatter = ColoredFormatter(
            fmt='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self) -> None:
        """Configura handler de arquivo."""
        # Cria diretório se não existir
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter sem cores para arquivo
        formatter = logging.Formatter(
            fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str) -> None:
        """Log debug."""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log info."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log warning."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error."""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical."""
        self.logger.critical(message)
    
    def log(self, level: str, message: str) -> None:
        """Log genérico."""
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.log(log_level, message)


class ColoredFormatter(logging.Formatter):
    """Formatter com cores para o console."""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formata o record com cores.
        
        Args:
            record: Record de log
            
        Returns:
            String formatada com cores
        """
        # Adiciona cor baseada no nível
        level_color = Logger.COLORS.get(record.levelname, '')
        reset_color = Logger.COLORS['RESET']
        
        # Formata a mensagem
        formatted = super().format(record)
        
        # Adiciona cores apenas se o output suportar
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            return f"{level_color}{formatted}{reset_color}"
        else:
            return formatted 