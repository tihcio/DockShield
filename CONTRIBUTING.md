# Contribuire a DockShield

Prima di tutto, grazie per aver considerato di contribuire a DockShield! È grazie a persone come te che DockShield può essere uno strumento migliore per tutti.

## Come Contribuire

### Segnalare Bug

Se trovi un bug, per favore apri un issue su GitHub includendo:

- Versione di DockShield
- Sistema operativo e versione
- Versione di Python
- Versione di Docker
- Passi per riprodurre il bug
- Comportamento atteso vs comportamento attuale
- Log rilevanti (se disponibili)

### Suggerire Funzionalità

Le richieste di nuove funzionalità sono benvenute! Apri un issue descrivendo:

- Il problema che la funzionalità risolverebbe
- Come immagini che dovrebbe funzionare
- Possibili alternative che hai considerato

### Pull Requests

1. **Fork** il repository
2. **Crea un branch** dalla `main`:
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Fai le tue modifiche** seguendo le linee guida del codice
4. **Aggiungi test** se applicabile
5. **Assicurati che i test passino**:
   ```bash
   pytest
   ```
6. **Formatta il codice**:
   ```bash
   black dockshield/
   flake8 dockshield/
   ```
7. **Commit** le modifiche:
   ```bash
   git commit -m 'Add amazing feature'
   ```
8. **Push** al branch:
   ```bash
   git push origin feature/amazing-feature
   ```
9. **Apri una Pull Request** su GitHub

## Linee Guida del Codice

### Stile Python

- Seguiamo [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Usa [Black](https://github.com/psf/black) per la formattazione
- Lunghezza massima riga: 100 caratteri
- Usa type hints dove possibile

### Documentazione

- Documenta tutte le funzioni pubbliche con docstring in formato Google:
  ```python
  def function(arg1: str, arg2: int) -> bool:
      """
      Brief description.

      Args:
          arg1: Description of arg1
          arg2: Description of arg2

      Returns:
          Description of return value

      Raises:
          ValueError: Description of when this is raised
      """
      pass
  ```

### Commit Messages

Usa commit message chiari e descrittivi:

- Usa il presente ("Add feature" non "Added feature")
- Prima riga: max 50 caratteri, sommario
- Corpo: descrizione dettagliata se necessario
- Riferisci issue con #numero

Esempio:
```
Add backup encryption feature

- Implement AES-256 encryption for backups
- Add encryption options to backup dialog
- Update configuration schema

Fixes #123
```

### Testing

- Aggiungi test per nuove funzionalità
- Mantieni la copertura test > 80%
- Test devono passare prima del merge

```bash
# Esegui test
pytest

# Con coverage
pytest --cov=dockshield --cov-report=html
```

### Branching

- `main`: branch stabile
- `develop`: branch di sviluppo
- `feature/*`: nuove funzionalità
- `bugfix/*`: correzioni bug
- `hotfix/*`: correzioni urgenti per main

## Setup Ambiente di Sviluppo

```bash
# Clone repository
git clone https://github.com/yourusername/dockshield.git
cd dockshield

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# Run application in development
python -m dockshield.main
```

## Processo di Review

1. Un maintainer revisionerà la tua PR
2. Potrebbero essere richieste modifiche
3. Una volta approvata, verrà merged
4. Le modifiche appariranno nella prossima release

## Codice di Condotta

### Il Nostro Impegno

Nell'interesse di promuovere un ambiente aperto e accogliente, ci impegniamo a rendere la partecipazione al nostro progetto un'esperienza libera da molestie per tutti.

### Standard

Esempi di comportamento che contribuiscono a creare un ambiente positivo:

- Uso di linguaggio accogliente e inclusivo
- Rispetto di punti di vista ed esperienze diverse
- Accettazione costruttiva delle critiche
- Focus su ciò che è meglio per la community
- Empatia verso altri membri della community

Comportamenti inaccettabili:

- Uso di linguaggio o immagini sessualizzate
- Trolling, commenti offensivi
- Molestie pubbliche o private
- Pubblicazione di informazioni private altrui
- Altra condotta non professionale

### Responsabilità

I maintainer del progetto hanno il diritto e la responsabilità di rimuovere, modificare o rifiutare commenti, commit, codice, modifiche wiki, issue e altri contributi che non sono allineati a questo Codice di Condotta.

## Domande?

Non esitare a:

- Aprire un issue di discussione
- Contattarci via email: dev@dockshield.org
- Unirti alla chat della community (se disponibile)

## Licenza

Contribuendo a DockShield, accetti che i tuoi contributi saranno rilasciati sotto licenza GPL-3.0.

---

Grazie per contribuire a DockShield! 🎉
