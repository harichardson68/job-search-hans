@echo off
chcp 65001 > nul
cd /d "C:\Users\haric\Jobsearch"
python job_search.py 
echo Job search completed at %date% %time% 
