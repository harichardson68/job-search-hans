@echo off
chcp 65001 > nul
cd /d "C:\Users\haric\Jobsearch"
set PYTHONIOENCODING=utf-8
if not exist dry_run mkdir dry_run
echo Dry run started %date% %time% > dry_run\run.log
echo Pulling latest code... >> dry_run\run.log
git pull >> dry_run\run.log 2>&1
python learn_weights.py >> dry_run\run.log 2>&1
python -u job_search.py --dry-run --email >> dry_run\run.log 2>&1
echo DRY RUN FINISHED %date% %time% >> dry_run\run.log
echo.
echo Test run finished. Check your email for the [TEST] digest.
pause
