# Changelog

Tutte le modifiche notevoli a questo progetto saranno documentate in questo file.


## [0.6.0] - 2025-11-13 (Beta)

### ✨ Nuove Funzionalità

#### Dialog Settings Completo
- Aggiunto dialog impostazioni completamente funzionale
- Tabs per Docker, Backup, Scheduler, Storage, Interface, Notifications
- Test connessione Docker con informazioni dettagliate
- Configurazione preset rapidi per scheduler (Daily, Weekly, Hourly)
- Supporto per temi (Auto/Light/Dark)
- Opzioni refresh interval e comportamento UI

### 🐛 Bug Fix Critici

#### Gestione Container con Immagini Mancanti
- **RISOLTO**: Errori continui in console per container con immagini cancellate
- Gestione graceful di container che referenziano immagini non esistenti
- Visualizzazione "(deleted)" invece di exception logging

