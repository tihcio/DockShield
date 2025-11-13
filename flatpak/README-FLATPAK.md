# DockShield Flatpak

Questa directory contiene i file necessari per creare un pacchetto Flatpak di DockShield.

## Prerequisiti

### Installare Flatpak e flatpak-builder

#### Fedora/RHEL
```bash
sudo dnf install flatpak flatpak-builder
```

#### Ubuntu/Debian
```bash
sudo apt install flatpak flatpak-builder
```

#### Arch Linux
```bash
sudo pacman -S flatpak flatpak-builder
```

### Aggiungere Flathub repository

```bash
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

## Build del Pacchetto

### Metodo Automatico (Raccomandato)

```bash
cd flatpak
chmod +x build-flatpak.sh
./build-flatpak.sh
```

Lo script:
1. Verifica le dipendenze necessarie
2. Installa i runtime KDE se mancanti
3. Compila il pacchetto Flatpak
4. Crea un bundle `.flatpak` per la distribuzione

### Metodo Manuale

```bash
# 1. Installa runtime e SDK
flatpak install flathub org.kde.Platform//6.6
flatpak install flathub org.kde.Sdk//6.6
flatpak install flathub com.riverbankcomputing.PyQt.BaseApp//6.6

# 2. Build
flatpak-builder --force-clean --repo=flatpak-repo flatpak-build ../com.dockshield.DockShield.yml

# 3. Crea bundle (opzionale)
flatpak build-bundle flatpak-repo DockShield.flatpak com.dockshield.DockShield

# 4. Installa localmente
flatpak install --user flatpak-repo com.dockshield.DockShield
```

## Installazione

### Da Repository Locale

```bash
flatpak install --user flatpak-repo com.dockshield.DockShield
```

### Da Bundle

```bash
flatpak install --user DockShield.flatpak
```

## Esecuzione

```bash
flatpak run com.dockshield.DockShield
```

O semplicemente cerca "DockShield" nel menu applicazioni KDE.

## Considerazioni Importanti su Docker e Flatpak

### Accesso al Docker Daemon

DockShield ha bisogno di accedere al Docker daemon dell'host. Il manifest Flatpak include i permessi necessari:

```yaml
finish-args:
  - --filesystem=/var/run/docker.sock  # Accesso al socket Docker
  - --filesystem=home                   # Per salvare backup nella home
  - --share=network                     # Per storage remoti
```

### Limitazioni del Sandbox

Flatpak esegue le applicazioni in un ambiente sandbox. Per DockShield, abbiamo configurato:

1. **Accesso Docker Socket**: Permette la comunicazione con il Docker daemon
2. **Accesso Filesystem**: Per leggere/scrivere backup
3. **Accesso Network**: Per backup remoti (SSH, S3, etc.)
4. **Notifiche System**: Per le notifiche KDE native

### Requisiti Host

Anche con Flatpak, l'host deve avere:
- Docker installato e in esecuzione
- L'utente deve essere nel gruppo `docker`
- Il socket `/var/run/docker.sock` deve essere accessibile

```bash
# Verifica Docker
docker ps

# Se fallisce, aggiungi utente al gruppo docker
sudo usermod -aG docker $USER
# Poi logout e login
```

## Aggiornamento

```bash
# Rebuild
cd flatpak
./build-flatpak.sh

# Update installazione
flatpak update com.dockshield.DockShield
```

## Disinstallazione

```bash
flatpak uninstall com.dockshield.DockShield

# Rimuovi anche dati utente (opzionale)
rm -rf ~/.var/app/com.dockshield.DockShield
```

## Pubblicazione su Flathub

Per pubblicare DockShield su Flathub:

1. Fork del repository Flathub: https://github.com/flathub/flathub
2. Crea una PR con il manifest e i file necessari
3. Segui le linee guida: https://docs.flathub.org/docs/for-app-authors/submission

### File necessari per Flathub

- `com.dockshield.DockShield.yml` (manifest)
- `com.dockshield.DockShield.metainfo.xml` (AppStream metadata)
- Screenshot dell'applicazione
- Icona SVG o PNG ad alta risoluzione

## Debugging

### Esegui con log dettagliati

```bash
flatpak run --verbose com.dockshield.DockShield --log-level DEBUG
```

### Accedi alla sandbox

```bash
flatpak run --command=bash com.dockshield.DockShield

# Poi all'interno:
ls -la /var/run/docker.sock
docker ps
```

### Verifica permessi

```bash
flatpak info --show-permissions com.dockshield.DockShield
```

### Log applicazione

I log sono salvati in:
```
~/.var/app/com.dockshield.DockShield/data/dockshield/dockshield.log
```

## Troubleshooting

### Errore: "Cannot connect to Docker daemon"

1. Verifica Docker sull'host:
   ```bash
   docker ps
   ```

2. Verifica permessi socket:
   ```bash
   ls -la /var/run/docker.sock
   ```

3. Verifica che Flatpak abbia accesso:
   ```bash
   flatpak run --command=bash com.dockshield.DockShield
   # Poi: ls -la /var/run/docker.sock
   ```

### Build fallisce con errori di rete

Se sei dietro un proxy:
```bash
export http_proxy="http://proxy:port"
export https_proxy="http://proxy:port"
flatpak-builder --force-clean ...
```

### Runtime non trovato

```bash
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install flathub org.kde.Platform//6.6
flatpak install flathub org.kde.Sdk//6.6
```

## Differenze tra Flatpak e Installazione Nativa

| Aspetto | Flatpak | Nativo |
|---------|---------|--------|
| Installazione | Sandbox isolato | Sistema globale |
| Dipendenze | Incluse nel pacchetto | Gestite dal sistema |
| Aggiornamenti | Tramite Flatpak | Tramite pip/package manager |
| Permessi | Controllati da Flatpak | Permessi utente normali |
| Config | `~/.var/app/com.dockshield.DockShield/config/dockshield/` | `~/.config/dockshield/` |
| Data | `~/.var/app/com.dockshield.DockShield/data/dockshield/` | `~/.local/share/dockshield/` |

## Vantaggi Flatpak

- ✅ Installazione pulita e isolata
- ✅ Stesse dipendenze su tutte le distro
- ✅ Facile disinstallazione completa
- ✅ Aggiornamenti centralizzati
- ✅ Sicurezza migliorata (sandbox)

## Svantaggi Flatpak

- ❌ Occupazione spazio maggiore (runtime incluso)
- ❌ Complessità nell'accesso Docker (richiede permessi speciali)
- ❌ Possibili problemi di permessi con file system

## Supporto

Per problemi specifici a Flatpak:
- GitHub Issues: https://github.com/yourusername/dockshield/issues
- Tag issue con `flatpak` label

## Risorse

- Documentazione Flatpak: https://docs.flatpak.org/
- KDE Flatpak Guidelines: https://community.kde.org/Guidelines_and_HOWTOs/Flatpak
- Flathub: https://flathub.org/
- PyQt BaseApp: https://github.com/flathub/com.riverbankcomputing.PyQt.BaseApp
