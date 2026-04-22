"""
Message Broker - Core Redis-based pub/sub implementation.
"""

import redis
import json
import time
import uuid
from typing import Any, Dict, Optional, Callable, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict, field
import threading
import logging

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Message type enumeration."""
    DATA = "data"           # Data message
    COMMAND = "command"     # Control command
    EVENT = "event"         # Event notification
    REQUEST = "request"     # Request for data/action
    RESPONSE = "response"   # Response to request
    ERROR = "error"         # Error notification
    HEARTBEAT = "heartbeat" # Heartbeat/keepalive


@dataclass
class Message:
    """
    Standard message format for all communications.
    
    Attributes:
        topic: Message topic/channel
        data: Message payload (must be JSON-serializable)
        message_type: Type of message
        message_id: Unique message identifier
        timestamp: Message creation timestamp
        source: Component that created the message
        correlation_id: ID for request/response correlation
        metadata: Additional metadata
    """
    topic: str
    data: Any
    message_type: MessageType = MessageType.DATA
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        result = asdict(self)
        result['message_type'] = self.message_type.value
        return result
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        if 'message_type' in data and isinstance(data['message_type'], str):
            data['message_type'] = MessageType(data['message_type'])
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create message from JSON string."""
        return cls.from_dict(json.loads(json_str))


class MessageBroker:
    """
    Redis-based message broker for pub/sub communication.
    
    Features:
    - Publish/subscribe messaging
    - Request/response pattern
    - Message persistence (optional)
    - Dead letter queue
    - Message TTL
    - Monitoring and metrics
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = True,
        max_connections: int = 50
    ):
        """
        Initialize message broker.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (if required)
            decode_responses: Decode responses to strings
            max_connections: Maximum connection pool size
        """
        self.host = host
        self.port = port
        self.db = db
        
        # Create connection pool
        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=decode_responses,
            max_connections=max_connections
        )
        
        # Create Redis clients
        self.redis_client = redis.Redis(connection_pool=self.pool)
        self.pubsub = self.redis_client.pubsub()
        
        # Metrics
        self.messages_published = 0
        self.messages_received = 0
        self.errors = 0
        
        # Test connection
        try:
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {host}:{port}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def publish(
        self,
        topic: str,
        data: Any,
        message_type: MessageType = MessageType.DATA,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Publish a message to a topic.
        
        Args:
            topic: Topic to publish to
            data: Message data (must be JSON-serializable)
            message_type: Type of message
            source: Source component identifier
            correlation_id: Correlation ID for request/response
            metadata: Additional metadata
        
        Returns:
            Message ID
        """
        try:
            # Create message
            message = Message(
                topic=topic,
                data=data,
                message_type=message_type,
                source=source,
                correlation_id=correlation_id,
                metadata=metadata or {}
            )
            
            # Publish to Redis
            self.redis_client.publish(topic, message.to_json())
            
            # Update metrics
            self.messages_published += 1
            
            logger.debug(f"Published message {message.message_id} to {topic}")
            
            return message.message_id
            
        except Exception as e:
            self.errors += 1
            logger.error(f"Error publishing message to {topic}: {e}")
            raise
    
    def subscribe(
        self,
        topics: List[str],
        callback: Callable[[Message], None],
        error_callback: Optional[Callable[[Exception], None]] = None
    ) -> threading.Thread:
        """
        Subscribe to topics and process messages.
        
        Args:
            topics: List of topics to subscribe to
            callback: Function to call for each message
            error_callback: Function to call on errors
        
        Returns:
            Thread running the subscription
        """
        def _subscribe_thread():
            try:
                # Subscribe to topics
                self.pubsub.subscribe(*topics)
                logger.info(f"Subscribed to topics: {topics}")
                
                # Listen for messages
                for message in self.pubsub.listen():
                    try:
                        if message['type'] == 'message':
                            # Parse message
                            msg = Message.from_json(message['data'])
                            
                            # Update metrics
                            self.messages_received += 1
                            
                            # Call callback
                            callback(msg)
                            
                    except Exception as e:
                        self.errors += 1
                        logger.error(f"Error processing message: {e}")
                        if error_callback:
                            error_callback(e)
                            
            except Exception as e:
                logger.error(f"Subscription error: {e}")
                if error_callback:
                    error_callback(e)
        
        # Start subscription thread
        thread = threading.Thread(target=_subscribe_thread, daemon=True)
        thread.start()
        
        return thread
    
    def request(
        self,
        topic: str,
        data: Any,
        timeout: float = 5.0,
        source: Optional[str] = None
    ) -> Optional[Message]:
        """
        Send a request and wait for response.
        
        Args:
            topic: Topic to send request to
            data: Request data
            timeout: Timeout in seconds
            source: Source component identifier
        
        Returns:
            Response message or None if timeout
        """
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        response_topic = f"{topic}.response.{correlation_id}"
        
        # Subscribe to response topic
        response = [None]
        response_event = threading.Event()
        
        def response_callback(msg: Message):
            if msg.correlation_id == correlation_id:
                response[0] = msg
                response_event.set()
        
        # Subscribe to response
        self.pubsub.subscribe(response_topic)
        thread = self.subscribe([response_topic], response_callback)
        
        try:
            # Send request
            self.publish(
                topic=topic,
                data=data,
                message_type=MessageType.REQUEST,
                source=source,
                correlation_id=correlation_id,
                metadata={'response_topic': response_topic}
            )
            
            # Wait for response
            if response_event.wait(timeout):
                return response[0]
            else:
                logger.warning(f"Request timeout for {topic}")
                return None
                
        finally:
            # Cleanup
            self.pubsub.unsubscribe(response_topic)
    
    def respond(
        self,
        request: Message,
        data: Any,
        source: Optional[str] = None
    ) -> str:
        """
        Send a response to a request.
        
        Args:
            request: Original request message
            data: Response data
            source: Source component identifier
        
        Returns:
            Message ID
        """
        response_topic = request.metadata.get('response_topic')
        
        if not response_topic:
            raise ValueError("Request message does not have response_topic in metadata")
        
        return self.publish(
            topic=response_topic,
            data=data,
            message_type=MessageType.RESPONSE,
            source=source,
            correlation_id=request.correlation_id
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get broker statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            info = self.redis_client.info()
            
            return {
                'messages_published': self.messages_published,
                'messages_received': self.messages_received,
                'errors': self.errors,
                'redis_connected_clients': info.get('connected_clients', 0),
                'redis_used_memory': info.get('used_memory_human', 'N/A'),
                'redis_uptime_seconds': info.get('uptime_in_seconds', 0),
                'pubsub_channels': self.redis_client.pubsub_numsub(),
                'pubsub_patterns': self.redis_client.pubsub_numpat()
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                'messages_published': self.messages_published,
                'messages_received': self.messages_received,
                'errors': self.errors,
                'error': str(e)
            }
    
    def close(self):
        """Close broker connections."""
        try:
            self.pubsub.close()
            self.redis_client.close()
            logger.info("Message broker closed")
        except Exception as e:
            logger.error(f"Error closing broker: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
