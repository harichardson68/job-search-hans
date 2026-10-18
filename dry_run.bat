@echo off
chcp 65001 > nul
cd /d "C:\Users\haric\Jobsearch"
if not exist dry_run mkdir dry_run
echo Dry run started %date% %time% > dry_run\run.log
python -u job_search.py --dry-run >> dry_run\run.log 2>&1
echo DRY RUN FINISHED %date% %time% >> dry_run\run.log
