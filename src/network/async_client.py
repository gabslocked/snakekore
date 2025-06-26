"""
Async Client
============

Cliente assíncrono para comunicação com servidores RO.
"""

import asyncio
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

from connection import Connection, ServerInfo, ConnectionState
from socket_manager import SocketManager, SocketConfig
from core.events.event_bus import EventBus
from core.logging.logger import Logger


@dataclass
class ClientConfig:
    """Configuração do cliente."""
    auto_reconnect: bool = True
    max_reconnect_attempts: int = 5
    reconnect_delay: float = 5.0
    keepalive_interval: float = 60.0
    timeout: float = 30.0
    buffer_size: int = 8192


class AsyncClient:
    """
    Cliente assíncrono para servidores RO.
    
    Características:
    - Gerenciamento automático de conexão
    - Reconexão automática
    - Pool de conexões
    - Event-driven architecture
    """
    
    def __init__(self, 
                 event_bus: EventBus,
                 logger: Logger,
                 config: Optional[ClientConfig] = None):
        """
        Inicializa o cliente assíncrono.
        
        Args:
            event_bus: Bus de eventos
            logger: Logger
            config: Configuração do cliente
        """
        self.event_bus = event_bus
        self.logger = logger
        self.config = config or ClientConfig()
        
        # Componentes
        self.socket_manager = SocketManager(logger)
        self.connection: Optional[Connection] = None
        
        # Estado
        self.is_running = False
        self.current_server: Optional[ServerInfo] = None
        
        # Tasks
        self.main_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.message_handlers: Dict[str, Callable] = {}
        
        # Registra handlers de eventos
        self._register_event_handlers()
    
    def _register_event_handlers(self) -> None:
        """Registra handlers de eventos."""
        self.event_bus.subscribe('connection_established', self._on_connection_established)
        self.event_bus.subscribe('connection_failed', self._on_connection_failed)
        self.event_bus.subscribe('connection_closed', self._on_connection_closed)
        self.event_bus.subscribe('connection_error', self._on_connection_error)
        self.event_bus.subscribe('data_received', self._on_data_received)
    
    async def connect_to_server(self, server_info: ServerInfo) -> bool:
        """
        Conecta a um servidor.
        
        Args:
            server_info: Informações do servidor
            
        Returns:
            True se conectado com sucesso
        """
        if self.is_running:
            self.logger.warning("Cliente já está rodando")
            return False
        
        self.current_server = server_info
        self.logger.info(f"Iniciando conexão com servidor {server_info.name}")
        
        # Cria conexão
        self.connection = Connection(
            server_info=server_info,
            event_bus=self.event_bus,
            logger=self.logger
        )
        
        # Configura parâmetros da conexão
        self.connection.auto_reconnect = self.config.auto_reconnect
        self.connection.max_reconnect_attempts = self.config.max_reconnect_attempts
        self.connection.reconnect_delay = self.config.reconnect_delay
        self.connection.keepalive_interval = self.config.keepalive_interval
        self.connection.timeout = self.config.timeout
        
        # Tenta conectar
        success = await self.connection.connect()
        
        if success:
            self.is_running = True
            self.main_task = asyncio.create_task(self._main_loop())
        
        return success
    
    async def disconnect(self) -> None:
        """Desconecta do servidor."""
        if not self.is_running:
            return
        
        self.logger.info("Desconectando do servidor")
        self.is_running = False
        
        # Para task principal
        if self.main_task and not self.main_task.done():
            self.main_task.cancel()
            try:
                await self.main_task
            except asyncio.CancelledError:
                pass
        
        # Fecha conexão
        if self.connection:
            await self.connection.disconnect()
            self.connection = None
        
        # Fecha todos os sockets
        self.socket_manager.close_all_sockets()
        
        self.current_server = None
        self.logger.info("Desconectado do servidor")
    
    async def send_data(self, data: bytes) -> bool:
        """
        Envia dados para o servidor.
        
        Args:
            data: Dados a serem enviados
            
        Returns:
            True se enviado com sucesso
        """
        if not self.connection or not self.connection.is_connected():
            self.logger.error("Não conectado ao servidor")
            return False
        
        return await self.connection.send_data(data)
    
    def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """
        Registra um handler para um tipo de mensagem.
        
        Args:
            message_type: Tipo da mensagem
            handler: Função handler
        """
        self.message_handlers[message_type] = handler
        self.logger.debug(f"Handler registrado para {message_type}")
    
    def unregister_message_handler(self, message_type: str) -> None:
        """
        Remove um handler de mensagem.
        
        Args:
            message_type: Tipo da mensagem
        """
        if message_type in self.message_handlers:
            del self.message_handlers[message_type]
            self.logger.debug(f"Handler removido para {message_type}")
    
    async def _main_loop(self) -> None:
        """Loop principal do cliente."""
        try:
            while self.is_running:
                # Processa eventos e mensagens
                await asyncio.sleep(0.01)  # Pequena pausa para não sobrecarregar CPU
                
                # TODO: Processar fila de mensagens
                # TODO: Processar timeouts
                # TODO: Processar keepalive
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Erro no loop principal: {e}")
    
    def _on_connection_established(self, event) -> None:
        """Handler para conexão estabelecida."""
        self.logger.info("Conexão estabelecida com sucesso")
        
        # TODO: Iniciar processo de autenticação
        # TODO: Enviar packets iniciais
    
    def _on_connection_failed(self, event) -> None:
        """Handler para falha na conexão."""
        self.logger.error("Falha ao estabelecer conexão")
        self.is_running = False
    
    def _on_connection_closed(self, event) -> None:
        """Handler para conexão fechada."""
        self.logger.info("Conexão fechada")
        self.is_running = False
    
    def _on_connection_error(self, event) -> None:
        """Handler para erro de conexão."""
        self.logger.error("Erro de conexão detectado")
        
        # TODO: Implementar lógica de recuperação
    
    def _on_data_received(self, event) -> None:
        """Handler para dados recebidos."""
        data = event.kwargs.get('data')
        if data:
            # TODO: Processar dados recebidos
            # TODO: Parse de packets
            # TODO: Chamar handlers apropriados
            self.logger.debug(f"Dados recebidos: {len(data)} bytes")
    
    def get_connection_stats(self) -> Optional[Dict[str, Any]]:
        """
        Obtém estatísticas da conexão.
        
        Returns:
            Estatísticas da conexão ou None
        """
        if self.connection:
            return self.connection.get_stats()
        return None
    
    def is_connected(self) -> bool:
        """
        Verifica se está conectado.
        
        Returns:
            True se conectado
        """
        return (self.connection is not None and 
                self.connection.is_connected() and 
                self.is_running) 