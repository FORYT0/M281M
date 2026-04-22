"""
Publisher - High-level publisher interface.
"""

import logging
from typing import Any, Dict, Optional
from .broker import MessageBroker, MessageType
from .topics import Topics

logger = logging.getLogger(__name__)


class Publisher:
    """
    High-level publisher for sending messages.
    
    Provides convenient methods for publishing different types of messages.
    """
    
    def __init__(
        self,
        broker: MessageBroker,
        component_id: str,
        default_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize publisher.
        
        Args:
            broker: Message broker instance
            component_id: Identifier for this component
            default_metadata: Default metadata to include in all messages
        """
        self.broker = broker
        self.component_id = component_id
        self.default_metadata = default_metadata or {}
    
    def publish_data(
        self,
        topic: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Publish a data message.
        
        Args:
            topic: Topic to publish to
            data: Message data
            metadata: Additional metadata
        
        Returns:
            Message ID
        """
        combined_metadata = {**self.default_metadata, **(metadata or {})}
        
        return self.broker.publish(
            topic=topic,
            data=data,
            message_type=MessageType.DATA,
            source=self.component_id,
            metadata=combined_metadata
        )
    
    def publish_event(
        self,
        topic: str,
        event_type: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Publish an event message.
        
        Args:
            topic: Topic to publish to
            event_type: Type of event
            data: Event data
            metadata: Additional metadata
        
        Returns:
            Message ID
        """
        combined_metadata = {
            **self.default_metadata,
            **(metadata or {}),
            'event_type': event_type
        }
        
        return self.broker.publish(
            topic=topic,
            data=data,
            message_type=MessageType.EVENT,
            source=self.component_id,
            metadata=combined_metadata
        )
    
    def publish_command(
        self,
        topic: str,
        command: str,
        params: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Publish a command message.
        
        Args:
            topic: Topic to publish to
            command: Command name
            params: Command parameters
            metadata: Additional metadata
        
        Returns:
            Message ID
        """
        data = {
            'command': command,
            'params': params or {}
        }
        
        combined_metadata = {**self.default_metadata, **(metadata or {})}
        
        return self.broker.publish(
            topic=topic,
            data=data,
            message_type=MessageType.COMMAND,
            source=self.component_id,
            metadata=combined_metadata
        )
    
    def publish_error(
        self,
        topic: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Publish an error message.
        
        Args:
            topic: Topic to publish to
            error: Exception that occurred
            context: Error context information
            metadata: Additional metadata
        
        Returns:
            Message ID
        """
        data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        }
        
        combined_metadata = {**self.default_metadata, **(metadata or {})}
        
        return self.broker.publish(
            topic=topic,
            data=data,
            message_type=MessageType.ERROR,
            source=self.component_id,
            metadata=combined_metadata
        )
    
    def publish_heartbeat(
        self,
        status: str = "healthy",
        metrics: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Publish a heartbeat message.
        
        Args:
            status: Component status
            metrics: Component metrics
        
        Returns:
            Message ID
        """
        topic = Topics.format(Topics.SYSTEM_HEARTBEAT, component_id=self.component_id)
        
        data = {
            'status': status,
            'metrics': metrics or {}
        }
        
        return self.broker.publish(
            topic=topic,
            data=data,
            message_type=MessageType.HEARTBEAT,
            source=self.component_id,
            metadata=self.default_metadata
        )
    
    def publish_features(
        self,
        symbol: str,
        features: Dict[str, Any],
        timestamp: float
    ) -> str:
        """
        Publish computed features.
        
        Args:
            symbol: Trading symbol
            features: Feature dictionary
            timestamp: Feature timestamp
        
        Returns:
            Message ID
        """
        topic = Topics.format(Topics.FEATURES_COMPUTED, symbol=symbol)
        
        data = {
            'symbol': symbol,
            'features': features,
            'timestamp': timestamp
        }
        
        return self.publish_data(topic, data)
    
    def publish_agent_signal(
        self,
        symbol: str,
        agent_id: str,
        signal: Dict[str, Any]
    ) -> str:
        """
        Publish agent signal.
        
        Args:
            symbol: Trading symbol
            agent_id: Agent identifier
            signal: Signal data
        
        Returns:
            Message ID
        """
        topic = Topics.format(Topics.AGENT_SIGNAL, symbol=symbol, agent_id=agent_id)
        
        return self.publish_data(topic, signal)
    
    def publish_ensemble_signal(
        self,
        symbol: str,
        signal: Dict[str, Any]
    ) -> str:
        """
        Publish ensemble signal.
        
        Args:
            symbol: Trading symbol
            signal: Aggregated signal
        
        Returns:
            Message ID
        """
        topic = Topics.format(Topics.ENSEMBLE_SIGNAL, symbol=symbol)
        
        return self.publish_data(topic, signal)
    
    def publish_order(
        self,
        symbol: str,
        order: Dict[str, Any]
    ) -> str:
        """
        Publish trading order.
        
        Args:
            symbol: Trading symbol
            order: Order details
        
        Returns:
            Message ID
        """
        topic = Topics.format(Topics.ORCHESTRATOR_ORDER, symbol=symbol)
        
        return self.publish_data(topic, order)
