# Phase 6: Deployment & Live Execution - PLAN

## Strategy: Hybrid Approach (Path B+)

We'll combine real data collection with paper trading deployment for maximum safety and performance.

## Why Hybrid?

**Current State:**
- Agents trained on synthetic data
- Backtest engine fixed but not validated on real data
- Risk management system ready
- WebSocket client exists but not integrated

**Problem:**
- Synthetic data doesn't capture real market dynamics
- Models may have poor performance on real data
- Need validation before risking capital

**Solution:**
- Collect 1-2 weeks of real market data
- Retrain agents on real data
- Validate with backtesting
- Deploy to paper trading
- Monitor and iterate

## Phase 6 Roadmap

### Stage 1: Real Data Collection (Week 1)
**Goal:** Collect high-quality real market data

1. **Live Data Recorder** (`scripts/record_live_data.py`)
   - Connect to Binance WebSocket
   - Record trades, order book, ticker
   - Store in CSV/Parquet
   - Run 24/7 for 1-2 weeks

2. **Data Quality Monitor** (`scripts/monitor_data_quality.py`)
   - Check for gaps
   - Validate data integrity
   - Alert on issues

3. **Feature Calculator Integration**
   - Process live data through feature pipeline
   - Store features for training

**Deliverables:**
- 1-2 weeks of real BTC/USDT data
- Order book snapshots (100ms)
- Trade stream
- Calculated features

### Stage 2: Model Retraining (Week 2)
**Goal:** Train agents on real market data

1. **Data Preprocessing**
   - Clean and validate collected data
   - Generate labels from real returns
   - Split train/val/test

2. **Agent Retraining**
   - Retrain all 4 agents on real data
   - Compare performance vs synthetic-trained
   - Save new models

3. **Backtesting Validation**
   - Run backtest on real data
   - Verify risk management works
   - Calculate realistic metrics

**Deliverables:**
- Retrained agent models
- Backtest results on real data
- Performance comparison report

### Stage 3: Paper Trading Deployment (Week 3)
**Goal:** Deploy to paper trading environment

1. **Paper Trading Engine** (`src/deployment/paper_trader.py`)
   - Connect to Binance testnet
   - Execute simulated orders
   - Track virtual portfolio

2. **Live Pipeline Integration**
   - WebSocket → Features → Agents → Orchestrator → Risk → Execution
   - Real-time processing
   - <100ms latency

3. **Monitoring Dashboard**
   - Real-time metrics
   - Position tracking
   - Risk alerts

**Deliverables:**
- Paper trading system running 24/7
- Real-time monitoring
- Performance tracking

### Stage 4: Production Preparation (Week 4)
**Goal:** Prepare for live deployment

1. **Containerization**
   - Docker containers for all components
   - Docker Compose orchestration
   - Health checks

2. **VPS Deployment**
   - Deploy to low-latency VPS
   - Near exchange servers
   - Auto-restart on failure

3. **Production Checklist**
   - Security audit
   - API key management
   - Backup systems
   - Kill switches

**Deliverables:**
- Docker images
- Deployment scripts
- Production runbook

## Timeline

| Week | Stage | Focus | Deliverable |
|------|-------|-------|-------------|
| 1 | Data Collection | Record real data | 1-2 weeks of data |
| 2 | Retraining | Train on real data | New models |
| 3 | Paper Trading | Deploy testnet | Live system |
| 4 | Production Prep | Containerize | Ready for live |

## Success Criteria

### Stage 1: Data Collection
- [ ] 1+ weeks of continuous data
- [ ] <1% data gaps
- [ ] Order book + trades captured
- [ ] Features calculated

### Stage 2: Retraining
- [ ] All agents retrained
- [ ] Test accuracy >55%
- [ ] Backtest Sharpe >0.5
- [ ] Risk management validated

### Stage 3: Paper Trading
- [ ] System runs 24/7
- [ ] <100ms latency
- [ ] No crashes for 48h
- [ ] Positive paper returns

### Stage 4: Production
- [ ] Docker containers built
- [ ] VPS deployed
- [ ] Monitoring active
- [ ] Kill switch tested

## Risk Mitigation

### Data Collection Risks
- **Connection drops:** Auto-reconnect with exponential backoff
- **Data gaps:** Alert and manual review
- **Storage full:** Monitor disk space

### Retraining Risks
- **Poor performance:** Keep synthetic models as fallback
- **Overfitting:** Use proper train/val/test split
- **Long training time:** Use GPU if available

### Paper Trading Risks
- **API rate limits:** Implement rate limiting
- **Testnet differences:** Document differences from mainnet
- **False confidence:** Track slippage differences

### Production Risks
- **Capital loss:** Start with small capital ($100-500)
- **System failure:** Multiple redundancy layers
- **Market conditions:** Circuit breakers active

## Immediate Next Steps

1. **Build Live Data Recorder** (2 hours)
   - WebSocket integration
   - Data storage
   - Quality monitoring

2. **Start Data Collection** (1-2 weeks passive)
   - Run recorder 24/7
   - Monitor daily
   - Validate quality

3. **Build Paper Trading Engine** (4 hours)
   - Testnet integration
   - Order execution
   - Portfolio tracking

4. **Integrate Components** (4 hours)
   - Connect all pieces
   - End-to-end testing
   - Performance optimization

## Cost Estimate

### Infrastructure
- VPS (4 CPU, 8GB RAM): $20-40/month
- Data storage: $5-10/month
- Monitoring: Free (self-hosted)

### Time Investment
- Development: 20-30 hours
- Data collection: 1-2 weeks (passive)
- Testing: 1 week
- Total: 3-4 weeks

### Capital Requirements
- Paper trading: $0 (testnet)
- Initial live: $100-500 (recommended)
- Full deployment: $1,000-10,000 (after validation)

## Decision Point

After Stage 3 (Paper Trading), evaluate:

**Go Live if:**
- Paper trading profitable for 2+ weeks
- Sharpe ratio >1.0
- Max drawdown <10%
- No system failures
- Risk management working

**Stay in Paper if:**
- Inconsistent returns
- High drawdown
- System instability
- Need more data

**Stop if:**
- Consistent losses
- Sharpe ratio <0
- System unreliable
- Risk management failing

## Next Document

After approval, I'll create:
- `scripts/record_live_data.py` - Data recorder
- `scripts/monitor_data_quality.py` - Quality monitor
- `src/deployment/paper_trader.py` - Paper trading engine
- `docker-compose.yml` - Container orchestration
- `docs/DEPLOYMENT_GUIDE.md` - Deployment instructions

---

**Recommendation:** Start with Stage 1 (Data Collection) immediately. This is passive and low-risk, giving us real data while we build the remaining components.

**Estimated Time to Paper Trading:** 2-3 weeks
**Estimated Time to Production Ready:** 4-6 weeks
