@echo off
echo Setting up Learning Agents...
echo.

cd /d "C:\Users\haric\Jobsearch"

echo Installing dependencies...
python -m pip install requests pillow --quiet

echo.
echo Creating desktop shortcut...

powershell -Command "$desktop = [Environment]::GetFolderPath('Desktop'); $ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut($desktop + '\Learning Agents.lnk'); $s.TargetPath = 'pythonw.exe'; $s.Arguments = 'C:\Users\haric\Jobsearch\learning_agents.py'; $s.WorkingDirectory = 'C:\Users\haric\Jobsearch'; $s.IconLocation = 'C:\Windows\System32\shell32.dll,25'; $s.Description = 'Hans Richardson Learning Agents'; $s.Save()"

echo.
echo Done! Learning Agents shortcut created on your Desktop.
echo Double-click it to launch all three learning agents.
echo.
pause
