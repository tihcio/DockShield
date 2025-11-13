# Changelog

Tutte le modifiche notevoli a questo progetto saranno documentate in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/),
e questo progetto aderisce al [Semantic Versioning](https://semver.org/lang/it/).

## [1.0.0] - 2024-01-XX

### Aggiunto
- Interfaccia grafica KDE Plasma con PyQt6
- Gestione container Docker con visualizzazione in tabella
- Sistema di backup con due modalità:
  - Backup completo (immagine + configurazione + filesystem)
  - Backup filesystem (solo dati)
- Sistema di ripristino container da backup
- Compressione configurabile (livelli 0-9)
- Verifica integrità backup con checksum SHA256
- Scheduler per backup automatici con sintassi cron
- Supporto storage multipli:
  - Storage locale
  - NFS
  - SSH/SFTP
  - AWS S3
- Sistema di notifiche desktop KDE
- Storico backup con dettagli completi
- Sistema di logging con rotazione file
- Supporto tema chiaro/scuro
- Configurazione YAML flessibile
- System tray integration
- Gestione retention automatica backup

### Documentazione
- README completo con esempi
- File di configurazione di esempio
- Documentazione inline del codice
- Desktop entry per integrazione KDE

## [Unreleased]

### Pianificato
- Backup incrementali
- Supporto Podman
- Interfaccia web (opzionale)
- Crittografia backup
- Plugin system per storage custom
- Traduzioni multiple lingue
- Export/import configurazioni
- Backup multi-container con dipendenze
