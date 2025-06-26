"""
Settings Manager
================

Gerenciador principal de configurações do PythonKore.
Compatível com arquivos de configuração do OpenKore.
"""

import os
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field

from config_parser import ConfigParser
from file_loader import FileLoader
from validators import ConfigValidator
from defaults import DEFAULT_CONFIG


@dataclass
class ConfigFile:
    """Representa um arquivo de configuração."""
    path: Path
    internal_name: str
    loader: Optional[str] = None
    auto_search: bool = True
    last_modified: float = 0.0
    data: Dict[str, Any] = field(default_factory=dict)


class SettingsManager:
    """
    Gerenciador principal de configurações.
    
    Responsável por:
    - Carregar e gerenciar arquivos de configuração
    - Validar configurações
    - Notificar mudanças
    - Compatibilidade com OpenKore
    """
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """
        Inicializa o gerenciador de configurações.
        
        Args:
            config_dir: Diretório de configurações (padrão: ./control)
        """
        self._config_dir = Path(config_dir or "control")
        self._tables_dir = Path("tables")
        self._config_files: Dict[str, ConfigFile] = {}
        self._config_data: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._parser = ConfigParser()
        self._loader = FileLoader()
        self._validator = ConfigValidator()
        
        # Event callbacks
        self._on_config_change_callbacks: List[callable] = []
        
        # Initialize with defaults
        self._config_data.update(DEFAULT_CONFIG)
    
    def add_control_file(self, 
                        filename: str, 
                        internal_name: Optional[str] = None,
                        loader: Optional[str] = None,
                        auto_search: bool = True) -> None:
        """
        Adiciona um arquivo de controle para ser gerenciado.
        
        Args:
            filename: Nome do arquivo ou caminho
            internal_name: Nome interno para referência
            loader: Tipo de loader a ser usado
            auto_search: Se deve buscar automaticamente o arquivo
        """
        with self._lock:
            if internal_name is None:
                internal_name = filename
                
            file_path = self._resolve_file_path(filename)
            
            config_file = ConfigFile(
                path=file_path,
                internal_name=internal_name,
                loader=loader,
                auto_search=auto_search
            )
            
            self._config_files[internal_name] = config_file
            
            # Carrega o arquivo se existir
            if file_path.exists():
                self._load_config_file(config_file)
    
    def _resolve_file_path(self, filename: str) -> Path:
        """Resolve o caminho completo do arquivo."""
        if os.path.isabs(filename):
            return Path(filename)
        
        # Tenta no diretório de controle primeiro
        control_path = self._config_dir / filename
        if control_path.exists():
            return control_path
            
        # Tenta no diretório de tabelas
        tables_path = self._tables_dir / filename
        if tables_path.exists():
            return tables_path
            
        # Retorna o caminho no diretório de controle (mesmo se não existir)
        return control_path
    
    def _load_config_file(self, config_file: ConfigFile) -> None:
        """Carrega um arquivo de configuração."""
        try:
            if not config_file.path.exists():
                return
                
            # Verifica se o arquivo foi modificado
            current_mtime = config_file.path.stat().st_mtime
            if current_mtime <= config_file.last_modified:
                return
                
            # Carrega o arquivo
            data = self._loader.load_file(config_file.path, config_file.loader)
            
            # Valida os dados
            if self._validator.validate(config_file.internal_name, data):
                config_file.data = data
                config_file.last_modified = current_mtime
                
                # Atualiza os dados de configuração
                self._update_config_data(config_file.internal_name, data)
                
                # Notifica mudanças
                self._notify_config_change(config_file.internal_name)
                
        except Exception as e:
            print(f"Erro ao carregar {config_file.path}: {e}")
    
    def _update_config_data(self, internal_name: str, data: Dict[str, Any]) -> None:
        """Atualiza os dados de configuração."""
        if internal_name == "config.txt":
            # Configuração principal
            self._config_data.update(data)
        else:
            # Outros arquivos são armazenados com seu nome interno
            self._config_data[internal_name] = data
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém um valor de configuração.
        
        Args:
            key: Chave da configuração
            default: Valor padrão se não encontrado
            
        Returns:
            Valor da configuração
        """
        with self._lock:
            return self._config_data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Define um valor de configuração.
        
        Args:
            key: Chave da configuração
            value: Valor a ser definido
        """
        with self._lock:
            old_value = self._config_data.get(key)
            self._config_data[key] = value
            
            if old_value != value:
                self._notify_config_change(key)
    
    def get_config_data(self, internal_name: str) -> Dict[str, Any]:
        """
        Obtém todos os dados de um arquivo de configuração.
        
        Args:
            internal_name: Nome interno do arquivo
            
        Returns:
            Dados do arquivo de configuração
        """
        with self._lock:
            return self._config_data.get(internal_name, {}).copy()
    
    def reload_all(self) -> None:
        """Recarrega todos os arquivos de configuração."""
        with self._lock:
            for config_file in self._config_files.values():
                self._load_config_file(config_file)
    
    def reload_file(self, internal_name: str) -> None:
        """
        Recarrega um arquivo específico.
        
        Args:
            internal_name: Nome interno do arquivo
        """
        with self._lock:
            if internal_name in self._config_files:
                config_file = self._config_files[internal_name]
                config_file.last_modified = 0  # Force reload
                self._load_config_file(config_file)
    
    def on_config_change(self, callback: callable) -> None:
        """
        Registra um callback para mudanças de configuração.
        
        Args:
            callback: Função a ser chamada quando a config mudar
        """
        self._on_config_change_callbacks.append(callback)
    
    def _notify_config_change(self, key: str) -> None:
        """Notifica os callbacks sobre mudanças."""
        for callback in self._on_config_change_callbacks:
            try:
                callback(key)
            except Exception as e:
                print(f"Erro em callback de configuração: {e}")
    
    def get_config_filename(self) -> Path:
        """Retorna o caminho do arquivo config.txt."""
        return self._config_dir / "config.txt"
    
    def get_control_filename(self, filename: str) -> Path:
        """Retorna o caminho de um arquivo de controle."""
        return self._config_dir / filename
    
    def get_tables_filename(self, filename: str) -> Path:
        """Retorna o caminho de um arquivo de tabelas."""
        return self._tables_dir / filename
    
    def initialize_openkore_compatibility(self) -> None:
        """Inicializa compatibilidade com arquivos do OpenKore."""
        # Arquivos principais de configuração
        self.add_control_file("config.txt", "config.txt", "config_parser")
        self.add_control_file("sys.txt", "sys.txt", "config_parser")
        
        # Arquivos de controle
        self.add_control_file("mon_control.txt", "mon_control.txt", "data_parser")
        self.add_control_file("items_control.txt", "items_control.txt", "data_parser")
        self.add_control_file("pickupitems.txt", "pickupitems.txt", "data_parser")
        self.add_control_file("priority.txt", "priority.txt", "data_parser")
        self.add_control_file("avoid.txt", "avoid.txt", "data_parser")
        self.add_control_file("responses.txt", "responses.txt", "responses_parser")
        self.add_control_file("chat_resp.txt", "chat_resp.txt", "responses_parser")
        self.add_control_file("timeouts.txt", "timeouts.txt", "timeouts_parser")
        self.add_control_file("routeweights.txt", "routeweights.txt", "data_parser")
        self.add_control_file("shop.txt", "shop.txt", "shop_parser")
        self.add_control_file("buyer_shop.txt", "buyer_shop.txt", "shop_parser")
        self.add_control_file("overallAuth.txt", "overallAuth.txt", "data_parser")
        self.add_control_file("consolecolors.txt", "consolecolors.txt", "sectioned_parser")
        
        # Carrega todos os arquivos
        self.reload_all()


# Instância global compatível com OpenKore
settings = SettingsManager() 