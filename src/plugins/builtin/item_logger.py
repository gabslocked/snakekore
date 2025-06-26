"""
Item Logger Plugin
==================

Plugin para registrar drops, loots e transações de itens.
Similar ao itemsGather do OpenKore.
"""

import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from base_plugin import BasePlugin, PluginInfo, PluginType


@dataclass
class ItemEvent:
    """Evento de item."""
    timestamp: float
    event_type: str  # drop, pickup, sold, bought, traded, etc.
    item_name: str
    item_id: int
    quantity: int
    map_name: str
    coordinates: tuple
    monster_name: Optional[str] = None
    npc_name: Optional[str] = None
    player_name: Optional[str] = None
    price: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return asdict(self)


class ItemLoggerPlugin(BasePlugin):
    """
    Plugin de log de itens.
    
    Funcionalidades:
    - Log de drops de monstros
    - Log de pickups
    - Log de vendas/compras
    - Log de trades
    - Estatísticas de farming
    - Exportação de dados
    """
    
    def _setup_plugin_info(self) -> None:
        """Configura informações do plugin."""
        self.info = PluginInfo(
            name="ItemLogger",
            version="1.0.0",
            description="Logger de drops, loots e transações de itens",
            author="PythonKore Team",
            plugin_type=PluginType.UTILITY,
            dependencies=[],
            min_pythonkore_version="1.0.0",
            tags=["logging", "items", "farming", "statistics"]
        )
    
    def _setup_default_config(self) -> None:
        """Configura valores padrão."""
        super()._setup_default_config()
        
        self.config.set_defaults({
            'enabled': True,
            'log_drops': True,
            'log_pickups': True,
            'log_sales': True,
            'log_purchases': True,
            'log_trades': True,
            'log_file': 'item_log.json',
            'auto_save_interval': 300,  # 5 minutos
            'max_log_size': 10000,      # Máximo de eventos
            'filter_worthless': False,  # Filtrar itens sem valor
            'min_item_value': 0,        # Valor mínimo para log
            'blacklist_items': [],      # Itens a ignorar
            'whitelist_items': [],      # Apenas estes itens (vazio = todos)
            'group_by_session': True,   # Agrupar por sessão
            'include_coordinates': True,
            'include_monster_info': True
        })
        
        # Estado interno
        self.item_events: List[ItemEvent] = []
        self.session_start: float = time.time()
        self.last_save: float = time.time()
        
        # Estatísticas da sessão
        self.session_stats = {
            'drops_count': 0,
            'pickups_count': 0,
            'sales_count': 0,
            'purchases_count': 0,
            'trades_count': 0,
            'total_zeny_gained': 0,
            'total_zeny_spent': 0,
            'unique_items': set(),
            'monsters_killed': {},
            'maps_visited': set()
        }
    
    def on_load(self) -> bool:
        """Carrega o plugin."""
        # Carrega log existente
        self._load_log_file()
        return True
    
    def on_activate(self) -> bool:
        """Ativa o plugin."""
        # Registra handlers de eventos
        self.add_event_handler('item_dropped', self._handle_item_dropped)
        self.add_event_handler('item_picked_up', self._handle_item_picked_up)
        self.add_event_handler('item_sold', self._handle_item_sold)
        self.add_event_handler('item_bought', self._handle_item_bought)
        self.add_event_handler('item_traded', self._handle_item_traded)
        self.add_event_handler('monster_killed', self._handle_monster_killed)
        self.add_event_handler('map_changed', self._handle_map_changed)
        
        # Timer para auto-save
        self.add_event_handler('timer_tick', self._handle_timer_tick)
        
        self.logger.info("ItemLogger ativado")
        return True
    
    def on_deactivate(self) -> None:
        """Desativa o plugin."""
        # Salva dados antes de desativar
        self._save_log_file()
        self.logger.info("ItemLogger desativado")
    
    def _handle_item_dropped(self, event_data: Dict[str, Any]) -> None:
        """Processa drop de item."""
        if not self.config.get('log_drops', True):
            return
        
        item_event = ItemEvent(
            timestamp=time.time(),
            event_type='drop',
            item_name=event_data.get('item_name', ''),
            item_id=event_data.get('item_id', 0),
            quantity=event_data.get('quantity', 1),
            map_name=event_data.get('map_name', ''),
            coordinates=event_data.get('coordinates', (0, 0)),
            monster_name=event_data.get('monster_name')
        )
        
        if self._should_log_item(item_event):
            self._add_item_event(item_event)
            self.session_stats['drops_count'] += 1
    
    def _handle_item_picked_up(self, event_data: Dict[str, Any]) -> None:
        """Processa pickup de item."""
        if not self.config.get('log_pickups', True):
            return
        
        item_event = ItemEvent(
            timestamp=time.time(),
            event_type='pickup',
            item_name=event_data.get('item_name', ''),
            item_id=event_data.get('item_id', 0),
            quantity=event_data.get('quantity', 1),
            map_name=event_data.get('map_name', ''),
            coordinates=event_data.get('coordinates', (0, 0))
        )
        
        if self._should_log_item(item_event):
            self._add_item_event(item_event)
            self.session_stats['pickups_count'] += 1
            self.session_stats['unique_items'].add(item_event.item_name)
    
    def _handle_item_sold(self, event_data: Dict[str, Any]) -> None:
        """Processa venda de item."""
        if not self.config.get('log_sales', True):
            return
        
        item_event = ItemEvent(
            timestamp=time.time(),
            event_type='sold',
            item_name=event_data.get('item_name', ''),
            item_id=event_data.get('item_id', 0),
            quantity=event_data.get('quantity', 1),
            map_name=event_data.get('map_name', ''),
            coordinates=event_data.get('coordinates', (0, 0)),
            npc_name=event_data.get('npc_name'),
            price=event_data.get('price', 0)
        )
        
        if self._should_log_item(item_event):
            self._add_item_event(item_event)
            self.session_stats['sales_count'] += 1
            self.session_stats['total_zeny_gained'] += item_event.price or 0
    
    def _handle_item_bought(self, event_data: Dict[str, Any]) -> None:
        """Processa compra de item."""
        if not self.config.get('log_purchases', True):
            return
        
        item_event = ItemEvent(
            timestamp=time.time(),
            event_type='bought',
            item_name=event_data.get('item_name', ''),
            item_id=event_data.get('item_id', 0),
            quantity=event_data.get('quantity', 1),
            map_name=event_data.get('map_name', ''),
            coordinates=event_data.get('coordinates', (0, 0)),
            npc_name=event_data.get('npc_name'),
            price=event_data.get('price', 0)
        )
        
        if self._should_log_item(item_event):
            self._add_item_event(item_event)
            self.session_stats['purchases_count'] += 1
            self.session_stats['total_zeny_spent'] += item_event.price or 0
    
    def _handle_item_traded(self, event_data: Dict[str, Any]) -> None:
        """Processa trade de item."""
        if not self.config.get('log_trades', True):
            return
        
        item_event = ItemEvent(
            timestamp=time.time(),
            event_type='traded',
            item_name=event_data.get('item_name', ''),
            item_id=event_data.get('item_id', 0),
            quantity=event_data.get('quantity', 1),
            map_name=event_data.get('map_name', ''),
            coordinates=event_data.get('coordinates', (0, 0)),
            player_name=event_data.get('player_name')
        )
        
        if self._should_log_item(item_event):
            self._add_item_event(item_event)
            self.session_stats['trades_count'] += 1
    
    def _handle_monster_killed(self, event_data: Dict[str, Any]) -> None:
        """Processa morte de monstro."""
        monster_name = event_data.get('monster_name', '')
        if monster_name:
            if monster_name not in self.session_stats['monsters_killed']:
                self.session_stats['monsters_killed'][monster_name] = 0
            self.session_stats['monsters_killed'][monster_name] += 1
    
    def _handle_map_changed(self, event_data: Dict[str, Any]) -> None:
        """Processa mudança de mapa."""
        map_name = event_data.get('map_name', '')
        if map_name:
            self.session_stats['maps_visited'].add(map_name)
    
    def _handle_timer_tick(self, event_data: Dict[str, Any]) -> None:
        """Processa tick do timer."""
        current_time = time.time()
        auto_save_interval = self.config.get('auto_save_interval', 300)
        
        if current_time - self.last_save >= auto_save_interval:
            self._save_log_file()
            self.last_save = current_time
    
    def _should_log_item(self, item_event: ItemEvent) -> bool:
        """
        Verifica se item deve ser logado.
        
        Args:
            item_event: Evento do item
            
        Returns:
            True se deve ser logado
        """
        # Verifica blacklist
        blacklist = self.config.get('blacklist_items', [])
        if item_event.item_name.lower() in [item.lower() for item in blacklist]:
            return False
        
        # Verifica whitelist (se definida)
        whitelist = self.config.get('whitelist_items', [])
        if whitelist and item_event.item_name.lower() not in [item.lower() for item in whitelist]:
            return False
        
        # Verifica valor mínimo
        if self.config.get('filter_worthless', False):
            min_value = self.config.get('min_item_value', 0)
            item_value = self._get_item_value(item_event.item_id)
            if item_value < min_value:
                return False
        
        return True
    
    def _get_item_value(self, item_id: int) -> int:
        """
        Obtém valor do item.
        
        Args:
            item_id: ID do item
            
        Returns:
            Valor do item
        """
        # TODO: Integrar com sistema de itens/database
        return 0
    
    def _add_item_event(self, item_event: ItemEvent) -> None:
        """
        Adiciona evento de item.
        
        Args:
            item_event: Evento a adicionar
        """
        self.item_events.append(item_event)
        
        # Limita tamanho do log
        max_size = self.config.get('max_log_size', 10000)
        if len(self.item_events) > max_size:
            # Remove eventos mais antigos
            self.item_events = self.item_events[-max_size:]
        
        self.logger.debug(f"Item event: {item_event.event_type} - {item_event.item_name} x{item_event.quantity}")
    
    def _load_log_file(self) -> None:
        """Carrega arquivo de log."""
        log_file = Path(self.config.get('log_file', 'item_log.json'))
        
        try:
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Carrega eventos
                for event_data in data.get('events', []):
                    item_event = ItemEvent(**event_data)
                    self.item_events.append(item_event)
                
                self.logger.info(f"Carregados {len(self.item_events)} eventos do log")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar log de itens: {e}")
    
    def _save_log_file(self) -> None:
        """Salva arquivo de log."""
        log_file = Path(self.config.get('log_file', 'item_log.json'))
        
        try:
            # Prepara dados
            data = {
                'metadata': {
                    'version': '1.0',
                    'created': datetime.now().isoformat(),
                    'session_start': datetime.fromtimestamp(self.session_start).isoformat(),
                    'total_events': len(self.item_events)
                },
                'session_stats': {
                    **self.session_stats,
                    'unique_items': list(self.session_stats['unique_items']),
                    'maps_visited': list(self.session_stats['maps_visited'])
                },
                'events': [event.to_dict() for event in self.item_events]
            }
            
            # Salva arquivo
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Log salvo: {len(self.item_events)} eventos")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar log de itens: {e}")
    
    # Métodos de consulta e análise
    def get_events_by_type(self, event_type: str) -> List[ItemEvent]:
        """Obtém eventos por tipo."""
        return [event for event in self.item_events if event.event_type == event_type]
    
    def get_events_by_item(self, item_name: str) -> List[ItemEvent]:
        """Obtém eventos por item."""
        return [event for event in self.item_events 
                if event.item_name.lower() == item_name.lower()]
    
    def get_events_by_monster(self, monster_name: str) -> List[ItemEvent]:
        """Obtém eventos por monstro."""
        return [event for event in self.item_events 
                if event.monster_name and event.monster_name.lower() == monster_name.lower()]
    
    def get_events_by_map(self, map_name: str) -> List[ItemEvent]:
        """Obtém eventos por mapa."""
        return [event for event in self.item_events 
                if event.map_name.lower() == map_name.lower()]
    
    def get_events_in_timerange(self, start_time: float, end_time: float) -> List[ItemEvent]:
        """Obtém eventos em período."""
        return [event for event in self.item_events 
                if start_time <= event.timestamp <= end_time]
    
    def get_item_statistics(self) -> Dict[str, Any]:
        """Obtém estatísticas de itens."""
        stats = {
            'total_events': len(self.item_events),
            'by_type': {},
            'by_item': {},
            'by_monster': {},
            'by_map': {},
            'session': {
                **self.session_stats,
                'unique_items': list(self.session_stats['unique_items']),
                'maps_visited': list(self.session_stats['maps_visited']),
                'duration_hours': (time.time() - self.session_start) / 3600
            }
        }
        
        # Estatísticas por tipo
        for event in self.item_events:
            event_type = event.event_type
            if event_type not in stats['by_type']:
                stats['by_type'][event_type] = 0
            stats['by_type'][event_type] += 1
            
            # Por item
            if event.item_name not in stats['by_item']:
                stats['by_item'][event.item_name] = {'count': 0, 'quantity': 0}
            stats['by_item'][event.item_name]['count'] += 1
            stats['by_item'][event.item_name]['quantity'] += event.quantity
            
            # Por monstro (apenas drops)
            if event.monster_name and event.event_type == 'drop':
                if event.monster_name not in stats['by_monster']:
                    stats['by_monster'][event.monster_name] = 0
                stats['by_monster'][event.monster_name] += 1
            
            # Por mapa
            if event.map_name not in stats['by_map']:
                stats['by_map'][event.map_name] = 0
            stats['by_map'][event.map_name] += 1
        
        return stats
    
    def export_csv(self, filename: str) -> bool:
        """
        Exporta dados para CSV.
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            True se exportado com sucesso
        """
        try:
            import csv
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if not self.item_events:
                    return True
                
                writer = csv.DictWriter(f, fieldnames=self.item_events[0].to_dict().keys())
                writer.writeheader()
                
                for event in self.item_events:
                    writer.writerow(event.to_dict())
            
            self.logger.info(f"Dados exportados para {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao exportar CSV: {e}")
            return False
    
    def clear_log(self) -> None:
        """Limpa log de eventos."""
        self.item_events.clear()
        self.session_stats = {
            'drops_count': 0,
            'pickups_count': 0,
            'sales_count': 0,
            'purchases_count': 0,
            'trades_count': 0,
            'total_zeny_gained': 0,
            'total_zeny_spent': 0,
            'unique_items': set(),
            'monsters_killed': {},
            'maps_visited': set()
        }
        self.session_start = time.time()
        self.logger.info("Log de itens limpo")
    
    def get_summary_report(self) -> str:
        """Gera relatório resumido."""
        stats = self.get_item_statistics()
        session = stats['session']
        
        report = f"""
📊 RELATÓRIO DE ITENS - ItemLogger
{'='*50}

⏱️ SESSÃO ATUAL:
   • Duração: {session['duration_hours']:.1f} horas
   • Início: {datetime.fromtimestamp(self.session_start).strftime('%d/%m/%Y %H:%M:%S')}

📦 EVENTOS:
   • Drops: {session['drops_count']}
   • Pickups: {session['pickups_count']}
   • Vendas: {session['sales_count']}
   • Compras: {session['purchases_count']}
   • Trades: {session['trades_count']}

💰 ECONOMIA:
   • Zeny ganho: {session['total_zeny_gained']:,}
   • Zeny gasto: {session['total_zeny_spent']:,}
   • Lucro líquido: {session['total_zeny_gained'] - session['total_zeny_spent']:,}

🎯 FARMING:
   • Itens únicos: {len(session['unique_items'])}
   • Mapas visitados: {len(session['maps_visited'])}
   • Monstros mortos: {sum(session['monsters_killed'].values())}

📈 TOP ITENS:
"""
        
        # Top 5 itens mais coletados
        top_items = sorted(stats['by_item'].items(), 
                          key=lambda x: x[1]['quantity'], reverse=True)[:5]
        
        for i, (item_name, data) in enumerate(top_items, 1):
            report += f"   {i}. {item_name}: {data['quantity']} unidades\n"
        
        return report 