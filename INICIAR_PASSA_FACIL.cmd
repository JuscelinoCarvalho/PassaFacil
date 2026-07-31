@echo off
setlocal
cd /d "%~dp0"

echo Iniciando o Passa Facil...

powershell -NoProfile -Command "if (-not (Test-NetConnection 127.0.0.1 -Port 9000 -InformationLevel Quiet)) { Start-Process -FilePath 'C:\Program Files\Python312\python.exe' -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','9000' -WorkingDirectory '%~dp0apps\api' -WindowStyle Hidden }"

powershell -NoProfile -Command "if (-not (Test-NetConnection 127.0.0.1 -Port 9001 -InformationLevel Quiet)) { Start-Process -FilePath 'C:\Program Files\nodejs\node.exe' -ArgumentList 'node_modules\next\dist\bin\next','start','-p','9001' -WorkingDirectory '%~dp0apps\web' -WindowStyle Hidden }"

echo Aguardando os servicos...
powershell -NoProfile -Command "$ok=$false; 1..20 | ForEach-Object { if ((Test-NetConnection 127.0.0.1 -Port 9000 -InformationLevel Quiet) -and (Test-NetConnection 127.0.0.1 -Port 9001 -InformationLevel Quiet)) { $ok=$true; return }; Start-Sleep -Seconds 1 }; if ($ok) { Write-Host 'Passa Facil iniciado com sucesso.' -ForegroundColor Green; Start-Process 'http://localhost:9001/' } else { Write-Host 'Nao foi possivel iniciar todos os servicos.' -ForegroundColor Red; exit 1 }"

endlocal
