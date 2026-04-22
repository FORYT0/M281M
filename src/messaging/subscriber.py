"""
Subscriber - High-level subscriber interface.
"""

import logging
from typing import Callable, List, Optional, Dict, Any
from .broker import MessageBroker, Message, MessageType
from .topics import Topics
import threading

logger = logging.getLogger(__name__)


class Subscriber:
    """
    High-level subscriber for receiving messages.
    
    Provides convenient methods for subscribing to different types of messages.
    """
    
    def __init__(
        self,
        broker: MessageBroker,
        component_id: str
    ):
        """
        Initialize subscriber.
        
        Args:
            broker: Message broker instance
            component_id: Identifier for this component
        """
        self.broker = broker
        self.component_id = component_id
        self.subscriptions: List[threading.Thread] = []
    
    def subscribe(
        self,
        topics: List[str],
        callback: Callable[[Message], None],
        error_callback: Optional[Callable[[Exception], None]] = None
    ) -> threading.Thread:
        """
        Subscribe to topics.
        
        Args:
            topics: List of topics to subscribe to
            callback: Function to call for each message
            error_callback: Function to call on errors
        
        Returns:
            Subscription thread
        """
        thread = self.broker.subscribe(topics, callback, error_callback)
        self.subscriptions.append(thread)
        return thread
    
    def subscribe_features(
        self,
        symbol: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> threading.Thread:
        """
        Subscribe to feature updates.
        
        Args:
            symbol: Trading symbol
            callback: Function to call with features
        
        Returns:
            Subscription thread
        """
        topic = Topics.format(Topics.FEATURES_COMPUTED, symbol=symbol)
        
        def wrapper(msg: Message):
            if msg.message_type == MessageType.DATA:
                callback(msg.data)
        
        return self.subscribe([topic], wrapper)
    
    def subscribe_agent_signals(
        self,
        symbol: str,
        callback: Callable[[str, Dict[str, Any]], None],
        agent_id: Optional[str] = None
    ) -> threading.Thread:
        """
        Subscribe to agent signals.
        
        Args:
            symbol: Trading symbol
            callback: Function to call with (agent_id, signal)
            agent_id: Specific agent ID (None for all agents)
        
        Returns:
            Subscription thread
        """
        if agent_id:
            topic = Topics.format(Topics.AGENT_SIGNAL, symbol=symbol, agent_id=agent_id)
        else:
            # Subscribe to all agents for this symbol
            topic = f"agent.signal.{symbol}.*"
        
        def wrapper(msg: Message):
            if msg.message_type == MessageType.DATA:
                # Extract agent_id from topic
                parsed = Topics.parse(msg.topic)
                aid = parsed.get('agent_id', msg.source)
                callback(aid, msg.data)
        
        return self.subscribe([topic], wrapper)
    
    def subscribe_ensemble_signals(
        self,
        symbol: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> threading.Thread:
        """
        Subscribe to ensemble signals.
        
        Args:
            symbol: Trading symbol
            callback: Function to call with signal
        
        Returns:
            Subscription thread
        """
        topic = Topics.format(Topics.ENSEMBLE_SIGNAL, symbol=symbol)
        
        def wrapper(msg: Message):
            if msg.message_type == MessageType.DATA:
                callback(msg.data)
        
        return self.subscribe([topic], wrapper)
    
    def subscribe_orders(
        self,
        symbol: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> threading.Thread:
        """
        Subscribe to trading orders.
        
        Args:
            symbol: Trading symbol
            callback: Function to call with order
        
        Returns:
            Subscription thread
        """
        topic = Topics.format(Topics.ORCHESTRATOR_ORDER, symbol=symbol)
        
        def wrapper(msg: Message):
            if msg.message_type == MessageType.DATA:
                callback(msg.data)
        
        return self.subscribe([topic], wrapper)
    
    def subscribe_market_data(
        self,
        symbol: str,
        callback: Callable[[Dict[str, Any]], None],
        data_type: str = 'tick'
    ) -> threading.Thread:
        """
        Subscribe to market data.
        
        Args:
            symbol: Trading symbol
            callback: Function to call with market data
            data_type: Type of data ('tick', 'orderbook', 'trade')
        
        Returns:
            Subscription thread
        """
        topic_map = {
            'tick': Topics.MARKET_TICK,
            'orderbook': Topics.MARKET_ORDERBOOK,
            'trade': Topics.MARKET_TRADE
        }
        
        topic_template = topic_map.get(data_type, Topics.MARKET_TICK)
        topic = Topics.format(topic_template, symbol=symbol)
        
        def wrapper(msg: Message):
            if msg.message_type == MessageType.DATA:
                callback(msg.data)
        
        return self.subscribe([topic], wrapper)
    
    def subscribe_commands(
        self,
        callback: Callable[[str, Dict[str, Any]], None]
    ) -> threading.Thread:
        """
        Subscribe to control commands.
        
        Args:
            callback: Function to call with (command, params)
        
        Returns:
            Subscription thread
        """
        topic = Topics.format(Topics.SYSTEM_COMMAND, component_id=self.component_id)
        
        def wrapper(msg: Message):
            if msg.message_type == MessageType.COMMAND:
                command = msg.data.get('command')
                params = msg.data.get('params', {})
                callback(command, params)
        
        return self.subscribe([topic], wrapper)
    
    def subscribe_heartbeats(
        self,
        callback: Callable[[str, Dict[str, Any]], None],
        component_id: Optional[str] = None
    ) -> threading.Thread:
        """
        Subscribe to heartbeat messages.
        
        Args:
            callback: Function to call with (component_id, data)
            component_id: Specific component ID (None for all)
        
        Returns:
            Subscription thread
        """
        if component_id:
            topic = Topics.format(Topics.SYSTEM_HEARTBEAT, component_id=component_id)
        else:
            topic = "system.heartbeat.*"
        
        def wrapper(msg: Message):
            if msg.message_type == MessageType.HEARTBEAT:
                cid = msg.source or Topics.parse(msg.topic).get('part2', 'unknown')
                callback(cid, msg.data)
        
        return self.subscribe([topic], wrapper)
    
    def subscribe_errors(
        self,
        callback: Callable[[str, Dict[str, Any]], None],
        component_id: Optional[str] = None
    ) -> threading.Thread:
        """
        Subscribe to error messages.
        
        Args:
            callback: Function to call with (component_id, error_data)
            component_id: Specific component ID (None for all)
        
        Returns:
            Subscription thread
        """
        if component_id:
            topic = Topics.format(Topics.SYSTEM_ERROR, component_id=component_id)
        else:
            topic = "system.error.*"
        
        def wrapper(msg: Message):
            if msg.message_type == MessageType.ERROR:
                cid = msg.source or Topics.parse(msg.topic).get('part2', 'unknown')
                callback(cid, msg.data)
        
        return self.subscribe([topic], wrapper)
    
    def wait_all(self):
        """Wait for all subscription threads to complete."""
        for thread in self.subscriptions:
            thread.join()
