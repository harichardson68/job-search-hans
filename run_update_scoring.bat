@echo off
chcp 65001 > nul
cd /d "C:\Users\haric\Jobsearch"
python update_scoring.py
echo Update scoring completed at %date% %time%