# Guida all'Installazione di DockShield

Questa guida fornisce istruzioni dettagliate per installare DockShield su diverse distribuzioni Linux.

## Requisiti di Sistema

### Requisiti Hardware

- CPU: x86_64 o ARM64
- RAM: Minimo 2GB (consigliato 4GB)
- Spazio disco: 100MB per l'applicazione + spazio per backup

### Requisiti Software

- Linux con KDE Plasma 5.x o 6.x
- Docker 20.x o superiore
- Python 3.10 o superiore
- Qt 6.5 o superiore

## Installazione su Fedora/RHEL

```bash
# Installa Docker
sudo dnf install docker
sudo systemctl enable --now docker

# Installa dipendenze Python
sudo dnf install python3 python3-pip python3-devel

# Installa dipendenze Qt
sudo dnf install python3-PyQt6

# Installa DockShield
pip install dockshield

# Oppure da sorgente
git clone https://github.com/yourusername/dockshield.git
cd dockshield
pip install -e .

# Aggiungi utente al gruppo docker
sudo usermod -aG docker $USER

# Logout e login per applicare le modifiche
```

## Installazione su Debian/Ubuntu

```bash
# Installa Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Installa dipendenze
sudo apt update
sudo apt install python3 python3-pip python3-venv
sudo apt install python3-pyqt6

# Installa DockShield
pip install dockshield

# Oppure da sorgente
git clone https://github.com/yourusername/dockshield.git
cd dockshield
pip install -e .

# Aggiungi utente al gruppo docker
sudo usermod -aG docker $USER

# Logout e login
```

## Installazione su Arch Linux

```bash
# Installa Docker
sudo pacman -S docker
sudo systemctl enable --now docker

# Installa dipendenze Python
sudo pacman -S python python-pip python-pyqt6

# Installa DockShield
pip install dockshield

# Oppure da AUR (se disponibile)
yay -S dockshield

# Aggiungi utente al gruppo docker
sudo usermod -aG docker $USER

# Logout e login
```

## Installazione da Sorgente (Metodo Universale)

```bash
# 1. Installa Docker (se non già presente)
# Segui le istruzioni su: https://docs.docker.com/engine/install/

# 2. Clone repository
git clone https://github.com/yourusername/dockshield.git
cd dockshield

# 3. Crea ambiente virtuale (raccomandato)
python3 -m venv venv
source venv/bin/activate

# 4. Installa dipendenze
pip install -r requirements.txt

# 5. Installa applicazione
pip install -e .

# 6. Copia file di configurazione
mkdir -p ~/.config/dockshield
cp config.example.yml ~/.config/dockshield/config.yml

# 7. (Opzionale) Installa desktop entry
mkdir -p ~/.local/share/applications
cp dockshield.desktop ~/.local/share/applications/

# 8. Aggiungi utente al gruppo docker
sudo usermod -aG docker $USER
```

## Configurazione Post-Installazione

### 1. Crea Directory Backup

```bash
sudo mkdir -p /var/backups/dockshield
sudo chown $USER:$USER /var/backups/dockshield
```

### 2. Configura Permessi Docker

Verifica di avere accesso a Docker:

```bash
docker ps
```

Se ricevi un errore di permessi:

```bash
# Aggiungi utente al gruppo docker
sudo usermod -aG docker $USER

# Applica immediatamente (alternativa a logout/login)
newgrp docker

# Verifica
docker ps
```

### 3. Configura l'Applicazione

Edita il file di configurazione:

```bash
nano ~/.config/dockshield/config.yml
```

Modifica almeno:
- `general.backup_dir`: Directory per i backup
- `docker.socket`: Path al socket Docker (default va bene)
- `notifications.desktop_enabled`: true per abilitare notifiche

### 4. Test Installazione

```bash
# Avvia l'applicazione
dockshield

# Oppure con log dettagliati
dockshield --log-level DEBUG
```

## Installazione Storage Backends Opzionali

### AWS S3

```bash
pip install boto3

# Configura credenziali AWS
aws configure
```

### Google Cloud Storage

```bash
pip install google-cloud-storage

# Configura credenziali
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

### Azure Blob Storage

```bash
pip install azure-storage-blob

# Configura connection string
export AZURE_STORAGE_CONNECTION_STRING="<your-connection-string>"
```

## Aggiornamento

### Da pip

```bash
pip install --upgrade dockshield
```

### Da sorgente

```bash
cd dockshield
git pull origin main
pip install -e . --upgrade
```

## Disinstallazione

```bash
# Rimuovi pacchetto
pip uninstall dockshield

# Rimuovi configurazione (opzionale)
rm -rf ~/.config/dockshield
rm -rf ~/.local/share/dockshield

# Rimuovi desktop entry (opzionale)
rm ~/.local/share/applications/dockshield.desktop

# Rimuovi backup (ATTENZIONE!)
# sudo rm -rf /var/backups/dockshield
```

## Troubleshooting Installazione

### Errore: "docker: command not found"

Docker non è installato. Segui le istruzioni di installazione per la tua distribuzione.

### Errore: "permission denied while trying to connect to Docker"

```bash
# Aggiungi utente al gruppo docker
sudo usermod -aG docker $USER

# Logout e login, oppure:
newgrp docker
```

### Errore: "PyQt6 not found"

```bash
# Fedora
sudo dnf install python3-PyQt6

# Ubuntu/Debian
sudo apt install python3-pyqt6

# Arch
sudo pacman -S python-pyqt6

# O via pip
pip install PyQt6
```

### Errore: "No module named 'docker'"

```bash
pip install docker
```

### L'applicazione non si avvia

1. Verifica i log:
   ```bash
   cat ~/.local/share/dockshield/dockshield.log
   ```

2. Avvia con debug:
   ```bash
   dockshield --log-level DEBUG
   ```

3. Verifica le dipendenze:
   ```bash
   pip list | grep -E 'docker|PyQt6|schedule'
   ```

## Supporto

Se riscontri problemi durante l'installazione:

1. Controlla i log: `~/.local/share/dockshield/dockshield.log`
2. Cerca issue esistenti: https://github.com/yourusername/dockshield/issues
3. Apri un nuovo issue con:
   - Output di `dockshield --version`
   - Distribuzione Linux e versione
   - Messaggi di errore completi
   - Log rilevanti

## Prossimi Passi

Dopo l'installazione:

1. Leggi il [README.md](../README.md) per le funzionalità
2. Consulta la [documentazione](../docs/) per guide dettagliate
3. Configura backup automatici con lo scheduler
4. Esplora le opzioni di storage remoto
