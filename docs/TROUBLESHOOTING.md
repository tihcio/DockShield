# DockShield - Guida al Troubleshooting

Questa guida aiuta a risolvere i problemi più comuni di DockShield.

## Problemi di Ripristino

### ❌ "Errore sconosciuto durante il ripristino"

**Causa**: Bug nella versione precedente del `restore_manager.py` che non implementava correttamente il ripristino del filesystem.

**Soluzione**: Aggiorna all'ultima versione. Il bug è stato corretto implementando correttamente il metodo `put_archive()` di Docker.

---

### ❌ "Un container con nome 'xxx' esiste già"

**Causa**: Un container con lo stesso nome è già presente nel sistema.

**Soluzioni**:

1. **Usa un nome diverso**: Nel dialog di ripristino, specifica un nuovo nome nel campo "New Container Name"

2. **Rimuovi il container esistente**:
   ```bash
   docker rm -f nome_container
   ```

3. **Rinomina il container esistente**:
   ```bash
   docker rename vecchio_nome nuovo_nome
   ```

---

### ❌ "Image not found: xxx"

**Causa**: L'immagine Docker necessaria non è disponibile sul sistema (solo per backup tipo "filesystem").

**Soluzioni**:

1. **Scarica l'immagine**:
   ```bash
   docker pull nome_immagine:tag
   ```

2. **Usa un backup "full"**: I backup completi includono l'immagine e non hanno questo problema.

---

### ❌ "Backup non trovato"

**Causa**: Il backup non esiste più o la directory è stata spostata/cancellata.

**Verifica**:
```bash
ls -la /var/backups/dockshield/
# O la tua directory custom configurata
```

**Soluzioni**:
- Verifica che il backup esista realmente
- Controlla la configurazione in `~/.config/dockshield/config.yml`
- Ripristina il backup da un'altra posizione se disponibile

---

### ❌ "Decompressione archivio fallita"

**Causa**: File backup corrotto o permessi insufficienti.

**Soluzioni**:

1. **Verifica integrità backup**:
   - Apri DockShield e vai in "View History"
   - Controlla i checksum del backup

2. **Verifica permessi**:
   ```bash
   ls -la /var/backups/dockshield/backup_id/
   # Deve essere leggibile dal tuo utente
   ```

3. **Verifica spazio disco**:
   ```bash
   df -h
   ```

---

### ❌ "put_archive ha ritornato False"

**Causa**: Problema durante l'estrazione del filesystem nel container.

**Possibili cause e soluzioni**:

1. **Container non in esecuzione**: Il container potrebbe essere stato fermato durante il ripristino
   - Verifica lo stato: `docker ps -a`

2. **Spazio disco insufficiente**:
   ```bash
   df -h
   docker system df
   ```

3. **Permessi Docker**:
   ```bash
   docker info
   # Se fallisce, controlla gruppo docker
   groups | grep docker
   ```

---

## Problemi di Backup

### ❌ "Cannot connect to Docker daemon"

**Causa**: DockShield non può connettersi al Docker daemon.

**Soluzioni**:

1. **Verifica che Docker sia in esecuzione**:
   ```bash
   systemctl status docker
   ```

2. **Avvia Docker**:
   ```bash
   sudo systemctl start docker
   ```

3. **Verifica permessi utente**:
   ```bash
   groups | grep docker
   ```

   Se non vedi "docker":
   ```bash
   sudo usermod -aG docker $USER
   # LOGOUT e LOGIN
   ```

4. **Per Flatpak**: Verifica che il socket Docker sia accessibile:
   ```bash
   flatpak run --command=bash com.dockshield.DockShield
   ls -la /var/run/docker.sock
   ```

---

### ❌ "Permission denied" durante backup

**Causa**: Permessi insufficienti per scrivere nella directory di backup.

**Soluzioni**:

1. **Crea/correggi permessi directory**:
   ```bash
   sudo mkdir -p /var/backups/dockshield
   sudo chown $USER:$USER /var/backups/dockshield
   ```

2. **Usa directory alternativa**:
   Modifica `~/.config/dockshield/config.yml`:
   ```yaml
   general:
     backup_dir: "/home/$USER/dockshield-backups"
   ```

---

### ❌ Backup molto lento

**Causa**: Container con molti dati o compressione troppo alta.

**Soluzioni**:

1. **Riduci livello compressione**: Nel dialog backup, usa livello 3-4 invece di 6-9

2. **Escludi file non necessari**: Modifica config:
   ```yaml
   backup:
     exclude_patterns:
       - "*.tmp"
       - "*.log"
       - "cache/*"
       - "tmp/*"
   ```

3. **Usa backup "filesystem"**: Più veloce del "full" se non serve l'immagine

---

## Problemi Interfaccia Grafica

### ❌ Notifiche non funzionano

**Causa**: `kdialog` o `notify-send` non disponibili.

**Soluzioni**:

1. **Installa kdialog** (KDE):
   ```bash
   sudo dnf install kdialog  # Fedora
   sudo apt install kdialog  # Ubuntu
   ```

2. **Installa notify-send** (fallback):
   ```bash
   sudo dnf install libnotify  # Fedora
   sudo apt install libnotify-bin  # Ubuntu
   ```

3. **Disabilita notifiche** (se non le vuoi):
   ```yaml
   notifications:
     desktop_enabled: false
   ```

---

### ❌ Tema scuro non funziona

**Causa**: Tema non applicato correttamente.

**Soluzione**: Modifica config:
```yaml
ui:
  theme: "dark"  # o "light" o "auto"
```

Riavvia l'applicazione.

---

### ❌ Container non appaiono nella lista

**Causa**: Docker non in esecuzione o permessi insufficienti.

**Verifica**:
```bash
docker ps -a
```

Se funziona da terminale ma non in DockShield:
- Riavvia DockShield
- Controlla log: `~/.local/share/dockshield/dockshield.log`

---

## Problemi di Installazione

### ❌ "ModuleNotFoundError: No module named 'docker'"

**Causa**: Dipendenze Python non installate.

**Soluzione**:
```bash
pip install -r requirements.txt
```

O per Flatpak, rebuilda:
```bash
cd flatpak
./build-flatpak.sh
```

---

### ❌ "No module named 'PyQt6'"

**Causa**: PyQt6 non installato.

**Soluzioni**:

1. **Via sistema**:
   ```bash
   sudo dnf install python3-PyQt6  # Fedora
   sudo apt install python3-pyqt6  # Ubuntu
   ```

2. **Via pip**:
   ```bash
   pip install PyQt6
   ```

---

## Problemi Scheduler

### ❌ Backup automatici non partono

**Causa**: Scheduler non abilitato o configurazione errata.

**Verifica configurazione**:
```yaml
scheduler:
  enabled: true
  jobs:
    - name: "daily_backup"
      enabled: true
      schedule: "0 2 * * *"
      containers:
        - "container_name"
```

**Verifica che l'applicazione sia in esecuzione**: Lo scheduler funziona solo mentre DockShield è aperto.

**Soluzione alternativa**: Usa cron di sistema:
```bash
crontab -e
# Aggiungi:
0 2 * * * flatpak run com.dockshield.DockShield --backup-job daily
```

---

## Debug Avanzato

### Abilitare Log Dettagliati

**Via riga di comando**:
```bash
dockshield --log-level DEBUG
```

**O Flatpak**:
```bash
flatpak run com.dockshield.DockShield --log-level DEBUG
```

**Via configurazione**:
```yaml
general:
  log_level: "DEBUG"
```

### Visualizzare Log

```bash
# Installazione nativa
tail -f ~/.local/share/dockshield/dockshield.log

# Flatpak
tail -f ~/.var/app/com.dockshield.DockShield/data/dockshield/dockshield.log
```

### Eseguire Backup/Restore da CLI (per debug)

```python
python3 -c "
from dockshield.core.config import Config
from dockshield.core.docker_manager import DockerManager
from dockshield.core.backup_manager import BackupManager
from pathlib import Path

config = Config()
docker_mgr = DockerManager()
backup_mgr = BackupManager(docker_mgr, Path('/tmp/test-backup'))

container = docker_mgr.get_container('nome_container')
result = backup_mgr.create_backup(container, 'full', 6, True, True)
print(result)
"
```

---

## Segnalare Bug

Se il problema persiste:

1. **Raccogli informazioni**:
   ```bash
   dockshield --version
   docker --version
   python --version
   uname -a
   ```

2. **Salva log**:
   ```bash
   cp ~/.local/share/dockshield/dockshield.log ~/dockshield-error.log
   ```

3. **Apri issue** su GitHub: https://github.com/yourusername/dockshield/issues
   - Includi versioni
   - Allega log
   - Descrivi passi per riprodurre

---

## Contatti

- **GitHub Issues**: https://github.com/yourusername/dockshield/issues
- **Email**: support@dockshield.org
- **Documentazione**: https://github.com/yourusername/dockshield/wiki
