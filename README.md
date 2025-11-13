# DockShield

![DockShield Logo](docs/logo.png)

**DockShield** è un'applicazione desktop per KDE Plasma che consente di effettuare backup e ripristino di container Docker in modo semplice e intuitivo.

## Caratteristiche

✨ **Caratteristiche principali:**

- 🐳 **Gestione Container Docker**: Visualizza e seleziona facilmente i container presenti nel sistema
- 💾 **Backup Flessibili**:
  - Backup completo (immagine + configurazione + filesystem)
  - Backup solo filesystem (dati e volumi)
  - Compressione configurabile (0-9)
  - Verifica automatica dell'integrità
- 🔄 **Ripristino Semplice**: Ripristina container con un click, mantenendo o modificando la configurazione
- ⏰ **Scheduler Integrato**: Pianifica backup automatici con sintassi cron
- 🌐 **Destinazioni Multiple**:
  - Storage locale
  - NFS
  - SSH/SFTP
  - Cloud (AWS S3, Azure, Google Cloud)
- 🔔 **Notifiche KDE**: Notifiche desktop native per backup e ripristino
- 📊 **Storico Completo**: Visualizza tutti i backup effettuati con dettagli completi
- 🎨 **Tema Adattivo**: Supporto per tema chiaro/scuro automatico
- 🌍 **Pronto per i18n**: Struttura pronta per traduzioni multiple

## Requisiti

### Sistema Operativo

- Linux (testato su KDE Plasma 6.5+)
- Docker installato e in esecuzione

### Dipendenze Python

- Python 3.10+
- PyQt6 >= 6.5.0
- docker >= 7.0.0
- schedule >= 1.2.0
- paramiko >= 3.4.0
- pyyaml >= 6.0.1
- python-dateutil >= 2.8.2
- psutil >= 5.9.0
- cryptography >= 41.0.0

### Dipendenze Opzionali (Cloud Storage)

- boto3 >= 1.28.0 (AWS S3)
- google-cloud-storage >= 2.10.0 (Google Cloud)
- azure-storage-blob >= 12.19.0 (Azure)

## Installazione

### Flatpak (Raccomandato per utenti finali)

```bash
# Build e installa da sorgente
cd dockshield/flatpak
chmod +x build-flatpak.sh
./build-flatpak.sh

# Installa
flatpak install --user flatpak-repo com.dockshield.DockShield

# Esegui
flatpak run com.dockshield.DockShield
```

**Vantaggi Flatpak:**
- ✅ Funziona su tutte le distribuzioni Linux
- ✅ Dipendenze incluse, nessun conflitto
- ✅ Installazione pulita e isolata
- ✅ Facile disinstallazione

Vedi [flatpak/QUICK-START.md](flatpak/QUICK-START.md) per dettagli completi.

### Da Sorgente

```bash
# Clona il repository
git clone https://github.com/yourusername/dockshield.git
cd dockshield

# Crea ambiente virtuale (raccomandato)
python -m venv venv
source venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt

# Installa l'applicazione
pip install -e .

# Oppure usa setup.py
python setup.py install
```

### Installazione con pip

```bash
pip install dockshield
```

### Aggiungere utente al gruppo Docker (se necessario)

```bash
sudo usermod -aG docker $USER
# Logout e login per applicare le modifiche
```

## Utilizzo

### Avvio GUI

```bash
# Avvia l'applicazione
dockshield

# Oppure
dockshield-gui

# Con configurazione personalizzata
dockshield --config /path/to/config.yml

# Con livello di log personalizzato
dockshield --log-level DEBUG
```

### Configurazione

Copia il file di configurazione di esempio:

```bash
mkdir -p ~/.config/dockshield
cp config.example.yml ~/.config/dockshield/config.yml
```

Modifica il file di configurazione secondo le tue esigenze:

```yaml
# ~/.config/dockshield/config.yml

general:
  backup_dir: "/var/backups/dockshield"
  compression_level: 6
  retention_days: 30

docker:
  socket: "unix:///var/run/docker.sock"
  timeout: 300

backup:
  default_type: "full"
  include_logs: true
  verify_backup: true

storage:
  local:
    enabled: true
    path: "/var/backups/dockshield"

scheduler:
  enabled: true
  jobs:
    - name: "daily_backup"
      enabled: true
      schedule: "0 2 * * *"  # Ogni giorno alle 2:00
      containers:
        - "container1"
        - "container2"
      backup_type: "full"

notifications:
  desktop_enabled: true
  notify_success: true
  notify_failure: true
```

## Funzionalità Dettagliate

### Backup

L'applicazione supporta due tipi di backup:

1. **Backup Completo (Full)**:
   - Salva l'immagine Docker del container
   - Salva la configurazione (variabili d'ambiente, volumi, porte, reti)
   - Esporta il filesystem del container
   - Include i log del container (opzionale)

2. **Backup Filesystem**:
   - Esporta solo il filesystem del container
   - Più veloce e occupa meno spazio
   - Richiede che l'immagine sia disponibile per il ripristino

**Come effettuare un backup:**

1. Seleziona uno o più container dalla lista
2. Clicca su "Backup Selected"
3. Configura le opzioni di backup:
   - Tipo di backup (Full/Filesystem)
   - Livello di compressione (0-9)
   - Inclusione log
   - Verifica integrità
4. Clicca su "Start Backup"

### Ripristino

Il ripristino di un container può essere effettuato da un backup esistente:

1. Clicca su "Restore from Backup"
2. Seleziona il backup da ripristinare
3. Opzionalmente, specifica un nuovo nome per il container
4. Scegli se avviare il container dopo il ripristino
5. Clicca su "Restore"

**Note:**
- Per backup di tipo "filesystem", l'immagine originale deve essere disponibile
- I backup "full" contengono tutto il necessario per il ripristino

### Scheduler

Lo scheduler permette di automatizzare i backup:

```yaml
scheduler:
  enabled: true
  jobs:
    - name: "daily_backup"
      enabled: true
      schedule: "0 2 * * *"  # min hour day month weekday
      containers:
        - "container1"
        - "container2"
      backup_type: "full"
      storage_backend: "local"
      retention_days: 7
```

**Formato Schedule (Cron):**
- `0 2 * * *` - Ogni giorno alle 2:00
- `0 */6 * * *` - Ogni 6 ore
- `0 3 * * 0` - Ogni domenica alle 3:00

### Storage Backends

#### Local Storage

```yaml
storage:
  local:
    enabled: true
    path: "/var/backups/dockshield"
```

#### NFS Storage

```yaml
storage:
  nfs:
    enabled: true
    server: "nfs.example.com"
    export_path: "/exports/backups"
    mount_point: "/mnt/nfs_backups"
    mount_options: "vers=4,rw"
```

#### SSH/SFTP Storage

```yaml
storage:
  ssh:
    enabled: true
    host: "backup.example.com"
    port: 22
    username: "backup_user"
    key_file: "~/.ssh/id_rsa"
    remote_path: "/backups/dockshield"
```

#### AWS S3 Storage

```yaml
storage:
  s3:
    enabled: true
    bucket: "my-docker-backups"
    region: "us-east-1"
    access_key_id: "YOUR_ACCESS_KEY"
    secret_access_key: "YOUR_SECRET_KEY"
    prefix: "dockshield/"
    storage_class: "STANDARD_IA"
```

### Notifiche

L'applicazione invia notifiche desktop KDE per:

- Inizio backup
- Completamento backup (con dimensione)
- Errori durante il backup
- Inizio ripristino
- Completamento ripristino
- Errori durante il ripristino

Le notifiche possono essere configurate:

```yaml
notifications:
  desktop_enabled: true
  notify_success: true
  notify_failure: true
  sound_enabled: true
```

## Architettura

```
dockshield/
├── core/                    # Moduli core
│   ├── config.py           # Gestione configurazione
│   ├── docker_manager.py   # Interfaccia Docker
│   ├── backup_manager.py   # Gestione backup
│   └── restore_manager.py  # Gestione ripristino
├── scheduler/              # Scheduler backup automatici
│   └── scheduler.py
├── storage/                # Backend storage
│   ├── base.py            # Interfaccia base
│   ├── local.py           # Storage locale
│   ├── nfs.py             # Storage NFS
│   ├── ssh.py             # Storage SSH/SFTP
│   └── cloud.py           # Storage cloud (S3, Azure, GCS)
├── ui/                     # Interfaccia grafica
│   ├── main_window.py     # Finestra principale
│   ├── backup_dialog.py   # Dialog backup
│   ├── restore_dialog.py  # Dialog ripristino
│   └── history_dialog.py  # Dialog storico
├── utils/                  # Utility
│   ├── notifications.py   # Notifiche KDE
│   └── logger.py          # Logging
└── main.py                # Entry point applicazione
```

## Sviluppo

### Setup Ambiente di Sviluppo

```bash
# Clona repository
git clone https://github.com/yourusername/dockshield.git
cd dockshield

# Crea ambiente virtuale
python -m venv venv
source venv/bin/activate

# Installa dipendenze di sviluppo
pip install -r requirements.txt
pip install -e ".[dev]"

# Esegui test
pytest

# Formattazione codice
black dockshield/

# Linting
flake8 dockshield/

# Type checking
mypy dockshield/
```

### Contribuire

Contributi sono benvenuti! Per favore:

1. Fai fork del repository
2. Crea un branch per la tua feature (`git checkout -b feature/amazing-feature`)
3. Commit delle modifiche (`git commit -m 'Add amazing feature'`)
4. Push al branch (`git push origin feature/amazing-feature`)
5. Apri una Pull Request

## Troubleshooting

### Errore: "Cannot connect to Docker daemon"

Assicurati che:
- Docker sia in esecuzione: `systemctl status docker`
- Il tuo utente sia nel gruppo docker: `groups` (dovrebbe mostrare "docker")
- Il socket Docker sia accessibile: `ls -l /var/run/docker.sock`

Se necessario:
```bash
sudo usermod -aG docker $USER
# Logout e login
```

### Errore: "Permission denied" durante il backup

Assicurati che la directory di backup sia scrivibile:
```bash
sudo mkdir -p /var/backups/dockshield
sudo chown $USER:$USER /var/backups/dockshield
```

### Notifiche non funzionano

Verifica che kdialog o notify-send siano installati:
```bash
which kdialog
which notify-send

# Su Fedora/RHEL:
sudo dnf install kdialog libnotify

# Su Debian/Ubuntu:
sudo apt install kdialog libnotify-bin
```

## FAQ

**Q: Posso fare backup di container in esecuzione?**
A: Sì, l'applicazione può fare backup di container sia in esecuzione che fermi.

**Q: I backup includono i volumi?**
A: Sì, i backup includono tutto il filesystem del container, inclusi i dati nei volumi montati.

**Q: Posso ripristinare un backup su un'altra macchina?**
A: Sì, i backup "full" contengono tutto il necessario. Per backup "filesystem" serve l'immagine originale.

**Q: Quanto spazio occupano i backup?**
A: Dipende dalla dimensione del container e dal livello di compressione. Un container tipico di 500MB può essere compresso a ~100-200MB.

**Q: Posso escludere file dal backup?**
A: Sì, puoi configurare pattern di esclusione nel file di configurazione.

## Roadmap

- [ ] Supporto per backup incrementali
- [ ] Interfaccia web (opzionale)
- [ ] Supporto per Podman
- [ ] Export/import configurazioni
- [ ] Backup multi-container con dipendenze
- [ ] Crittografia backup
- [ ] Sincronizzazione cloud automatica
- [ ] Plugin system per storage backends custom

## Licenza

Questo progetto è rilasciato sotto licenza GPL-3.0. Vedi il file [LICENSE](LICENSE) per dettagli.

## Autori

DockShield Team

## Supporto

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/yourusername/dockshield/issues)
- 💬 **Discussioni**: [GitHub Discussions](https://github.com/yourusername/dockshield/discussions)
- 📧 **Email**: support@dockshield.org

## Ringraziamenti

- Docker per l'eccellente piattaforma di containerizzazione
- KDE Team per il fantastico desktop environment
- PyQt Team per i bindings Python di Qt
- Tutti i contributori open source

---

**Made with ❤️ for the KDE community**
