# Message Broker Setup Guide

**Date:** February 16, 2026  
**Component:** Redis-based Message Broker

---

## Overview

The M281M trading system uses Redis as a message broker to decouple components and enable horizontal scaling. This allows:

- **Decoupling:** Components communicate via pub/sub, not direct calls
- **Scaling:** Multiple instances of each component can run in parallel
- **Monitoring:** All messages flow through a central point
- **Reliability:** Redis provides persistence and high availability
- **Performance:** In-memory operations with microsecond latency

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MESSAGE BROKER                        │
│                      (Redis)                             │
└─────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
    ┌────┴────┐          ┌────┴────┐         ┌────┴────┐
    │ Feature │          │ Agents  │         │Orchestr.│
    │  Calc   │          │ (1-N)   │         │         │
    └─────────┘          └─────────┘         └─────────┘
         │                    │                    │
         │ publish            │ publish            │ publish
         │ features           │ signals            │ orders
         ▼                    ▼                    ▼
    features.computed    agent.signal.*    orchestrator.order
```

---

## Installation

### Windows

1. **Download Redis:**
   - Visit: https://github.com/microsoftarchive/redis/releases
   - Download: Redis-x64-3.0.504.msi (or latest)
   - Install to: C:\Program Files\Redis

2. **Start Redis:**
   ```cmd
   cd "C:\Program Files\Redis"
   redis-server.exe redis.windows.conf
   ```

3. **Verify:**
   ```cmd
   redis-cli.exe ping
   ```
   Should return: `PONG`

### Linux/Mac

1. **Install Redis:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install redis-server
   
   # Mac
   brew install redis
   
   # CentOS/RHEL
   sudo yum install redis
   ```

2. **Start Redis:**
   ```bash
   # Ubuntu/Debian
   sudo systemctl start redis-server
   
   # Mac
   brew services start redis
   
   # Manual
   redis-server
   ```

3. **Verify:**
   ```bash
   redis-cli ping
   ```
   Should return: `PONG`

### Docker

```bash
# Pull Redis image
docker pull redis:latest

# Run Redis
docker run -d \
  --name m281m-redis \
  -p 6379:6379 \
  -v $(pwd)/config/redis.conf:/usr/local/etc/redis/redis.conf \
  redis:latest \
  redis-server /usr/local/etc/redis/redis.conf

# Verify
docker exec -it m281m-redis redis-cli ping
```

---

## Python Dependencies

Add to `requirements.txt`:

```
redis>=5.0.0
```

Install:

```bash
pip install redis
```

---

## Configuration

### Basic Configuration

```python
from src.messaging import MessageBroker

# Create broker
broker = MessageBroker(
    host='localhost',
    port=6379,
    db=0,
    password=None,  # Set if Redis requires auth
    max_connections=50
)
```

### Production Configuration

```python
broker = MessageBroker(
    host='redis.production.com',
    port=6379,
    db=0,
    password='your_secure_password',
    max_connections=100
)
```

### Environment Variables

```bash
# .env file
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_MAX_CONNECTIONS=50
```

```python
import os
from src.messaging import MessageBroker

broker = MessageBroker(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    password=os.getenv('REDIS_PASSWORD'),
    max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', 50))
)
```

---

## Usage Examples

### Publishing Features

```python
from src.messaging import MessageBroker, Publisher

# Create broker and publisher
broker = MessageBroker()
publisher = Publisher(broker, component_id='feature_calculator')

# Publish features
features = {
    'rsi': 65.3,
    'ema_fast': 50000.0,
    'ema_slow': 49500.0,
    'volume': 1000000
}

publisher.publish_features(
    symbol='BTCUSDT',
    features=features,
    timestamp=time.time()
)
```

### Subscribing to Features

```python
from src.messaging import MessageBroker, Subscriber

# Create broker and subscriber
broker = MessageBroker()
subscriber = Subscriber(broker, component_id='momentum_agent')

# Define callback
def on_features(features):
    print(f"Received features: {features}")
    # Process features...

# Subscribe
subscriber.subscribe_features('BTCUSDT', on_features)

# Keep running
subscriber.wait_all()
```

### Agent Publishing Signals

```python
from src.messaging import MessageBroker, Publisher

broker = MessageBroker()
publisher = Publisher(broker, component_id='momentum_agent')

# Publish signal
signal = {
    'direction': 'long',
    'confidence': 0.85,
    'reasoning': 'Strong upward momentum'
}

publisher.publish_agent_signal(
    symbol='BTCUSDT',
    agent_id='momentum_agent',
    signal=signal
)
```

### Ensemble Subscribing to Agents

```python
from src.messaging import MessageBroker, Subscriber

broker = MessageBroker()
subscriber = Subscriber(broker, component_id='ensemble')

# Track signals
signals = {}

def on_agent_signal(agent_id, signal):
    signals[agent_id] = signal
    print(f"Received signal from {agent_id}: {signal}")
    
    # When all agents have reported, aggregate
    if len(signals) >= 4:
        aggregate_signals(signals)

# Subscribe to all agents
subscriber.subscribe_agent_signals('BTCUSDT', on_agent_signal)
```

---

## Message Topics

### Market Data
- `market.tick.{symbol}` - Raw tick data
- `market.orderbook.{symbol}` - Order book updates
- `market.trade.{symbol}` - Trade executions

### Features
- `features.computed.{symbol}` - Computed features
- `features.request.{symbol}` - Feature computation request

### Agents
- `agent.signal.{symbol}.{agent_id}` - Individual agent signals
- `agent.status.{agent_id}` - Agent health status

### Ensemble
- `ensemble.signal.{symbol}` - Aggregated ensemble signal
- `ensemble.confidence.{symbol}` - Ensemble confidence

### Orchestrator
- `orchestrator.decision.{symbol}` - Final trading decision
- `orchestrator.order.{symbol}` - Order to execute

### System
- `system.heartbeat.{component_id}` - Component heartbeat
- `system.error.{component_id}` - Error notifications
- `system.metrics.{component_id}` - Performance metrics

---

## Testing

### Run Test Suite

```bash
# Make sure Redis is running
redis-server

# Run tests
python scripts/test_message_broker.py
```

### Manual Testing

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Monitor messages
redis-cli
> PSUBSCRIBE *

# Terminal 3: Publish test message
python -c "
from src.messaging import MessageBroker, Publisher
broker = MessageBroker()
pub = Publisher(broker, 'test')
pub.publish_data('test.topic', {'hello': 'world'})
"
```

---

## Monitoring

### Redis CLI

```bash
# Connect to Redis
redis-cli

# Monitor all commands
MONITOR

# Get info
INFO

# Check pub/sub channels
PUBSUB CHANNELS

# Check number of subscribers
PUBSUB NUMSUB channel_name
```

### Python Monitoring

```python
from src.messaging import MessageBroker

broker = MessageBroker()

# Get statistics
stats = broker.get_stats()

print(f"Messages Published: {stats['messages_published']}")
print(f"Messages Received: {stats['messages_received']}")
print(f"Errors: {stats['errors']}")
print(f"Connected Clients: {stats['redis_connected_clients']}")
print(f"Memory Used: {stats['redis_used_memory']}")
```

---

## Performance Tuning

### Redis Configuration

Edit `config/redis.conf`:

```conf
# Increase max clients
maxclients 10000

# Set memory limit
maxmemory 2gb
maxmemory-policy allkeys-lru

# Optimize pub/sub buffer
client-output-buffer-limit pubsub 32mb 8mb 60

# Disable persistence for max performance (if acceptable)
save ""
appendonly no
```

### Connection Pooling

```python
broker = MessageBroker(
    host='localhost',
    port=6379,
    max_connections=100  # Increase for high throughput
)
```

### Batch Publishing

```python
# Instead of publishing one by one
for i in range(1000):
    publisher.publish_data('topic', {'value': i})

# Use pipeline (future enhancement)
# with broker.pipeline() as pipe:
#     for i in range(1000):
#         pipe.publish('topic', {'value': i})
#     pipe.execute()
```

---

## Troubleshooting

### Connection Refused

**Problem:** `redis.exceptions.ConnectionError: Error connecting to localhost:6379`

**Solution:**
1. Check if Redis is running: `redis-cli ping`
2. Start Redis: `redis-server`
3. Check firewall settings
4. Verify host/port in configuration

### Too Many Connections

**Problem:** `redis.exceptions.ConnectionError: max number of clients reached`

**Solution:**
1. Increase `maxclients` in redis.conf
2. Reduce `max_connections` in MessageBroker
3. Close unused connections

### Memory Issues

**Problem:** Redis using too much memory

**Solution:**
1. Set `maxmemory` in redis.conf
2. Configure eviction policy: `maxmemory-policy allkeys-lru`
3. Monitor memory usage: `redis-cli INFO memory`

### Slow Performance

**Problem:** High latency

**Solution:**
1. Check Redis CPU usage
2. Enable persistence only if needed
3. Use connection pooling
4. Consider Redis Cluster for scaling

---

## Production Deployment

### High Availability

Use Redis Sentinel for automatic failover:

```bash
# Start Redis master
redis-server --port 6379

# Start Redis replicas
redis-server --port 6380 --replicaof 127.0.0.1 6379
redis-server --port 6381 --replicaof 127.0.0.1 6379

# Start Sentinel
redis-sentinel sentinel.conf
```

### Clustering

For horizontal scaling:

```bash
# Create Redis Cluster
redis-cli --cluster create \
  127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 \
  127.0.0.1:7003 127.0.0.1:7004 127.0.0.1:7005 \
  --cluster-replicas 1
```

### Security

1. **Enable Authentication:**
   ```conf
   # redis.conf
   requirepass your_secure_password
   ```

2. **Bind to Specific Interface:**
   ```conf
   bind 127.0.0.1 192.168.1.100
   ```

3. **Use TLS:**
   ```conf
   tls-port 6380
   tls-cert-file /path/to/cert.pem
   tls-key-file /path/to/key.pem
   ```

---

## Next Steps

1. **Install Redis** following the instructions above
2. **Run test suite** to verify installation
3. **Integrate with existing components:**
   - Update feature calculator to publish via broker
   - Update agents to subscribe to features
   - Update ensemble to subscribe to agent signals
   - Update orchestrator to subscribe to ensemble signals

4. **Monitor performance** and tune as needed
5. **Deploy to production** with high availability setup

---

## Resources

- Redis Documentation: https://redis.io/documentation
- Redis Python Client: https://redis-py.readthedocs.io/
- Redis Pub/Sub: https://redis.io/topics/pubsub
- Redis Sentinel: https://redis.io/topics/sentinel
- Redis Cluster: https://redis.io/topics/cluster-tutorial

---

**Status:** ✅ Message broker implementation complete and ready for integration
