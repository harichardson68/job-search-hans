@echo off
echo Setting up Agent Hub...
echo.

cd /d "C:\Users\haric\Jobsearch"

echo Installing dependencies...
python -m pip install requests pillow --quiet

echo.
echo Creating desktop shortcut...

powershell -Command "$desktop = [Environment]::GetFolderPath('Desktop'); $ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut($desktop + '\Agent Hub.lnk'); $s.TargetPath = 'pythonw.exe'; $s.Arguments = 'C:\Users\haric\Jobsearch\agent_hub.py'; $s.WorkingDirectory = 'C:\Users\haric\Jobsearch'; $s.IconLocation = 'C:\Windows\System32\shell32.dll,25'; $s.Description = 'Hans Richardson Agent Hub'; $s.Save()"

echo.
echo Done! Agent Hub shortcut created on your Desktop.
echo Double-click "Agent Hub" on your Desktop to launch all four agents.
echo.
echo You can now delete the old Claudio and Learning Agents shortcuts
echo since Agent Hub replaces both of them!
echo.
pause
