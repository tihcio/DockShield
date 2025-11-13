# Come Creare un'Icona per DockShield

L'applicazione necessita di un'icona per:
- Desktop entry
- Notifiche
- Flathub submission
- Branding generale

## Requisiti Icona

### Per Flatpak/Flathub
- **Formato**: SVG (preferito) o PNG
- **Dimensione**: 256x256 px minimo (per PNG)
- **Stile**: Seguire le [linee guida KDE](https://develop.kde.org/hig/style/icons/)

### Linee Guida Design

L'icona dovrebbe rappresentare:
- 🐳 Docker (container, whale logo)
- 🛡️ Protezione/Shield (backup, sicurezza)
- 💾 Storage/Backup

## Idee Design

### Concept 1: Shield + Docker Whale
```
Un piccolo whale Docker dentro/dietro uno scudo
Colori: Blu Docker (#2496ED) + colori KDE
```

### Concept 2: Container + Frecce Backup
```
Container stilizzato con frecce circolari (backup/restore)
Stile iconografico minimale KDE
```

### Concept 3: Scudo con Logo Docker
```
Scudo con simbolo Docker o container
Design pulito e riconoscibile
```

## Strumenti per Creare l'Icona

### Inkscape (Raccomandato per SVG)
```bash
# Installa Inkscape
sudo dnf install inkscape  # Fedora
sudo apt install inkscape  # Ubuntu

# Crea icona SVG
inkscape &
# File > Proprietà documento > 256x256 px
# Disegna l'icona
# Salva come: dockshield/resources/icons/dockshield.svg
```

### GIMP (Per PNG)
```bash
# Installa GIMP
sudo dnf install gimp  # Fedora
sudo apt install gimp  # Ubuntu

# Crea nuovo progetto 256x256 px
# Disegna l'icona
# Esporta come PNG
# Salva in: dockshield/resources/icons/dockshield.png
```

### Krita (Alternativa KDE)
```bash
sudo dnf install krita
# Ottimo per design digitale
```

## Template SVG Base

Salva questo come `dockshield/resources/icons/dockshield.svg`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <!-- Background circle -->
  <circle cx="128" cy="128" r="120" fill="#3daee9" opacity="0.2"/>

  <!-- Shield shape -->
  <path d="M 128,40 L 60,70 L 60,140 L 128,210 L 196,140 L 196,70 Z"
        fill="#3daee9"
        stroke="#31363b"
        stroke-width="4"/>

  <!-- Docker container symbol (simplified) -->
  <rect x="98" y="100" width="60" height="50"
        fill="#ffffff"
        stroke="#31363b"
        stroke-width="2"/>
  <line x1="98" y1="115" x2="158" y2="115"
        stroke="#31363b"
        stroke-width="2"/>
  <line x1="98" y1="130" x2="158" y2="130"
        stroke="#31363b"
        stroke-width="2"/>

  <!-- Backup arrow (circular) -->
  <path d="M 165,125 A 30,30 0 1,1 165,135"
        fill="none"
        stroke="#27ae60"
        stroke-width="4"
        stroke-linecap="round"/>
  <polygon points="168,122 175,125 168,128"
           fill="#27ae60"/>
</svg>
```

## Dimensioni Multiple (Opzionale)

Per una perfetta integrazione, crea più dimensioni:

```bash
# Usa Inkscape per esportare da SVG a PNG in varie dimensioni
inkscape dockshield.svg --export-filename=dockshield-16.png -w 16 -h 16
inkscape dockshield.svg --export-filename=dockshield-22.png -w 22 -h 22
inkscape dockshield.svg --export-filename=dockshield-32.png -w 32 -h 32
inkscape dockshield.svg --export-filename=dockshield-48.png -w 48 -h 48
inkscape dockshield.svg --export-filename=dockshield-64.png -w 64 -h 64
inkscape dockshield.svg --export-filename=dockshield-128.png -w 128 -h 128
inkscape dockshield.svg --export-filename=dockshield-256.png -w 256 -h 256
```

## Posizionamento File

```
dockshield/resources/icons/
├── dockshield.svg           # Principale (per Flatpak)
├── hicolor/
│   ├── 16x16/apps/dockshield.png
│   ├── 22x22/apps/dockshield.png
│   ├── 32x32/apps/dockshield.png
│   ├── 48x48/apps/dockshield.png
│   ├── 64x64/apps/dockshield.png
│   ├── 128x128/apps/dockshield.png
│   └── 256x256/apps/dockshield.png
└── scalable/apps/dockshield.svg
```

## Installazione Icona

### Per Flatpak

Nel manifest `com.dockshield.DockShield.yml`, aggiungi:

```yaml
- name: dockshield
  buildsystem: simple
  build-commands:
    # ... altri comandi ...

    # Installa icona SVG
    - install -Dm644 dockshield/resources/icons/dockshield.svg
        ${FLATPAK_DEST}/share/icons/hicolor/scalable/apps/${FLATPAK_ID}.svg

    # O PNG multipli
    - install -Dm644 dockshield/resources/icons/hicolor/*/apps/*.png
        -t ${FLATPAK_DEST}/share/icons/hicolor/
```

### Per Installazione Nativa

Nel `setup.py`, l'icona è già configurata in `package_data`.

## Test Icona

```bash
# Dopo l'installazione, verifica
ls ~/.local/share/icons/hicolor/*/apps/dockshield.*

# Per Flatpak
flatpak run --command=ls com.dockshield.DockShield
    /app/share/icons/hicolor/scalable/apps/

# Aggiorna cache icone
gtk-update-icon-cache ~/.local/share/icons/hicolor/
```

## Risorse Design

### Ispirazione
- [KDE Visual Design Group](https://community.kde.org/Get_Involved/design)
- [Breeze Icons](https://github.com/KDE/breeze-icons)
- [Docker Branding](https://www.docker.com/company/newsroom/media-resources)

### Colori KDE Breeze
- Blu primario: `#3daee9`
- Blu scuro: `#1d99f3`
- Sfondo: `#31363b`
- Testo: `#eff0f1`
- Verde: `#27ae60`
- Rosso: `#ed1515`

### Font
Per eventuali testi nell'icona:
- **Noto Sans** (default KDE)
- **Oxygen** (legacy KDE)

## Alternative Rapide

Se non hai tempo/skill per design grafico:

### 1. Usa Placeholder Temporaneo
```bash
# Copia un'icona esistente simile
cp /usr/share/icons/breeze/apps/256/utilities-system-monitor.svg
   dockshield/resources/icons/dockshield.svg
```

### 2. Genera con AI
- DALL-E, Midjourney, Stable Diffusion
- Prompt: "minimal flat icon of docker whale with shield, KDE Breeze style, SVG"

### 3. Commissiona a Designer
- Fiverr, Upwork
- Budget: $20-50 per un'icona professionale

### 4. Usa Icon Generator Online
- https://www.favicon-generator.org/
- https://iconifier.net/
- Carica un'immagine Docker + Shield e genera

## Validazione Icona

Prima di pubblicare su Flathub:

```bash
# Valida SVG
xmllint --noout dockshield/resources/icons/dockshield.svg

# Verifica dimensioni PNG
identify dockshield/resources/icons/dockshield.png
# Dovrebbe essere almeno 256x256

# Test visivo
eog dockshield/resources/icons/dockshield.svg  # GNOME
gwenview dockshield/resources/icons/dockshield.svg  # KDE
```

## Checklist Finale

Prima di pubblicare:

- [ ] Icona creata in formato SVG
- [ ] Dimensione adeguata (256x256+)
- [ ] Colori compatibili con tema chiaro/scuro
- [ ] Testata su background chiaro e scuro
- [ ] File salvato in `dockshield/resources/icons/`
- [ ] Manifest Flatpak aggiornato
- [ ] Cache icone aggiornata dopo installazione
- [ ] Icona visibile nel menu applicazioni
- [ ] Icona appare nelle notifiche

## Note Legali

⚠️ **Attenzione Copyright:**
- Non usare il logo Docker ufficiale senza permesso
- Ispirazione OK, copia esatta NO
- Crea un design originale o usa elementi generici
- Verifica la licenza di eventuali risorse usate

---

Una volta creata l'icona, aggiornala nel manifest Flatpak decommentando le righe appropriate!
