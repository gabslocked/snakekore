"""
Socket Manager
==============

Gerenciador de sockets com funcionalidades avançadas.
"""

import asyncio
import socket
import ssl
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

from core.logging.logger import Logger


@dataclass
class SocketConfig:
    """Configuração de socket."""
    family: int = socket.AF_INET
    type: int = socket.SOCK_STREAM
    timeout: float = 30.0
    buffer_size: int = 8192
    keepalive: bool = True
    nodelay: bool = True
    reuse_addr: bool = True


class SocketManager:
    """
    Gerenciador de sockets com funcionalidades avançadas.
    
    Características:
    - Configuração automática de sockets
    - Suporte SSL/TLS
    - Monitoramento de bandwidth
    - Pool de conexões
    """
    
    def __init__(self, logger: Logger):
        """
        Inicializa o gerenciador de sockets.
        
        Args:
            logger: Logger para debug
        """
        self.logger = logger
        self.active_sockets: Dict[str, socket.socket] = {}
        self.socket_stats: Dict[str, Dict[str, Any]] = {}
        
    def create_socket(self, 
                     config: Optional[SocketConfig] = None,
                     ssl_context: Optional[ssl.SSLContext] = None) -> socket.socket:
        """
        Cria um socket configurado.
        
        Args:
            config: Configuração do socket
            ssl_context: Contexto SSL (opcional)
            
        Returns:
            Socket configurado
        """
        if config is None:
            config = SocketConfig()
        
        # Cria socket
        sock = socket.socket(config.family, config.type)
        
        # Configura opções
        if config.reuse_addr:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        if config.keepalive:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        
        if config.nodelay and config.type == socket.SOCK_STREAM:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        
        # Configura timeout
        sock.settimeout(config.timeout)
        
        # Aplica SSL se necessário
        if ssl_context:
            sock = ssl_context.wrap_socket(sock)
        
        self.logger.debug(f"Socket criado com configuração: {config}")
        
        return sock
    
    async def create_connection(self,
                              host: str,
                              port: int,
                              config: Optional[SocketConfig] = None,
                              ssl_context: Optional[ssl.SSLContext] = None) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """
        Cria uma conexão assíncrona.
        
        Args:
            host: Endereço do servidor
            port: Porta do servidor
            config: Configuração do socket
            ssl_context: Contexto SSL
            
        Returns:
            Tuple com reader e writer
        """
        if config is None:
            config = SocketConfig()
        
        # Cria socket
        sock = self.create_socket(config, ssl_context)
        
        try:
            # Conecta
            if ssl_context:
                reader, writer = await asyncio.open_connection(
                    host, port,
                    ssl=ssl_context,
                    sock=sock
                )
            else:
                reader, writer = await asyncio.open_connection(
                    host, port,
                    sock=sock
                )
            
            # Registra socket
            socket_id = f"{host}:{port}"
            self.active_sockets[socket_id] = sock
            self.socket_stats[socket_id] = {
                'host': host,
                'port': port,
                'created_at': asyncio.get_event_loop().time(),
                'bytes_sent': 0,
                'bytes_received': 0
            }
            
            self.logger.info(f"Conexão estabelecida com {host}:{port}")
            
            return reader, writer
            
        except Exception as e:
            sock.close()
            self.logger.error(f"Erro ao conectar com {host}:{port}: {e}")
            raise
    
    def close_socket(self, socket_id: str) -> None:
        """
        Fecha um socket.
        
        Args:
            socket_id: ID do socket
        """
        if socket_id in self.active_sockets:
            sock = self.active_sockets[socket_id]
            try:
                sock.close()
            except Exception as e:
                self.logger.error(f"Erro ao fechar socket {socket_id}: {e}")
            
            del self.active_sockets[socket_id]
            if socket_id in self.socket_stats:
                del self.socket_stats[socket_id]
            
            self.logger.debug(f"Socket {socket_id} fechado")
    
    def close_all_sockets(self) -> None:
        """Fecha todos os sockets ativos."""
        socket_ids = list(self.active_sockets.keys())
        for socket_id in socket_ids:
            self.close_socket(socket_id)
        
        self.logger.info("Todos os sockets fechados")
    
    def get_socket_info(self, socket_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações de um socket.
        
        Args:
            socket_id: ID do socket
            
        Returns:
            Informações do socket ou None
        """
        return self.socket_stats.get(socket_id)
    
    def get_all_sockets_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtém informações de todos os sockets.
        
        Returns:
            Dicionário com informações de todos os sockets
        """
        return self.socket_stats.copy()
    
    def update_stats(self, socket_id: str, bytes_sent: int = 0, bytes_received: int = 0) -> None:
        """
        Atualiza estatísticas de um socket.
        
        Args:
            socket_id: ID do socket
            bytes_sent: Bytes enviados
            bytes_received: Bytes recebidos
        """
        if socket_id in self.socket_stats:
            self.socket_stats[socket_id]['bytes_sent'] += bytes_sent
            self.socket_stats[socket_id]['bytes_received'] += bytes_received
    
    def create_ssl_context(self, 
                          verify_mode: ssl.VerifyMode = ssl.CERT_NONE,
                          check_hostname: bool = False) -> ssl.SSLContext:
        """
        Cria um contexto SSL.
        
        Args:
            verify_mode: Modo de verificação
            check_hostname: Se deve verificar hostname
            
        Returns:
            Contexto SSL configurado
        """
        context = ssl.create_default_context()
        context.verify_mode = verify_mode
        context.check_hostname = check_hostname
        
        self.logger.debug("Contexto SSL criado")
        
        return context 