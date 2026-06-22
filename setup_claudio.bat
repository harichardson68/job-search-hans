@echo off
echo Setting up Claudio Job Search Agent...
echo.

cd /d "C:\Users\haric\Jobsearch"

echo Installing dependencies...
python -m pip install pystray pillow requests --quiet

echo.
echo Creating desktop shortcut...

powershell -Command "$desktop = [Environment]::GetFolderPath('Desktop'); $ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut($desktop + '\Claudio.lnk'); $s.TargetPath = 'pythonw.exe'; $s.Arguments = 'C:\Users\haric\Jobsearch\claudio_agent.py'; $s.WorkingDirectory = 'C:\Users\haric\Jobsearch'; $s.IconLocation = 'C:\Windows\System32\shell32.dll,13'; $s.Description = 'Claudio Job Search Agent'; $s.Save()"

echo.
echo Done! Claudio shortcut created on your Desktop.
echo Double-click it to launch your job search agent.
echo.
pause
