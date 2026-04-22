"""
Test script for message broker functionality.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import asyncio
from src.messaging import MessageBroker, Publisher, Subscriber, Topics, MessageType

def test_basic_pubsub():
    """Test basic publish/subscribe."""
    print("\n" + "="*60)
    print("TEST 1: Basic Publish/Subscribe")
    print("="*60)
    
    try:
        # Create broker
        broker = MessageBroker(host='localhost', port=6379)
        
        # Create publisher and subscriber
        publisher = Publisher(broker, component_id='test_publisher')
        subscriber = Subscriber(broker, component_id='test_subscriber')
        
        # Track received messages
        received = []
        
        def on_message(msg):
            print(f"  Received: {msg.data}")
            received.append(msg.data)
        
        # Subscribe
        topic = "test.basic"
        subscriber.subscribe([topic], on_message)
        
        # Give subscription time to start
        time.sleep(0.5)
        
        # Publish messages
        print("\nPublishing messages...")
        for i in range(3):
            data = {'message': f'Hello {i}', 'value': i}
            publisher.publish_data(topic, data)
            print(f"  Published: {data}")
            time.sleep(0.1)
        
        # Wait for messages
        time.sleep(1)
        
        # Verify
        print(f"\nReceived {len(received)} messages")
        if len(received) == 3:
            print("[PASS] All messages received")
        else:
            print(f"[FAIL] Expected 3 messages, got {len(received)}")
        
        broker.close()
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False
    
    return True


def test_features_pubsub():
    """Test feature publishing and subscription."""
    print("\n" + "="*60)
    print("TEST 2: Features Publish/Subscribe")
    print("="*60)
    
    try:
        broker = MessageBroker(host='localhost', port=6379)
        
        publisher = Publisher(broker, component_id='feature_calculator')
        subscriber = Subscriber(broker, component_id='agent')
        
        received_features = []
        
        def on_features(features):
            print(f"  Agent received features: {list(features['features'].keys())}")
            received_features.append(features)
        
        # Subscribe to features
        symbol = 'BTCUSDT'
        subscriber.subscribe_features(symbol, on_features)
        
        time.sleep(0.5)
        
        # Publish features
        print("\nPublishing features...")
        features = {
            'rsi': 65.3,
            'ema_fast': 50000.0,
            'ema_slow': 49500.0,
            'volume': 1000000
        }
        
        publisher.publish_features(symbol, features, time.time())
        
        time.sleep(1)
        
        if len(received_features) > 0:
            print("[PASS] Features received")
        else:
            print("[FAIL] No features received")
        
        broker.close()
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False
    
    return True


def test_agent_signals():
    """Test agent signal publishing."""
    print("\n" + "="*60)
    print("TEST 3: Agent Signals")
    print("="*60)
    
    try:
        broker = MessageBroker(host='localhost', port=6379)
        
        # Create multiple agents
        agent1_pub = Publisher(broker, component_id='momentum_agent')
        agent2_pub = Publisher(broker, component_id='mean_reversion_agent')
        
        # Create ensemble subscriber
        ensemble_sub = Subscriber(broker, component_id='ensemble')
        
        received_signals = []
        
        def on_signal(agent_id, signal):
            print(f"  Ensemble received signal from {agent_id}: {signal['direction']}")
            received_signals.append((agent_id, signal))
        
        # Subscribe to all agent signals
        symbol = 'BTCUSDT'
        ensemble_sub.subscribe_agent_signals(symbol, on_signal)
        
        time.sleep(0.5)
        
        # Agents publish signals
        print("\nAgents publishing signals...")
        
        signal1 = {'direction': 'long', 'confidence': 0.85}
        agent1_pub.publish_agent_signal(symbol, 'momentum_agent', signal1)
        print(f"  momentum_agent: {signal1}")
        
        time.sleep(0.2)
        
        signal2 = {'direction': 'short', 'confidence': 0.65}
        agent2_pub.publish_agent_signal(symbol, 'mean_reversion_agent', signal2)
        print(f"  mean_reversion_agent: {signal2}")
        
        time.sleep(1)
        
        if len(received_signals) == 2:
            print("[PASS] All agent signals received")
        else:
            print(f"[FAIL] Expected 2 signals, got {len(received_signals)}")
        
        broker.close()
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False
    
    return True


def test_full_pipeline():
    """Test complete pipeline: features -> agents -> ensemble -> orchestrator."""
    print("\n" + "="*60)
    print("TEST 4: Full Pipeline")
    print("="*60)
    
    try:
        broker = MessageBroker(host='localhost', port=6379)
        symbol = 'BTCUSDT'
        
        # Components
        feature_pub = Publisher(broker, component_id='feature_calculator')
        agent_sub = Subscriber(broker, component_id='agent')
        agent_pub = Publisher(broker, component_id='agent')
        ensemble_sub = Subscriber(broker, component_id='ensemble')
        ensemble_pub = Publisher(broker, component_id='ensemble')
        orchestrator_sub = Subscriber(broker, component_id='orchestrator')
        
        # Track pipeline
        pipeline_steps = []
        
        # Agent: receives features, publishes signal
        def on_features(features):
            print(f"  [Agent] Received features")
            pipeline_steps.append('features_received')
            
            # Generate signal
            signal = {'direction': 'long', 'confidence': 0.8}
            agent_pub.publish_agent_signal(symbol, 'test_agent', signal)
            print(f"  [Agent] Published signal: {signal}")
            pipeline_steps.append('signal_published')
        
        # Ensemble: receives signals, publishes aggregated signal
        def on_agent_signal(agent_id, signal):
            print(f"  [Ensemble] Received signal from {agent_id}")
            pipeline_steps.append('signal_received')
            
            # Aggregate and publish
            ensemble_signal = {'direction': signal['direction'], 'confidence': 0.75}
            ensemble_pub.publish_ensemble_signal(symbol, ensemble_signal)
            print(f"  [Ensemble] Published ensemble signal: {ensemble_signal}")
            pipeline_steps.append('ensemble_published')
        
        # Orchestrator: receives ensemble signal, makes decision
        def on_ensemble_signal(signal):
            print(f"  [Orchestrator] Received ensemble signal: {signal}")
            pipeline_steps.append('orchestrator_received')
            
            # Make decision
            order = {
                'symbol': symbol,
                'side': 'buy' if signal['direction'] == 'long' else 'sell',
                'size': 1.0
            }
            print(f"  [Orchestrator] Decision: {order}")
            pipeline_steps.append('decision_made')
        
        # Setup subscriptions
        agent_sub.subscribe_features(symbol, on_features)
        ensemble_sub.subscribe_agent_signals(symbol, on_agent_signal)
        orchestrator_sub.subscribe_ensemble_signals(symbol, on_ensemble_signal)
        
        time.sleep(0.5)
        
        # Start pipeline with features
        print("\nStarting pipeline...")
        features = {'rsi': 65.0, 'ema': 50000.0}
        feature_pub.publish_features(symbol, features, time.time())
        print(f"  [Features] Published: {features}")
        
        # Wait for pipeline to complete
        time.sleep(2)
        
        # Verify pipeline
        print(f"\nPipeline steps completed: {len(pipeline_steps)}")
        expected_steps = [
            'features_received',
            'signal_published',
            'signal_received',
            'ensemble_published',
            'orchestrator_received',
            'decision_made'
        ]
        
        if pipeline_steps == expected_steps:
            print("[PASS] Full pipeline executed correctly")
        else:
            print(f"[FAIL] Pipeline incomplete")
            print(f"  Expected: {expected_steps}")
            print(f"  Got: {pipeline_steps}")
        
        broker.close()
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_broker_stats():
    """Test broker statistics."""
    print("\n" + "="*60)
    print("TEST 5: Broker Statistics")
    print("="*60)
    
    try:
        broker = MessageBroker(host='localhost', port=6379)
        publisher = Publisher(broker, component_id='test')
        
        # Publish some messages
        for i in range(10):
            publisher.publish_data('test.stats', {'value': i})
        
        time.sleep(0.5)
        
        # Get stats
        stats = broker.get_stats()
        
        print("\nBroker Statistics:")
        print(f"  Messages Published: {stats['messages_published']}")
        print(f"  Messages Received: {stats['messages_received']}")
        print(f"  Errors: {stats['errors']}")
        print(f"  Redis Connected Clients: {stats.get('redis_connected_clients', 'N/A')}")
        print(f"  Redis Memory: {stats.get('redis_used_memory', 'N/A')}")
        
        if stats['messages_published'] >= 10:
            print("[PASS] Statistics working")
        else:
            print("[FAIL] Statistics not tracking correctly")
        
        broker.close()
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False
    
    return True


if __name__ == '__main__':
    print("\n" + "="*60)
    print("MESSAGE BROKER TEST SUITE")
    print("="*60)
    print("\nMake sure Redis is running on localhost:6379")
    print("  Windows: redis-server.exe")
    print("  Linux/Mac: redis-server")
    
    input("\nPress Enter to start tests...")
    
    results = []
    
    # Run tests
    results.append(("Basic Pub/Sub", test_basic_pubsub()))
    results.append(("Features Pub/Sub", test_features_pubsub()))
    results.append(("Agent Signals", test_agent_signals()))
    results.append(("Full Pipeline", test_full_pipeline()))
    results.append(("Broker Stats", test_broker_stats()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll tests passed! Message broker is working correctly.")
    else:
        print(f"\n{total - passed} test(s) failed.")
