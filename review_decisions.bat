@echo off
chcp 65001 > nul
cd /d "C:\Users\haric\Jobsearch"
python review_decisions.py
echo Decision review completed at %date% %time%
