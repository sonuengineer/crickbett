@echo off
title CricketArb - Stopping
echo.
echo  Stopping CricketArb...
echo.
taskkill /fi "WINDOWTITLE eq CricketArb Backend*" /f 2>nul
taskkill /fi "WINDOWTITLE eq CricketArb Worker*" /f 2>nul
taskkill /fi "WINDOWTITLE eq CricketArb Beat*" /f 2>nul
taskkill /fi "WINDOWTITLE eq CricketArb Frontend*" /f 2>nul
cd /d g:\sonu\CricketArb
docker-compose down
echo.
echo  All services stopped.
pause
