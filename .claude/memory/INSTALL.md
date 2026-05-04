# Ripristino memoria su nuovo PC

Dopo aver clonato il repo, copia questa cartella nella posizione corretta:

```
%USERPROFILE%\.claude\projects\c--Users-globalgeo-Desktop-WIP\memory\
```

Comando PowerShell:
```powershell
$dest = "$env:USERPROFILE\.claude\projects\c--Users-globalgeo-Desktop-WIP\memory"
New-Item -ItemType Directory -Path $dest -Force
Copy-Item "$PWD\.claude\memory\*" $dest -Force
```

Eseguilo dalla cartella radice del repo clonato.
