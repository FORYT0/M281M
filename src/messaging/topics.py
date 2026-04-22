"""
Message Topics - Centralized topic definitions.
"""

class Topics:
    """
    Centralized message topic definitions.
    
    Topic naming convention: {component}.{data_type}.{symbol}
    """
    
    # Market Data Topics
    MARKET_TICK = "market.tick.{symbol}"           # Raw tick data
    MARKET_ORDERBOOK = "market.orderbook.{symbol}" # Order book updates
    MARKET_TRADE = "market.trade.{symbol}"         # Trade executions
    
    # Feature Topics
    FEATURES_COMPUTED = "features.computed.{symbol}"  # Computed features
    FEATURES_REQUEST = "features.request.{symbol}"    # Feature computation request
    
    # Agent Topics
    AGENT_SIGNAL = "agent.signal.{symbol}.{agent_id}"      # Individual agent signals
    AGENT_PREDICTION = "agent.prediction.{symbol}.{agent_id}"  # Agent predictions
    AGENT_STATUS = "agent.status.{agent_id}"               # Agent health status
    
    # Ensemble Topics
    ENSEMBLE_SIGNAL = "ensemble.signal.{symbol}"     # Aggregated ensemble signal
    ENSEMBLE_CONFIDENCE = "ensemble.confidence.{symbol}"  # Ensemble confidence
    
    # Orchestrator Topics
    ORCHESTRATOR_DECISION = "orchestrator.decision.{symbol}"  # Final trading decision
    ORCHESTRATOR_ORDER = "orchestrator.order.{symbol}"        # Order to execute
    ORCHESTRATOR_STATUS = "orchestrator.status"               # Orchestrator status
    
    # Execution Topics
    EXECUTION_ORDER = "execution.order.{symbol}"      # Order sent to exchange
    EXECUTION_FILL = "execution.fill.{symbol}"        # Order fill notification
    EXECUTION_CANCEL = "execution.cancel.{symbol}"    # Order cancellation
    
    # Risk Topics
    RISK_CHECK = "risk.check.{symbol}"          # Risk check request
    RISK_VIOLATION = "risk.violation.{symbol}"  # Risk limit violation
    RISK_STATUS = "risk.status"                 # Risk system status
    
    # System Topics
    SYSTEM_HEARTBEAT = "system.heartbeat.{component_id}"  # Component heartbeat
    SYSTEM_ERROR = "system.error.{component_id}"          # Error notifications
    SYSTEM_METRICS = "system.metrics.{component_id}"      # Performance metrics
    SYSTEM_COMMAND = "system.command.{component_id}"      # Control commands
    
    # Control Topics
    CONTROL_START = "control.start"    # Start all components
    CONTROL_STOP = "control.stop"      # Stop all components
    CONTROL_PAUSE = "control.pause"    # Pause processing
    CONTROL_RESUME = "control.resume"  # Resume processing
    
    @staticmethod
    def format(topic_template: str, **kwargs) -> str:
        """
        Format a topic template with parameters.
        
        Args:
            topic_template: Topic template with {placeholders}
            **kwargs: Values to substitute
        
        Returns:
            Formatted topic string
        
        Example:
            >>> Topics.format(Topics.MARKET_TICK, symbol='BTCUSDT')
            'market.tick.BTCUSDT'
        """
        return topic_template.format(**kwargs)
    
    @staticmethod
    def parse(topic: str) -> dict:
        """
        Parse a topic string into components.
        
        Args:
            topic: Topic string (e.g., 'market.tick.BTCUSDT')
        
        Returns:
            Dictionary with parsed components
        
        Example:
            >>> Topics.parse('market.tick.BTCUSDT')
            {'category': 'market', 'type': 'tick', 'symbol': 'BTCUSDT'}
        """
        parts = topic.split('.')
        
        if len(parts) < 2:
            return {'raw': topic}
        
        result = {
            'category': parts[0],
            'type': parts[1]
        }
        
        # Add additional parts as indexed keys
        for i, part in enumerate(parts[2:], start=2):
            result[f'part{i}'] = part
        
        # Try to identify common patterns
        if len(parts) >= 3:
            # Assume third part is symbol for market/features/agent topics
            if parts[0] in ['market', 'features', 'agent', 'ensemble', 'orchestrator', 'execution', 'risk']:
                result['symbol'] = parts[2]
            
            # For agent topics, fourth part might be agent_id
            if parts[0] == 'agent' and len(parts) >= 4:
                result['agent_id'] = parts[3]
        
        return result
    
    @staticmethod
    def match_pattern(topic: str, pattern: str) -> bool:
        """
        Check if a topic matches a pattern with wildcards.
        
        Args:
            topic: Actual topic string
            pattern: Pattern with * (single level) or # (multi-level) wildcards
        
        Returns:
            True if topic matches pattern
        
        Example:
            >>> Topics.match_pattern('market.tick.BTCUSDT', 'market.*.BTCUSDT')
            True
            >>> Topics.match_pattern('market.tick.BTCUSDT', 'market.#')
            True
        """
        topic_parts = topic.split('.')
        pattern_parts = pattern.split('.')
        
        # Handle multi-level wildcard (#)
        if '#' in pattern_parts:
            hash_idx = pattern_parts.index('#')
            # Match up to the # wildcard
            if topic_parts[:hash_idx] != pattern_parts[:hash_idx]:
                return False
            # Everything after # matches
            return True
        
        # Must have same number of parts for single-level wildcards
        if len(topic_parts) != len(pattern_parts):
            return False
        
        # Check each part
        for topic_part, pattern_part in zip(topic_parts, pattern_parts):
            if pattern_part != '*' and pattern_part != topic_part:
                return False
        
        return True
