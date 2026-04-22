# Deployment Guide - Phase 6

## Overview

This guide covers deploying the M281M AI Trading System from data collection through production deployment.

## Prerequisites

### Local Development
- Python 3.11+
- 8GB RAM minimum
- 50GB disk space
- Internet connection

### Production Deployment
- VPS with 4 CPU, 8GB RAM
- Ubuntu 22.04 LTS
- Docker & Docker Compose
- Low latency to exchange servers

## Stage 1: Data Collection

### Start Data Recorder

```bash
# Local machine
python scripts/record_live_data.py
```

This will:
- Connect to Binance WebSocket
- Record order book, trades, ticker
- Save to `data/live/` every 60 seconds
- Auto-reconnect on disconnection

### Monitor Data Quality

```bash
# Run daily
python scripts/monitor_data_quality.py
```

### Run for 1-2 Weeks

Let the recorder run continuously for 1-2 weeks to collect sufficient data.

**Minimum:** 1 week (168 hours)
**Recommended:** 2 weeks (336 hours)

## Stage 2: Model Retraining

### Prepare Data

```bash
# After collecting data, prepare for training
python scripts/prepare_live_data.py
```

This will:
- Combine all CSV files
- Add technical indicators
- Generate labels
- Split train/val/test

### Retrain Agents

```bash
# Retrain all agents on real data
python scripts/retrain_agents.py
```

This will:
- Load collected data
- Retrain all 4 agents
- Evaluate on test set
- Save new models to `models/`

### Validate with Backtest

```bash
# Run backtest on real data
python scripts/backtest_real_data.py
```

Compare results to synthetic-trained models.

## Stage 3: Paper Trading

### Local Paper Trading

```bash
# Run paper trading locally
python scripts/run_paper_trading.py
```

This will:
- Connect to Binance (mainnet for data)
- Run complete trading pipeline
- Execute simulated trades
- Print status every 5 minutes

### Monitor Performance

Watch for:
- Positive returns
- Stable system (no crashes)
- Risk management working
- Reasonable trade frequency

### Run for 1-2 Weeks

Let paper trading run for 1-2 weeks to validate:
- System stability
- Model performance
- Risk management
- Execution quality

## Stage 4: Production Deployment

### Option A: Docker (Recommended)

#### Build Image

```bash
# Build Docker image
docker build -t m281m-trading .
```

#### Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services:
- `data-recorder`: Collects live data
- `paper-trading`: Runs paper trading
- `redis`: Message broker (optional)

#### Monitor Containers

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f paper-trading

# Restart service
docker-compose restart paper-trading
```

### Option B: VPS Deployment

#### 1. Provision VPS

Recommended providers:
- DigitalOcean (NYC/Singapore)
- AWS EC2 (us-east-1/ap-southeast-1)
- Vultr (Tokyo/London)

Choose location near exchange servers for low latency.

#### 2. Setup VPS

```bash
# SSH into VPS
ssh root@your-vps-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Create app directory
mkdir -p /opt/m281m
cd /opt/m281m
```

#### 3. Deploy Code

```bash
# On local machine, copy files to VPS
scp -r . root@your-vps-ip:/opt/m281m/

# Or use git
ssh root@your-vps-ip
cd /opt/m281m
git clone https://github.com/yourusername/m281m.git .
```

#### 4. Configure

```bash
# Edit config
nano config/config.yaml

# Add API keys if needed (for live trading)
# For paper trading, no keys needed
```

#### 5. Start Services

```bash
# Start with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f
```

#### 6. Setup Monitoring

```bash
# Install monitoring tools
apt install htop iotop -y

# Monitor resources
htop

# Monitor disk
df -h

# Monitor logs
tail -f logs/m281m.log
```

### Option C: Systemd Service (No Docker)

#### 1. Create Service File

```bash
# Create service
sudo nano /etc/systemd/system/m281m-paper-trading.service
```

```ini
[Unit]
Description=M281M Paper Trading
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/m281m
ExecStart=/usr/bin/python3 scripts/run_paper_trading.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. Enable and Start

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable m281m-paper-trading

# Start service
sudo systemctl start m281m-paper-trading

# Check status
sudo systemctl status m281m-paper-trading

# View logs
sudo journalctl -u m281m-paper-trading -f
```

## Production Checklist

### Before Going Live

- [ ] Collected 1-2 weeks of real data
- [ ] Retrained agents on real data
- [ ] Backtested on real data (Sharpe >0.5)
- [ ] Paper traded for 1-2 weeks
- [ ] Paper trading profitable
- [ ] System stable (no crashes 48h+)
- [ ] Risk management tested
- [ ] Kill switches tested
- [ ] Monitoring setup
- [ ] Alerts configured
- [ ] Backup system ready

### Security

- [ ] API keys stored securely
- [ ] Firewall configured
- [ ] SSH key authentication
- [ ] Disable root login
- [ ] Regular backups
- [ ] Log rotation configured
- [ ] Rate limiting enabled

### Monitoring

- [ ] System metrics (CPU, RAM, disk)
- [ ] Application logs
- [ ] Trading performance
- [ ] Risk metrics
- [ ] Alert system
- [ ] Daily reports

## Live Trading (After Paper Trading Success)

### 1. Get API Keys

```bash
# Binance
# 1. Go to binance.com
# 2. Account > API Management
# 3. Create API Key
# 4. Enable spot trading
# 5. Whitelist VPS IP
# 6. Save keys securely
```

### 2. Configure API Keys

```bash
# Edit config
nano config/config.yaml

# Add keys
exchange:
  api_key: "your-api-key"
  api_secret: "your-api-secret"
  testnet: false  # Switch to mainnet
```

### 3. Start with Small Capital

**Recommended:**
- Start: $100-500
- After 1 week: $500-1,000
- After 1 month: $1,000-5,000
- After 3 months: Scale up

### 4. Monitor Closely

First week:
- Check every hour
- Monitor all trades
- Verify risk management
- Watch for issues

First month:
- Check daily
- Review performance
- Adjust parameters
- Scale gradually

## Troubleshooting

### Data Recorder Issues

**Problem:** Connection drops
```bash
# Check logs
tail -f logs/m281m.log

# Restart recorder
docker-compose restart data-recorder
```

**Problem:** Disk full
```bash
# Check disk space
df -h

# Clean old data
rm data/live/*_old.csv
```

### Paper Trading Issues

**Problem:** No trades executing
```bash
# Check if agents loaded
grep "Loaded.*Agent" logs/m281m.log

# Check risk manager
grep "Risk check" logs/m281m.log

# Verify signals generated
grep "signal" logs/m281m.log
```

**Problem:** High CPU usage
```bash
# Check processes
htop

# Reduce update frequency
# Edit config.yaml
```

### Docker Issues

**Problem:** Container keeps restarting
```bash
# Check logs
docker-compose logs paper-trading

# Check resources
docker stats

# Restart all
docker-compose down
docker-compose up -d
```

## Performance Optimization

### Reduce Latency

1. **VPS Location:** Choose near exchange
2. **Network:** Use wired connection
3. **Code:** Optimize hot paths
4. **Resources:** Adequate CPU/RAM

### Reduce Costs

1. **VPS:** Start small, scale up
2. **Data:** Compress old data
3. **Logs:** Rotate regularly
4. **Monitoring:** Use free tools

### Improve Reliability

1. **Auto-restart:** Use Docker/systemd
2. **Health checks:** Monitor services
3. **Backups:** Daily backups
4. **Redundancy:** Multiple VPS (advanced)

## Monitoring & Alerts

### Setup Alerts

```bash
# Install monitoring
pip install prometheus-client

# Setup alerts (email/SMS)
# Configure in config.yaml
```

### Key Metrics to Monitor

- System uptime
- Trade execution rate
- Win rate
- PnL
- Drawdown
- Risk metrics
- API rate limits
- Latency

### Daily Checklist

- [ ] Check system status
- [ ] Review trades
- [ ] Check PnL
- [ ] Verify risk limits
- [ ] Monitor drawdown
- [ ] Check logs for errors
- [ ] Verify data quality

## Backup & Recovery

### Backup Strategy

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf backup_$DATE.tar.gz \
    data/ \
    models/ \
    config/ \
    logs/

# Upload to cloud
# aws s3 cp backup_$DATE.tar.gz s3://your-bucket/
```

### Recovery

```bash
# Restore from backup
tar -xzf backup_20260216.tar.gz

# Restart services
docker-compose up -d
```

## Scaling

### Horizontal Scaling

- Multiple VPS in different regions
- Load balancing
- Distributed data collection
- Centralized monitoring

### Vertical Scaling

- Upgrade VPS resources
- Optimize code
- Use GPU for training
- Faster storage

## Cost Breakdown

### Development Phase
- Time: 40-60 hours
- Cost: $0 (local machine)

### Data Collection (1-2 weeks)
- VPS: $0 (local) or $20-40
- Data: $0 (free from Binance)

### Paper Trading (1-2 weeks)
- VPS: $20-40/month
- Monitoring: $0 (self-hosted)

### Live Trading
- VPS: $20-40/month
- Capital: $100-10,000
- Exchange fees: 0.1% per trade

### Total First Month
- Development: $0
- Infrastructure: $20-40
- Capital: $100-500 (recommended start)

## Next Steps

1. **Start data collection** (run now)
2. **Wait 1-2 weeks** (passive)
3. **Retrain agents** (1-2 days)
4. **Paper trade** (1-2 weeks)
5. **Deploy production** (1 day)
6. **Go live** (small capital)

---

**Status:** Ready for deployment
**Estimated time to live:** 4-6 weeks
**Recommended start capital:** $100-500
