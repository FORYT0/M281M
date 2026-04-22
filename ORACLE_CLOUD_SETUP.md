# 🌩️ Oracle Cloud Free Tier Setup Guide

## Complete guide to run M281M data collection on Oracle Cloud (Always Free)

---

## Part 1: Create Oracle Cloud Account (10 minutes)

### Step 1: Sign Up

1. Go to: https://www.oracle.com/cloud/free/
2. Click "Start for free"
3. Fill in your details:
   - Email address
   - Country/Territory
   - First and Last name

### Step 2: Verify Email

1. Check your email
2. Click verification link
3. Complete registration

### Step 3: Add Payment Method

**Important:** This is for verification only. You won't be charged if you stay in Always Free tier.

1. Enter credit/debit card details
2. Oracle may charge $1 for verification (refunded immediately)
3. Set up billing alerts (recommended)

### Step 4: Choose Home Region

**Important:** Choose carefully - you can't change this later!

**Recommended regions:**
- US East (Ashburn) - Usually available
- US West (Phoenix) - Usually available
- UK South (London) - Good for Europe/Africa

**Note:** Some regions have high demand for free tier. If one doesn't work, try another.

---

## Part 2: Create a VM Instance (15 minutes)

### Step 1: Access Compute

1. Log in to Oracle Cloud Console
2. Click hamburger menu (☰) top left
3. Go to: **Compute** → **Instances**
4. Click **"Create Instance"**

### Step 2: Configure Instance

**Name:**
```
m281m-data-collector
```

**Placement:**
- Leave as default (Availability Domain)

**Image and Shape:**

1. Click **"Change Image"**
   - Select: **Ubuntu 22.04** (or latest Ubuntu)
   - Click **"Select Image"**

2. Click **"Change Shape"**
   - Select: **Ampere** (ARM-based)
   - Choose: **VM.Standard.A1.Flex**
   - Set: **1 OCPU, 6 GB RAM** (this is free!)
   - Click **"Select Shape"**

**Why ARM?** Better specs for free tier (6GB RAM vs 1GB)

### Step 3: Networking

**Virtual Cloud Network:**
- Leave default (auto-creates VCN)

**Subnet:**
- Leave default (public subnet)

**Public IP:**
- ✅ **Assign a public IPv4 address** (IMPORTANT!)

### Step 4: SSH Keys

**IMPORTANT:** You need SSH keys to access your VM.

**Option A: Generate new keys (Recommended)**

1. Click **"Generate a key pair for me"**
2. Click **"Save Private Key"** - Save as `oracle_key.key`
3. Click **"Save Public Key"** - Save as `oracle_key.pub`
4. **Keep these files safe!** You need them to access your VM

**Option B: Use existing keys**
- If you have SSH keys, upload your public key

### Step 5: Boot Volume

- Leave default (50 GB is plenty)

### Step 6: Create!

1. Review settings
2. Click **"Create"**
3. Wait 2-3 minutes for provisioning
4. Status will change to **"Running"** (green)

---

## Part 3: Configure Firewall (5 minutes)

### Step 1: Open Required Ports

Your VM needs internet access but doesn't need incoming connections (except SSH).

1. In your instance details, find **"Virtual Cloud Network"**
2. Click on the VCN name
3. Click **"Security Lists"** on the left
4. Click **"Default Security List"**

### Step 2: Verify Rules

**Ingress Rules (incoming):**
- SSH (port 22) should already be open
- That's all you need!

**Egress Rules (outgoing):**
- All traffic should be allowed (default)
- This lets your script connect to Binance

**Note:** You don't need to open any additional ports. Data collection only makes outgoing connections.

---

## Part 4: Connect to Your VM (5 minutes)

### Step 1: Get Connection Details

1. Go back to **Compute** → **Instances**
2. Click your instance name
3. Find **"Public IP address"** - copy this (e.g., 123.45.67.89)

### Step 2: Connect via SSH

**On Windows (using PowerShell):**

1. Move your private key to a safe location:
   ```powershell
   mkdir C:\Users\YourName\.ssh
   move oracle_key.key C:\Users\YourName\.ssh\
   ```

2. Set correct permissions:
   ```powershell
   icacls C:\Users\YourName\.ssh\oracle_key.key /inheritance:r
   icacls C:\Users\YourName\.ssh\oracle_key.key /grant:r "%username%:R"
   ```

3. Connect:
   ```powershell
   ssh -i C:\Users\YourName\.ssh\oracle_key.key ubuntu@YOUR_PUBLIC_IP
   ```

**Replace:**
- `YourName` with your Windows username
- `YOUR_PUBLIC_IP` with the IP from Step 1

**First time connecting:**
- You'll see: "Are you sure you want to continue connecting?"
- Type: `yes`

**You're in!** You should see:
```
ubuntu@m281m-data-collector:~$
```

---

## Part 5: Install Dependencies (10 minutes)

### Step 1: Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### Step 2: Install Python 3.11+

```bash
sudo apt install -y python3 python3-pip python3-venv
python3 --version  # Should show 3.10 or higher
```

### Step 3: Install Git

```bash
sudo apt install -y git
```

### Step 4: Create Working Directory

```bash
mkdir -p ~/m281m
cd ~/m281m
```

---

## Part 6: Upload Your Code (10 minutes)

### Option A: Using Git (If you have a repo)

```bash
git clone YOUR_REPO_URL
cd YOUR_REPO_NAME
```

### Option B: Manual Upload (Recommended)

**On your Windows laptop:**

1. Create a zip of your project:
   - Right-click `M281M` folder
   - Send to → Compressed (zipped) folder
   - Name it `m281m.zip`

2. Upload using SCP (from PowerShell):
   ```powershell
   scp -i C:\Users\YourName\.ssh\oracle_key.key C:\Path\To\m281m.zip ubuntu@YOUR_PUBLIC_IP:~/
   ```

**Back on the VM:**

```bash
# Install unzip
sudo apt install -y unzip

# Unzip
unzip m281m.zip
cd M281M  # or whatever your folder is named

# Verify files
ls -la
```

You should see your project files: `scripts/`, `src/`, `requirements.txt`, etc.

---

## Part 7: Setup Python Environment (5 minutes)

### Step 1: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** This will take 5-10 minutes on ARM. Be patient!

### Step 3: Create Data Directory

```bash
mkdir -p data/live
```

---

## Part 8: Start Data Collection (5 minutes)

### Step 1: Test the Script

```bash
python scripts/record_live_data.py
```

You should see:
```
Data Recorder initialized
Symbol: BTCUSDT
Starting data recording...
WebSocket connected successfully
```

Press `Ctrl+C` to stop (just testing).

### Step 2: Run in Background

**Use screen (keeps running after you disconnect):**

```bash
# Install screen
sudo apt install -y screen

# Start a new screen session
screen -S datacollection

# Run the script
python scripts/record_live_data.py
```

**To detach (leave it running):**
- Press `Ctrl+A` then `D`

**To reattach (check on it later):**
```bash
screen -r datacollection
```

**To stop:**
- Reattach with `screen -r datacollection`
- Press `Ctrl+C`

---

## Part 9: Verify It's Working (2 minutes)

### Check Files Being Created

```bash
ls -lh data/live/
```

You should see CSV files growing in size.

### Check Disk Space

```bash
df -h
```

You have 50GB, plenty for 2 weeks (~10-15GB needed).

### Monitor the Process

```bash
# Reattach to screen
screen -r datacollection

# You should see statistics updating every minute
```

---

## Part 10: Download Data After 2 Weeks

### When Collection is Complete

**On your Windows laptop (PowerShell):**

```powershell
# Download all data files
scp -i C:\Users\YourName\.ssh\oracle_key.key -r ubuntu@YOUR_PUBLIC_IP:~/M281M/data/live C:\Path\To\Local\M281M\data\
```

This will copy all CSV files back to your laptop.

---

## Maintenance & Monitoring

### Daily Check (30 seconds)

**Connect to VM:**
```bash
ssh -i C:\Users\YourName\.ssh\oracle_key.key ubuntu@YOUR_PUBLIC_IP
```

**Check status:**
```bash
screen -r datacollection  # See if it's running
ls -lh data/live/         # Check file sizes
df -h                     # Check disk space
```

**Detach:**
- Press `Ctrl+A` then `D`

### If Script Stops

**Restart it:**
```bash
cd ~/M281M
source venv/bin/activate
screen -S datacollection
python scripts/record_live_data.py
```

---

## Cost Monitoring

### Set Up Billing Alerts

1. Go to Oracle Cloud Console
2. Click profile icon (top right)
3. Go to **"Billing & Cost Management"**
4. Set up alerts for $1, $5, $10

**You should stay at $0** if you only use Always Free resources.

### Always Free Resources

**What you're using:**
- ✅ VM.Standard.A1.Flex (1 OCPU, 6GB RAM)
- ✅ 50GB boot volume
- ✅ 10TB outbound data transfer/month
- ✅ All compute hours

**All of this is Always Free - no expiration!**

---

## Troubleshooting

### Can't Create Instance?

**Error: "Out of capacity"**
- Try different Availability Domain
- Try different region
- Try at different time of day
- Use AMD instance instead (VM.Standard.E2.1.Micro - 1GB RAM)

### Can't Connect via SSH?

**Check:**
1. Public IP is correct
2. Private key file path is correct
3. Using `ubuntu` as username (not `root`)
4. Security list allows SSH (port 22)

### Script Crashes?

**Check logs:**
```bash
screen -r datacollection
# See error messages
```

**Common issues:**
- Out of memory (1GB RAM) - Use ARM instance (6GB)
- Network issues - Check internet connection
- Disk full - Check with `df -h`

---

## Security Best Practices

### 1. Keep Private Key Safe
- Don't share `oracle_key.key`
- Don't commit to Git
- Keep backup in safe location

### 2. Update System Regularly
```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Monitor Access
```bash
# Check who's logged in
who

# Check login history
last
```

### 4. Firewall
- Only SSH (port 22) should be open
- No other incoming ports needed

---

## After 2 Weeks

### Step 1: Stop Collection
```bash
screen -r datacollection
# Press Ctrl+C
```

### Step 2: Download Data
```powershell
scp -i C:\Users\YourName\.ssh\oracle_key.key -r ubuntu@YOUR_PUBLIC_IP:~/M281M/data/live C:\Path\To\Local\M281M\data\
```

### Step 3: Verify Data
On your laptop:
```bash
check_data_quality.bat
```

### Step 4: Keep or Delete VM

**Keep it:**
- It's free forever
- Use for future data collection
- Use for paper trading later

**Delete it:**
1. Go to Compute → Instances
2. Click ⋮ (three dots)
3. Click "Terminate"
4. Confirm

---

## Summary

**What you get:**
- ✅ Free VM (always free, no expiration)
- ✅ 6GB RAM (plenty for data collection)
- ✅ 50GB storage
- ✅ Runs 24/7 without your laptop
- ✅ Reliable internet connection

**Total cost:** $0

**Setup time:** ~1 hour

**Maintenance:** 30 seconds/day

---

## Quick Reference

**Connect:**
```bash
ssh -i ~/.ssh/oracle_key.key ubuntu@YOUR_PUBLIC_IP
```

**Check status:**
```bash
screen -r datacollection
```

**Detach:**
```
Ctrl+A then D
```

**Download data:**
```powershell
scp -i ~/.ssh/oracle_key.key -r ubuntu@YOUR_PUBLIC_IP:~/M281M/data/live ./data/
```

---

## Need Help?

Common issues and solutions are in the Troubleshooting section above.

**Ready to start?** Follow Part 1 and work your way through!

---

**Good luck! You'll have a professional data collection setup running 24/7 for free!** 🚀
