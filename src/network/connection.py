"""
Connection Manager
==================

Gerenciador de conexões de rede para servidores RO.
"""

import asyncio
import socket
import time
from enum import Enum
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

from core.events.event_bus import EventBus
from core.logging.logger import Logger


class ConnectionState(Enum):
    """Estados da conexão."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    IN_GAME = "in_game"
    DISCONNECTING = "disconnecting"
    ERROR = "error"


@dataclass
class ServerInfo:
    """Informações do servidor."""
    name: str
    host: str
    port: int
    server_type: int = 0
    encryption: bool = False
    version: int = 0


class Connection:
    """
    Gerenciador de conexão com servidor RO.
    
    Responsável por:
    - Gerenciar estado da conexão
    - Enviar/receber dados
    - Reconexão automática
    - Monitoramento de latência
    """
    
    def __init__(self, 
                 server_info: ServerInfo,
                 event_bus: EventBus,
                 logger: Logger):
        """
        Inicializa o gerenciador de conexão.
        
        Args:
            server_info: Informações do servidor
            event_bus: Bus de eventos
            logger: Logger
        """
        self.server_info = server_info
        self.event_bus = event_bus
        self.logger = logger
        
        # Estado da conexão
        self.state = ConnectionState.DISCONNECTED
        self.socket: Optional[socket.socket] = None
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        
        # Estatísticas
        self.connect_time: Optional[float] = None
        self.last_ping_time: float = 0
        self.ping_latency: float = 0
        self.bytes_sent: int = 0
        self.bytes_received: int = 0
        self.packets_sent: int = 0
        self.packets_received: int = 0
        
        # Configurações
        self.timeout: float = 30.0
        self.keepalive_interval: float = 60.0
        self.max_reconnect_attempts: int = 5
        self.reconnect_delay: float = 5.0
        
        # Controle de reconexão
        self.reconnect_attempts: int = 0
        self.auto_reconnect: bool = True
        
        # Tasks assíncronas
        self.keepalive_task: Optional[asyncio.Task] = None
        self.receive_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> bool:
        """
        Conecta ao servidor.
        
        Returns:
            True se conectado com sucesso
        """
        if self.state in [ConnectionState.CONNECTED, ConnectionState.CONNECTING]:
            self.logger.warning("Já conectado ou conectando")
            return False
        
        self.logger.info(f"Conectando a {self.server_info.host}:{self.server_info.port}")
        self.state = ConnectionState.CONNECTING
        
        try:
            # Emite evento de início de conexão
            self.event_bus.emit('connection_starting', server=self.server_info)
            
            # Cria conexão TCP
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(
                    self.server_info.host,
                    self.server_info.port
                ),
                timeout=self.timeout
            )
            
            # Marca como conectado
            self.state = ConnectionState.CONNECTED
            self.connect_time = time.time()
            self.reconnect_attempts = 0
            
            self.logger.info(f"Conectado ao servidor {self.server_info.name}")
            
            # Inicia tarefas de background
            await self._start_background_tasks()
            
            # Emite evento de conexão estabelecida
            self.event_bus.emit('connection_established', connection=self)
            
            return True
            
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout ao conectar com {self.server_info.host}")
            self.state = ConnectionState.ERROR
            
        except Exception as e:
            self.logger.error(f"Erro ao conectar: {e}")
            self.state = ConnectionState.ERROR
        
        # Emite evento de falha na conexão
        self.event_bus.emit('connection_failed', server=self.server_info)
        
        # Tenta reconectar se habilitado
        if self.auto_reconnect:
            await self._schedule_reconnect()
        
        return False
    
    async def disconnect(self) -> None:
        """Desconecta do servidor."""
        if self.state == ConnectionState.DISCONNECTED:
            return
        
        self.logger.info("Desconectando do servidor")
        self.state = ConnectionState.DISCONNECTING
        
        # Para tarefas de background
        await self._stop_background_tasks()
        
        # Fecha conexão
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception as e:
                self.logger.error(f"Erro ao fechar conexão: {e}")
        
        self.reader = None
        self.writer = None
        self.state = ConnectionState.DISCONNECTED
        self.connect_time = None
        
        self.logger.info("Desconectado do servidor")
        
        # Emite evento de desconexão
        self.event_bus.emit('connection_closed', connection=self)
    
    async def send_data(self, data: bytes) -> bool:
        """
        Envia dados para o servidor.
        
        Args:
            data: Dados a serem enviados
            
        Returns:
            True se enviado com sucesso
        """
        if self.state != ConnectionState.CONNECTED or not self.writer:
            self.logger.error("Não conectado ao servidor")
            return False
        
        try:
            self.writer.write(data)
            await self.writer.drain()
            
            # Atualiza estatísticas
            self.bytes_sent += len(data)
            self.packets_sent += 1
            
            # Emite evento de dados enviados
            self.event_bus.emit('data_sent', data=data, size=len(data))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar dados: {e}")
            await self._handle_connection_error()
            return False
    
    async def receive_data(self, size: int) -> Optional[bytes]:
        """
        Recebe dados do servidor.
        
        Args:
            size: Número de bytes a receber
            
        Returns:
            Dados recebidos ou None se erro
        """
        if self.state != ConnectionState.CONNECTED or not self.reader:
            return None
        
        try:
            data = await asyncio.wait_for(
                self.reader.read(size),
                timeout=self.timeout
            )
            
            if not data:
                # Conexão fechada pelo servidor
                self.logger.warning("Conexão fechada pelo servidor")
                await self._handle_connection_error()
                return None
            
            # Atualiza estatísticas
            self.bytes_received += len(data)
            self.packets_received += 1
            
            # Emite evento de dados recebidos
            self.event_bus.emit('data_received', data=data, size=len(data))
            
            return data
            
        except asyncio.TimeoutError:
            self.logger.error("Timeout ao receber dados")
            await self._handle_connection_error()
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao receber dados: {e}")
            await self._handle_connection_error()
            return None
    
    async def _start_background_tasks(self) -> None:
        """Inicia tarefas de background."""
        # Keepalive task
        self.keepalive_task = asyncio.create_task(self._keepalive_loop())
        
        # Receive task
        self.receive_task = asyncio.create_task(self._receive_loop())
    
    async def _stop_background_tasks(self) -> None:
        """Para tarefas de background."""
        tasks = [self.keepalive_task, self.receive_task]
        
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.keepalive_task = None
        self.receive_task = None
    
    async def _keepalive_loop(self) -> None:
        """Loop de keepalive."""
        try:
            while self.state == ConnectionState.CONNECTED:
                await asyncio.sleep(self.keepalive_interval)
                
                if self.state == ConnectionState.CONNECTED:
                    # Envia ping se necessário
                    current_time = time.time()
                    if current_time - self.last_ping_time > self.keepalive_interval:
                        await self._send_ping()
                        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Erro no keepalive: {e}")
    
    async def _receive_loop(self) -> None:
        """Loop de recebimento de dados."""
        try:
            while self.state == ConnectionState.CONNECTED:
                # TODO: Implementar recebimento de pacotes
                # Por enquanto, apenas aguarda
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Erro no receive loop: {e}")
    
    async def _send_ping(self) -> None:
        """Envia ping para o servidor."""
        # TODO: Implementar packet de ping específico do RO
        self.last_ping_time = time.time()
        self.logger.debug("Ping enviado")
    
    async def _handle_connection_error(self) -> None:
        """Lida com erros de conexão."""
        if self.state != ConnectionState.ERROR:
            self.state = ConnectionState.ERROR
            self.logger.error("Erro de conexão detectado")
            
            # Emite evento de erro
            self.event_bus.emit('connection_error', connection=self)
            
            # Tenta reconectar se habilitado
            if self.auto_reconnect:
                await self._schedule_reconnect()
    
    async def _schedule_reconnect(self) -> None:
        """Agenda uma tentativa de reconexão."""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.logger.error("Máximo de tentativas de reconexão atingido")
            self.auto_reconnect = False
            return
        
        self.reconnect_attempts += 1
        delay = self.reconnect_delay * (2 ** (self.reconnect_attempts - 1))  # Backoff exponencial
        
        self.logger.info(f"Tentativa de reconexão {self.reconnect_attempts}/{self.max_reconnect_attempts} em {delay}s")
        
        await asyncio.sleep(delay)
        await self.connect()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da conexão.
        
        Returns:
            Dicionário com estatísticas
        """
        uptime = time.time() - self.connect_time if self.connect_time else 0
        
        return {
            'state': self.state.value,
            'server': self.server_info.name,
            'uptime': uptime,
            'ping_latency': self.ping_latency,
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received,
            'packets_sent': self.packets_sent,
            'packets_received': self.packets_received,
            'reconnect_attempts': self.reconnect_attempts
        }
    
    def is_connected(self) -> bool:
        """
        Verifica se está conectado.
        
        Returns:
            True se conectado
        """
        return self.state == ConnectionState.CONNECTED 