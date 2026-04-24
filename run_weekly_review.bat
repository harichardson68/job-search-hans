@echo off
chcp 65001 > nul
cd /d "C:\Users\haric\Jobsearch"
python weekly_review.py
echo Weekly review completed at %date% %time%
