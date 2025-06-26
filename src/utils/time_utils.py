"""
Time Utils
==========

Utilidades de tempo para o PythonKore.
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Union


class TimeUtils:
    """
    Utilidades de tempo.
    
    Funcionalidades:
    - Conversões de tempo
    - Timers e cronômetros
    - Formatação de tempo
    - Cálculos de duração
    """
    
    @staticmethod
    def now() -> float:
        """
        Obtém timestamp atual.
        
        Returns:
            Timestamp em segundos
        """
        return time.time()
    
    @staticmethod
    def now_datetime() -> datetime:
        """
        Obtém datetime atual.
        
        Returns:
            Datetime atual
        """
        return datetime.now()
    
    @staticmethod
    def now_utc() -> datetime:
        """
        Obtém datetime UTC atual.
        
        Returns:
            Datetime UTC atual
        """
        return datetime.now(timezone.utc)
    
    @staticmethod
    def timestamp_to_datetime(timestamp: float) -> datetime:
        """
        Converte timestamp para datetime.
        
        Args:
            timestamp: Timestamp em segundos
            
        Returns:
            Datetime correspondente
        """
        return datetime.fromtimestamp(timestamp)
    
    @staticmethod
    def datetime_to_timestamp(dt: datetime) -> float:
        """
        Converte datetime para timestamp.
        
        Args:
            dt: Datetime a converter
            
        Returns:
            Timestamp em segundos
        """
        return dt.timestamp()
    
    @staticmethod
    def format_timestamp(timestamp: float, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Formata timestamp.
        
        Args:
            timestamp: Timestamp em segundos
            format_str: Formato de saída
            
        Returns:
            String formatada
        """
        dt = TimeUtils.timestamp_to_datetime(timestamp)
        return dt.strftime(format_str)
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Formata duração em segundos.
        
        Args:
            seconds: Duração em segundos
            
        Returns:
            String formatada (ex: "1h 30m 45s")
        """
        if seconds < 0:
            return "0s"
        
        # Converte para inteiro para facilitar cálculos
        total_seconds = int(seconds)
        
        if total_seconds < 60:
            return f"{total_seconds}s"
        
        minutes = total_seconds // 60
        remaining_seconds = total_seconds % 60
        
        if minutes < 60:
            if remaining_seconds > 0:
                return f"{minutes}m {remaining_seconds}s"
            else:
                return f"{minutes}m"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if hours < 24:
            parts = [f"{hours}h"]
            if remaining_minutes > 0:
                parts.append(f"{remaining_minutes}m")
            if remaining_seconds > 0:
                parts.append(f"{remaining_seconds}s")
            return " ".join(parts)
        
        days = hours // 24
        remaining_hours = hours % 24
        
        parts = [f"{days}d"]
        if remaining_hours > 0:
            parts.append(f"{remaining_hours}h")
        if remaining_minutes > 0:
            parts.append(f"{remaining_minutes}m")
        
        return " ".join(parts)
    
    @staticmethod
    def parse_duration(duration_str: str) -> float:
        """
        Converte string de duração para segundos.
        
        Args:
            duration_str: String de duração (ex: "1h 30m 45s")
            
        Returns:
            Duração em segundos
        """
        import re
        
        if not duration_str:
            return 0.0
        
        total_seconds = 0.0
        
        # Padrões de tempo
        patterns = {
            r'(\d+(?:\.\d+)?)d': 24 * 60 * 60,  # dias
            r'(\d+(?:\.\d+)?)h': 60 * 60,       # horas
            r'(\d+(?:\.\d+)?)m': 60,            # minutos
            r'(\d+(?:\.\d+)?)s': 1              # segundos
        }
        
        for pattern, multiplier in patterns.items():
            matches = re.findall(pattern, duration_str.lower())
            for match in matches:
                total_seconds += float(match) * multiplier
        
        return total_seconds
    
    @staticmethod
    def elapsed_time(start_time: float) -> float:
        """
        Calcula tempo decorrido desde um timestamp.
        
        Args:
            start_time: Timestamp inicial
            
        Returns:
            Tempo decorrido em segundos
        """
        return TimeUtils.now() - start_time
    
    @staticmethod
    def sleep(seconds: float) -> None:
        """
        Pausa execução por um tempo.
        
        Args:
            seconds: Tempo de pausa em segundos
        """
        time.sleep(seconds)
    
    @staticmethod
    def is_timeout(start_time: float, timeout: float) -> bool:
        """
        Verifica se houve timeout.
        
        Args:
            start_time: Timestamp inicial
            timeout: Timeout em segundos
            
        Returns:
            True se houve timeout
        """
        return TimeUtils.elapsed_time(start_time) >= timeout
    
    @staticmethod
    def remaining_time(start_time: float, duration: float) -> float:
        """
        Calcula tempo restante.
        
        Args:
            start_time: Timestamp inicial
            duration: Duração total
            
        Returns:
            Tempo restante em segundos (pode ser negativo)
        """
        elapsed = TimeUtils.elapsed_time(start_time)
        return duration - elapsed
    
    @staticmethod
    def add_seconds(timestamp: float, seconds: float) -> float:
        """
        Adiciona segundos a um timestamp.
        
        Args:
            timestamp: Timestamp base
            seconds: Segundos a adicionar
            
        Returns:
            Novo timestamp
        """
        return timestamp + seconds
    
    @staticmethod
    def add_minutes(timestamp: float, minutes: float) -> float:
        """
        Adiciona minutos a um timestamp.
        
        Args:
            timestamp: Timestamp base
            minutes: Minutos a adicionar
            
        Returns:
            Novo timestamp
        """
        return timestamp + (minutes * 60)
    
    @staticmethod
    def add_hours(timestamp: float, hours: float) -> float:
        """
        Adiciona horas a um timestamp.
        
        Args:
            timestamp: Timestamp base
            hours: Horas a adicionar
            
        Returns:
            Novo timestamp
        """
        return timestamp + (hours * 60 * 60)
    
    @staticmethod
    def add_days(timestamp: float, days: float) -> float:
        """
        Adiciona dias a um timestamp.
        
        Args:
            timestamp: Timestamp base
            days: Dias a adicionar
            
        Returns:
            Novo timestamp
        """
        return timestamp + (days * 24 * 60 * 60)
    
    @staticmethod
    def get_age(timestamp: float) -> str:
        """
        Obtém "idade" de um timestamp (tempo decorrido formatado).
        
        Args:
            timestamp: Timestamp a verificar
            
        Returns:
            Idade formatada (ex: "2 hours ago")
        """
        elapsed = TimeUtils.elapsed_time(timestamp)
        
        if elapsed < 60:
            return f"{int(elapsed)} seconds ago"
        elif elapsed < 3600:
            minutes = int(elapsed / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif elapsed < 86400:
            hours = int(elapsed / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(elapsed / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"


class Timer:
    """
    Classe para cronometrar operações.
    """
    
    def __init__(self):
        """Inicializa timer."""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.paused_time: float = 0.0
        self.pause_start: Optional[float] = None
        self.is_running = False
        self.is_paused = False
    
    def start(self) -> None:
        """Inicia o timer."""
        self.start_time = TimeUtils.now()
        self.end_time = None
        self.paused_time = 0.0
        self.pause_start = None
        self.is_running = True
        self.is_paused = False
    
    def stop(self) -> float:
        """
        Para o timer.
        
        Returns:
            Tempo decorrido em segundos
        """
        if not self.is_running:
            return 0.0
        
        self.end_time = TimeUtils.now()
        self.is_running = False
        
        if self.is_paused and self.pause_start:
            self.paused_time += TimeUtils.now() - self.pause_start
            self.is_paused = False
        
        return self.elapsed()
    
    def pause(self) -> None:
        """Pausa o timer."""
        if self.is_running and not self.is_paused:
            self.pause_start = TimeUtils.now()
            self.is_paused = True
    
    def resume(self) -> None:
        """Resume o timer."""
        if self.is_running and self.is_paused and self.pause_start:
            self.paused_time += TimeUtils.now() - self.pause_start
            self.pause_start = None
            self.is_paused = False
    
    def reset(self) -> None:
        """Reseta o timer."""
        self.start_time = None
        self.end_time = None
        self.paused_time = 0.0
        self.pause_start = None
        self.is_running = False
        self.is_paused = False
    
    def elapsed(self) -> float:
        """
        Obtém tempo decorrido.
        
        Returns:
            Tempo decorrido em segundos
        """
        if not self.start_time:
            return 0.0
        
        if self.end_time:
            # Timer parado
            total_time = self.end_time - self.start_time
        else:
            # Timer ainda rodando
            total_time = TimeUtils.now() - self.start_time
        
        # Subtrai tempo pausado
        paused = self.paused_time
        if self.is_paused and self.pause_start:
            paused += TimeUtils.now() - self.pause_start
        
        return max(0.0, total_time - paused)
    
    def elapsed_formatted(self) -> str:
        """
        Obtém tempo decorrido formatado.
        
        Returns:
            Tempo formatado
        """
        return TimeUtils.format_duration(self.elapsed())
    
    def __str__(self) -> str:
        """Representação string."""
        status = "running" if self.is_running else "stopped"
        if self.is_paused:
            status = "paused"
        
        return f"Timer({status}, {self.elapsed_formatted()})"
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop() 