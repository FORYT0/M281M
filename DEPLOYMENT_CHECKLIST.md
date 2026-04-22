# M281M Deployment Checklist

## Pre-Deployment Checks

### Environment Setup
- [x] Python 3.11+ installed (✅ Python 3.14.0)
- [x] Virtual environment activated (✅ venv)
- [x] All dependencies installed (✅ including ccxt)
- [x] Data directories created (✅ data/live/)
- [x] All code complete (✅ 12,660+ lines)

### System Requirements
- [x] 8GB RAM minimum
- [x] 50GB disk space
- [x] Internet connection
- [x] Windows compatible commands

## Stage 1: Data Collection (Current Stage)

### Setup
- [x] Data recorder implemented (✅ record_live_data.py)
- [x] Quality monitor implemented (✅ monitor_data_quality.py)
- [x] Batch scripts created (✅ .bat files)
- [ ] Data recorder started

### Daily Tasks
- [ ] Check data recorder is running
- [ ] Monitor disk space
- [ ] Run quality check daily
- [ ] Verify no gaps in data

### Success Criteria
- [ ] 1+ weeks of continuous data
- [ ] <1% data gaps
- [ ] Order book + trades + ticker captured
- [ ] No major anomalies

### Commands
```bash
# Start data collection
start_data_collection.bat
# OR
python scripts/record_live_data.py

# Check quality (run daily)
check_data_quality.bat
# OR
python scripts/monitor_data_quality.py
```

## Stage 2: Model Retraining (After 1-2 weeks)

### Prerequisites
- [ ] 1+ weeks of data collected
- [ ] Data quality validated
- [ ] No major gaps or issues

### Tasks
- [ ] Create data preprocessing script
- [ ] Create retraining script
- [ ] Retrain all 4 agents
- [ ] Validate on test set
- [ ] Compare to synthetic models
- [ ] Run backtest on real data

### Success Criteria
- [ ] Test accuracy >55%
- [ ] Backtest Sharpe >0.5
- [ ] Better than synthetic-trained models
- [ ] Models saved to models/

### Commands (To be created)
```bash
# Preprocess collected data
python scripts/prepare_live_data.py

# Retrain agents
python scripts/retrain_agents.py

# Validate with backtest
python scripts/backtest_real_data.py
```

## Stage 3: Paper Trading (After retraining)

### Prerequisites
- [ ] Agents retrained on real data
- [ ] Backtest validated
- [ ] Models performing well

### Tasks
- [ ] Start paper trading system
- [ ] Monitor performance
- [ ] Track trades
- [ ] Verify risk management
- [ ] Check system stability

### Success Criteria
- [ ] System runs 24/7
- [ ] No crashes for 48h+
- [ ] Positive returns
- [ ] Sharpe >0.5
- [ ] Max drawdown <10%
- [ ] Risk management working

### Commands
```bash
# Start paper trading
python scripts/run_paper_trading.py

# Monitor (check every 5 minutes)
# System prints status automatically
```

## Stage 4: Production Deployment (After paper trading)

### Prerequisites
- [ ] Paper trading successful (1+ week)
- [ ] Positive returns
- [ ] System stable
- [ ] Risk management validated

### Option A: Local Deployment
```bash
# Run locally
python scripts/run_paper_trading.py
```

### Option B: Docker Deployment
```bash
# Build image
docker build -t m281m-trading .

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option C: VPS Deployment
1. [ ] Provision VPS (4 CPU, 8GB RAM)
2. [ ] Install Docker
3. [ ] Copy code to VPS
4. [ ] Configure settings
5. [ ] Start services
6. [ ] Setup monitoring

### Success Criteria
- [ ] Containers running
- [ ] Services healthy
- [ ] Logs accessible
- [ ] Auto-restart working
- [ ] Monitoring active

## Stage 5: Live Trading (After production validation)

### Prerequisites
- [ ] Paper trading profitable (2+ weeks)
- [ ] System stable (no crashes 1+ week)
- [ ] Risk management tested
- [ ] Small capital ready ($100-500)

### Setup
- [ ] Get Binance API keys
- [ ] Configure API keys in config.yaml
- [ ] Set testnet: false
- [ ] Start with small capital
- [ ] Enable monitoring

### Risk Management
- [ ] Circuit breakers active
- [ ] Stop losses configured
- [ ] Daily drawdown limit set
- [ ] Position limits set
- [ ] Kill switch tested

### Monitoring
- [ ] Check system hourly (first day)
- [ ] Check system daily (first week)
- [ ] Review all trades
- [ ] Monitor PnL
- [ ] Watch for issues

### Success Criteria
- [ ] Profitable for 1+ week
- [ ] Win rate >50%
- [ ] Sharpe >1.0
- [ ] Max drawdown <5%
- [ ] No system failures

## Daily Checklist (During Live Trading)

### Morning
- [ ] Check system status
- [ ] Review overnight trades
- [ ] Check PnL
- [ ] Verify risk limits
- [ ] Check logs for errors

### Evening
- [ ] Review day's performance
- [ ] Check open positions
- [ ] Verify drawdown within limits
- [ ] Check system health
- [ ] Backup data

### Weekly
- [ ] Calculate weekly returns
- [ ] Review all trades
- [ ] Analyze performance
- [ ] Adjust parameters if needed
- [ ] Update documentation

## Emergency Procedures

### System Failure
1. Stop all services
2. Check logs
3. Identify issue
4. Fix and restart
5. Verify recovery

### Large Loss
1. Activate kill switch
2. Close all positions
3. Review what happened
4. Analyze risk management
5. Adjust parameters
6. Resume cautiously

### API Issues
1. Check API keys
2. Verify rate limits
3. Check exchange status
4. Switch to backup if needed
5. Monitor closely

## Current Status

**Stage:** 1 - Data Collection  
**Status:** Ready to start  
**Next Action:** Run `start_data_collection.bat`

**Timeline:**
- Week 1-2: Data collection (current)
- Week 3: Model retraining
- Week 4: Paper trading
- Week 5: Production deployment
- Week 6+: Live trading

**Estimated time to live trading:** 4-6 weeks

## Quick Commands

```bash
# Start data collection
start_data_collection.bat

# Check data quality
check_data_quality.bat

# Test risk management
python scripts/test_risk_management.py

# Demo risk management
python scripts/demo_risk_management.py

# Run backtest
python scripts/backtest_demo.py
```

## Support

- Documentation: `docs/`
- Quick start: `QUICK_START.md`
- Project status: `PROJECT_STATUS.md`
- Deployment guide: `docs/DEPLOYMENT_GUIDE.md`

---

**Ready to start:** ✅ YES  
**Next command:** `start_data_collection.bat`
