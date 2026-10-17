@echo off
setlocal
where vivado >nul 2>nul
if errorlevel 1 (
  echo Open a Vivado command shell or call the installation's settings64.bat first.
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch.ps1" %*
exit /b %errorlevel%
