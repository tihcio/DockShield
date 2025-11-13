# DockShield Flatpak - Guida Rapida

## Build e Installazione in 3 Passi

### 1. Prepara l'Ambiente

```bash
# Installa flatpak-builder (se non già installato)
# Fedora:
sudo dnf install flatpak flatpak-builder

# Ubuntu/Debian:
sudo apt install flatpak flatpak-builder

# Arch:
sudo pacman -S flatpak flatpak-builder

# Aggiungi Flathub
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

### 2. Build

```bash
cd dockshield/flatpak
chmod +x build-flatpak.sh
./build-flatpak.sh
```

Il processo richiederà alcuni minuti la prima volta.

### 3. Installa e Esegui

```bash
# Installa
flatpak install --user flatpak-repo com.dockshield.DockShield

# Esegui
flatpak run com.dockshield.DockShield
```

## ⚠️ IMPORTANTE: Requisiti Docker

Prima di usare DockShield (Flatpak o nativo), devi:

```bash
# 1. Installa Docker (se non già presente)
# Vedi: https://docs.docker.com/engine/install/

# 2. Avvia Docker
sudo systemctl start docker
sudo systemctl enable docker

# 3. Aggiungi il tuo utente al gruppo docker
sudo usermod -aG docker $USER

# 4. LOGOUT e LOGIN per applicare le modifiche
# (o esegui: newgrp docker)

# 5. Verifica
docker ps
# Dovrebbe funzionare senza sudo
```

## Distribuzione del Pacchetto

Dopo il build, avrai:
- `flatpak-repo/`: Repository locale Flatpak
- `DockShield.flatpak`: Bundle singolo file

### Distribuire il Bundle

Il file `DockShield.flatpak` può essere distribuito agli utenti:

```bash
# Gli utenti possono installarlo con:
flatpak install DockShield.flatpak

# Oppure con doppio click nel file manager
```

### Creare un Repository Pubblico

```bash
# Dopo il build, puoi pubblicare il repository:
python3 -m http.server --directory flatpak-repo 8000

# Gli utenti possono aggiungerlo con:
flatpak remote-add --user dockshield http://your-server:8000
flatpak install dockshield com.dockshield.DockShield
```

## Test del Pacchetto

```bash
# Esegui con log di debug
flatpak run com.dockshield.DockShield --log-level DEBUG

# Verifica che Docker funzioni
flatpak run --command=bash com.dockshield.DockShield
# Poi: docker ps
```

## Pubblicare su Flathub

Per rendere DockShield disponibile su Flathub (store Flatpak ufficiale):

1. Crea un fork: https://github.com/flathub/flathub
2. Aggiungi i file del manifest
3. Aggiungi screenshot
4. Crea una Pull Request

Requisiti:
- Screenshot di qualità
- Icona SVG o PNG (256x256 o superiore)
- Metainfo completo e validato
- Test su più distribuzioni

Guida completa: https://docs.flathub.org/docs/for-app-authors/submission

## Aggiornamenti

Per rilasciare una nuova versione:

```bash
# 1. Aggiorna il codice
# 2. Modifica la versione in com.dockshield.DockShield.metainfo.xml
# 3. Rebuild
cd flatpak
./build-flatpak.sh

# 4. Gli utenti aggiornano con:
flatpak update com.dockshield.DockShield
```

## Troubleshooting Rapido

### Problema: Build fallisce

```bash
# Pulisci tutto e riprova
rm -rf flatpak-build flatpak-repo DockShield.flatpak
./build-flatpak.sh
```

### Problema: "Cannot connect to Docker daemon"

```bash
# Verifica Docker sull'host
docker ps

# Se fallisce:
sudo usermod -aG docker $USER
# LOGOUT e LOGIN
```

### Problema: Runtime non trovato

```bash
flatpak install flathub org.kde.Platform//6.6
flatpak install flathub org.kde.Sdk//6.6
flatpak install flathub com.riverbankcomputing.PyQt.BaseApp//6.6
```

## Comandi Utili

```bash
# Lista applicazioni installate
flatpak list --app

# Info su DockShield
flatpak info com.dockshield.DockShield

# Permessi
flatpak info --show-permissions com.dockshield.DockShield

# Override permessi (se necessario)
flatpak override --user --filesystem=/custom/path com.dockshield.DockShield

# Rimuovi override
flatpak override --user --reset com.dockshield.DockShield

# Logs applicazione
flatpak run com.dockshield.DockShield 2>&1 | tee dockshield.log

# Disinstalla
flatpak uninstall com.dockshield.DockShield

# Pulisci runtime inutilizzati
flatpak uninstall --unused
```

## Percorsi File in Flatpak

All'interno del sandbox Flatpak:

- **Config**: `~/.var/app/com.dockshield.DockShield/config/dockshield/`
- **Data**: `~/.var/app/com.dockshield.DockShield/data/dockshield/`
- **Cache**: `~/.var/app/com.dockshield.DockShield/cache/`

Backup di default: `/var/backups/dockshield` (se accessibile)

## Vantaggi di Usare Flatpak

✅ **Portabilità**: Funziona su tutte le distribuzioni Linux
✅ **Isolamento**: Ambiente sandbox sicuro
✅ **Dipendenze**: Tutto incluso, nessun conflitto
✅ **Aggiornamenti**: Sistema centralizzato
✅ **Pulizia**: Disinstallazione completa senza residui

## Link Utili

- [Flatpak Documentation](https://docs.flatpak.org/)
- [Flathub](https://flathub.org/)
- [KDE Flatpak Guidelines](https://community.kde.org/Guidelines_and_HOWTOs/Flatpak)
- [DockShield GitHub](https://github.com/yourusername/dockshield)

## Supporto

Problemi? Apri un issue su GitHub con il tag `flatpak`:
https://github.com/yourusername/dockshield/issues
