@echo off
rem This script intercepts calls to python and uses new_venv's Python instead
"%~dp0new_venv\Scripts\python.exe" %* 