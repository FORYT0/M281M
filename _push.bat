@echo off
set GIT=C:\Program Files\Git\cmd\git.exe
set REPO=C:\Users\User\AndroidStudioProjects\M281M

cd /d "%REPO%"

echo [1] Init git
"%GIT%" init

echo [2] Config
"%GIT%" config user.email "m281m@trading.ai"
"%GIT%" config user.name "M281M"

echo [3] Set remote
"%GIT%" remote remove origin 2>nul
"%GIT%" remote add origin https://github.com/FORYT0/M281M.git

echo [4] Stage all
"%GIT%" add -A

echo [5] Status
"%GIT%" status --short

echo [6] Commit
"%GIT%" commit -m "feat: improved UI v2 - dark themed dashboards for both monitors"

echo [7] Branch main
"%GIT%" branch -M main

echo [8] Push
"%GIT%" push -u origin main --force

echo [9] Done
"%GIT%" log --oneline -5
