# Mac Restore — Backup & Recovery Framework

Version: **1.0.6**

## English

Mac Restore is a modular Python framework for creating a focused, encrypted backup of a macOS development workstation and restoring it after a migration or clean installation. It complements a full-system backup such as Time Machine: it preserves important configurations, credentials, project-local files, databases, SSH material, VPN profiles, browser data and development environments without copying an entire home directory or reproducible caches.

The project is designed for user-space migration. Do not run the Mac Restore application with `sudo` or as root. The generated printer helper is separate and opt-in; it may use `sudo lpadmin` because macOS protects the CUPS configuration.

### What is backed up

The standard flow discovers and records:

- IDE settings, keybindings, snippets and extension lists;
- application inventory, Homebrew casks and a Brewfile;
- Chrome and Arc profiles, bookmarks, preferences, password databases and Arc's current special files;
- shell, Git, Node.js, npm/pnpm and development configuration;
- selected Git-ignored project files such as `.env`, copied individually rather than as a home-directory tree;
- Android keystores and AVD configuration, iOS simulator inventory and recreation instructions;
- local MySQL databases as compressed SQL dumps;
- Obsidian preferences and vaults, excluding Electron/runtime caches;
- macOS keychains, browser password databases and remote-tool configuration;
- SSH keys/configuration with recorded permissions;
- Tunnelblick and OpenVPN profiles;
- MySQL Workbench connections;
- system, application, printer and VMware inventories. Printer queues are recorded from CUPS so they can be recreated after drivers are installed.

The optional `disk_usage` audit module is available for inventory purposes but is not part of the default standard selection. VMware is inventoried only: virtual machine bundles and virtual disks are intentionally not copied.

### Safety model

- New backups are compressed and encrypted as a single AES-256-GCM `.backup` archive. The password is never stored.
- Backup passwords must contain at least 8 characters, including uppercase, lowercase, a digit and a special character.
- Plaintext staging and decrypted restore data live in hidden temporary directories with permissions `700` and are removed when processing finishes.
- Each backup contains `manifest.json` and SHA-256 `checksums.json`.
- Restore performs an integrity verification before running modules. A corrupted or tampered backup is rejected.
- Restore starts in dry-run mode. Dry-run calculates destinations and prints planned changes without creating, overwriting or deleting system files.
- Live restore requires explicit confirmation by typing `RESTORE`.
- Before a live direct replacement, existing destinations are copied to `~/Desktop/MacRestore-PreRestore/<timestamp>/`.
- Keychains are never overwritten automatically. They are extracted to `~/Desktop/MacRestore-Keychains/` for manual import.
- Databases, production mobile keys, VPN profiles, application lists and Obsidian vaults are exported to named Desktop folders or guides when manual action is safer. MySQL also receives a password-safe import script.

### Applications and consistency

The backup warns or blocks when affected applications are open. Close Arc, Chrome, Obsidian, AnyDesk, TeamViewer, Termius, FileZilla, MySQL Workbench and other affected applications before the final backup and before a live restore. The override `MAC_RESTORE_ALLOW_OPEN_APPS=1` exists for advanced use, but is not recommended for a migration backup.

### Requirements

- macOS with Python 3.11 or newer;
- access to the source backup location and, when needed, Full Disk Access for the terminal application;
- the relevant applications installed before restoring their settings;
- MySQL installed and available when importing local databases.

For protected locations such as keychains, browser databases and application support folders, open **System Settings > Privacy & Security > Full Disk Access** and enable the terminal or IDE used to run the scripts. Never publish the backup archive, its password, keychains, `.env` files or private keys.

### Usage

Start the interactive interface:

```bash
python3 macrestore.py
```

#### Create a backup

1. Choose `1. Backup`.
2. Choose all standard modules or a single module.
3. Select `./backups/` or choose a destination with Finder, such as an external drive.
4. Enter and confirm the encryption password.
5. Wait for the `.backup` archive and the adjacent non-sensitive `.txt` summary.

For a final migration backup, close affected applications first. Keep the password separate from the archive and retain at least one additional copy of the encrypted archive.

#### Verify a backup

Verification decrypts the archive temporarily and checks every recorded checksum:

```bash
python3 audit.py --verify /path/to/YYYY-MM-DD_HH-MM.backup
```

A valid result ends with `[OK] Backup is valid` and every listed item should be `ok`. Perform this check before erasing or formatting the source Mac. If possible, copy the archive to a second disk and verify that copy too.

#### Inspect and restore

```bash
python3 macrestore.py
```

Choose `2. Restore`, select the backup, and choose one of these modes:

- **dry-run**: shows the complete plan and changes nothing;
- **live execution**: applies selected modules after explicit `RESTORE` confirmation.

The restore menu labels modules as `automatic`, `risky`, `manual` or `inventory`. Choose individual modules for a staged migration. Every completed restore and dry-run creates a timestamped report beside the selected backup.

Legacy direct entry points remain available:

```bash
python3 audit.py
python3 restore.py
```

### Restore order after a clean installation

1. Install Python and the applications required by the selected modules.
2. Mount or copy the verified encrypted backup and run a dry-run.
3. Restore automatic configuration modules such as development, Git, Node, SSH and IDE settings.
4. Clone or update the tracked project repositories from their remote sources, then restore project-local ignored files and inspect the resulting `.env` files carefully.
5. Install printer drivers/software when required, review `~/Desktop/Install_Lists/PRINTERS.md`, then optionally run `restore_printers.sh` and select only the required queues.
6. Install MySQL Community Server for macOS ARM64/Apple Silicon and MySQL Workbench from the links in `~/Desktop/Install_Lists/APPLICATION_DOWNLOADS.md`.
7. Import databases using `~/Desktop/Database_Restored/restore_mysql.sh` or the generated `RESTORE_GUIDE.md`. The script asks for the MySQL root password without saving it in the backup.
8. Import keychains manually from `~/Desktop/MacRestore-Keychains/`.
9. Install or open the relevant VPN client and import profiles from `~/Desktop/VPN_Restored/`.
10. Run `~/Desktop/Install_Lists/BOOTSTRAP_MAC.sh` to coordinate Homebrew, Brewfile packages/casks, Node globals and IDE extensions when available.
11. Install listed applications/extensions and restore manual Desktop exports.
12. Test SSH, Git, printers, MySQL, VPN, browser profiles, development projects and mobile emulators before deleting older backups.

### Backup layout

```text
YYYY-MM-DD_HH-MM.backup       encrypted archive
YYYY-MM-DD_HH-MM.txt          non-sensitive summary beside the archive
  inventory/                   JSON metadata for every module
  backup_config/               text and lightweight configuration
  files/                       databases, keys, profiles and binary data
  manifest.json                backup metadata and module results
  checksums.json               SHA-256 integrity records
  backup_report.md             detailed report inside the encrypted archive
```

The restore report is written outside the archive as `YYYY-MM-DD_HH-MM_restore_YYYY-MM-DD_HH-MM.txt`. It records the mode, module results, skipped items, errors and planned or completed actions.

### Generated helper files and download sources

The MySQL restore module creates `~/Desktop/Database_Restored/restore_mysql.sh`. It checks that `mysql` is installed, asks for the root password without echoing it, creates missing database schemas, imports all `.sql.gz` dumps, and removes its temporary credential file through a shell trap. The password is never embedded in the backup or script. Review the dump list before running it and ensure that MySQL is installed and running.

Android emulator restoration already provides `recreate_emulators.sh`. Application installation, browser extensions, VPN profiles and keychains remain guided/manual because they require software-specific choices, GUI authorization or security confirmation.

The `system_lists` restore module also creates `~/Desktop/Install_Lists/APPLICATION_DOWNLOADS.md`. It lists third-party applications with their backed-up version and a curated vendor-maintained download page where available; macOS system applications are intentionally omitted because the operating system provides them. The file always includes the official pages for MySQL Community Server (macOS ARM64/Apple Silicon) and MySQL Workbench. Links point to download pages rather than fixed version files, so the latest compatible release can be selected after the migration.

The same folder contains `BOOTSTRAP_MAC.sh`, which coordinates the available helpers: `INSTALL_COMMANDS.sh` interactively offers to install Homebrew and runs `brew bundle --file=Brewfile`; `restore_node_globals.sh` restores npm/pnpm global packages; and `install_ide_extensions.sh` installs the recorded VS Code-compatible extensions when the `code` command is available. This is the correct place for command-line tools such as `wget`: they are restored from the Brewfile rather than mixed into the application download list. `applications.txt` contains only applications to reinstall; `applications-full.txt` retains the complete original inventory for reference.

The system inventory records CUPS printer queues with `lpstat -v`, `lpstat -p` and `lpstat -d`. When printers are present, `PRINTERS.md` and the interactive `restore_printers.sh` are placed in `~/Desktop/Install_Lists/`. The helper presents a numbered menu and processes only the queues selected by the user; it does not restore every printer automatically. For queue names containing Xerox, Zebra or Canon, it shows the corresponding official support/download page and can open it in the browser, then pauses so the driver can be installed before continuing. The helper uses `lpadmin`, may request the macOS administrator password, and requires the printer to be reachable. It uses the generic `everywhere` driver mode only as the queue recreation command; install/select the manufacturer driver manually when that mode is not suitable. Printer connection credentials are not reproduced in the generated command.

`RESTORE_GUIDE.md` is the short parent guide for the whole migration. It gives the recommended order and a map of the Desktop folders/files, while the MySQL and VPN guides contain only their module-specific details.

### Modules and restore behavior

| Module         | Backup                                                             | Restore behavior                                      |
| -------------- | ------------------------------------------------------------------ | ----------------------------------------------------- |
| `antigravity`  | IDE settings and extension list                                    | Settings injected; extensions listed for installation |
| `applications` | Installed apps and casks                                           | Inventory exported by `system_lists`                  |
| `browser`      | Chrome/Arc preferences, bookmarks, passwords and Arc special files | Direct copy; close browsers first                     |
| `development`  | Shell dotfiles and runtime inventory                              | Direct copy with pre-restore protection               |
| `git`          | `.gitconfig`                                                       | Direct copy with pre-restore protection               |
| `git_ignored`  | Git-ignored local project files only                               | Individual file restore; no clone, pull or full-home copy |
| `homebrew`     | Brewfile                                                           | Brewfile exported for manual provisioning             |
| `mobile_dev`   | Keystores, AVD config, simulator inventory                         | Safe restore plus emulator recreation instructions    |
| `mysql`        | Compressed SQL dumps                                               | Extracted to Desktop with `RESTORE_GUIDE.md` and `restore_mysql.sh` |
| `node`         | Node manager configuration and global package lists                | Config restore and package lists for manual install   |
| `obsidian`     | Preferences and vaults without runtime caches                      | Preferences injected; vaults exported to Desktop      |
| `passwords`    | Keychains and browser login databases                              | Keychains always extracted for manual import          |
| `remote_tools` | Termius, FileZilla, AnyDesk and TeamViewer config                  | Direct copy with filtered caches/logs                 |
| `ssh`          | Keys, known hosts and SSH files                                    | Direct copy with secure `~/.ssh` permissions          |
| `system`       | Hardware/system and CUPS printer inventory                         | Inventory only; printer queues are recreated by the generated helper |
| `system_lists` | —                                                                  | Creates application, Homebrew, printer and disk-usage lists |
| `vmware`       | VM inventory                                                       | Inventory only; no virtual disks copied               |
| `vpn`          | Tunnelblick and OpenVPN profiles                                   | Profiles exported to Desktop for manual import        |
| `workbench`    | MySQL Workbench connections                                        | Direct copy with pre-restore protection               |

### Development and tests

Modules are discovered dynamically. Add audit modules under `audit/modules/` and matching restore modules under `restore/modules/`. Preserve the plugin contract and keep dry-run side-effect free.

Run the project checks before committing:

```bash
pytest -q
python3 -m compileall -q audit restore shared tests
git diff --check
```

New modules should include tests for discovery, missing sources, counts, errors and dry-run behavior. Do not copy whole home directories, caches, sockets, locks, dependency trees, build artifacts or virtual disks without an explicit documented reason.

## Italiano

Mac Restore è un framework modulare Python per creare un backup mirato e cifrato di una workstation macOS e ripristinarla dopo una migrazione o una reinstallazione pulita. Integra un backup completo come Time Machine: conserva configurazioni importanti, credenziali, file locali dei progetti, database, materiale SSH, profili VPN, dati dei browser e ambienti di sviluppo senza copiare l'intera home directory né cache o dipendenze ricreabili.

Il progetto è pensato per una migrazione nello spazio dell'utente. L'applicazione Mac Restore non deve essere eseguita con `sudo` o come root. Lo script stampanti generato è separato e facoltativo; può usare `sudo lpadmin` perché macOS protegge la configurazione CUPS.

### Cosa viene salvato

Il flusso standard rileva e salva:

- impostazioni IDE, scorciatoie, snippet ed elenco delle estensioni;
- inventario applicazioni, cask Homebrew e Brewfile;
- profili Chrome e Arc, preferenze, segnalibri, database password e file speciali correnti di Arc;
- configurazioni della shell, Git, Node.js, npm/pnpm e ambiente di sviluppo;
- file locali ignorati da Git, come `.env`, copiati singolarmente e non come intero albero della home;
- keystore Android, configurazioni AVD, inventario simulatori iOS e istruzioni di ricostruzione;
- database MySQL locali come dump SQL compressi;
- preferenze e Vault Obsidian, escludendo le cache Electron/runtime;
- portachiavi macOS, database password dei browser e configurazioni degli strumenti remoti;
- chiavi e configurazioni SSH con permessi registrati;
- profili Tunnelblick e OpenVPN;
- connessioni MySQL Workbench;
- inventari di sistema, applicazioni e VMware.

Il modulo opzionale `disk_usage` è disponibile per l'inventario ma non fa parte della selezione standard predefinita. VMware viene soltanto inventariato: bundle e dischi virtuali non vengono copiati intenzionalmente.

### Modello di sicurezza

- I nuovi backup vengono compressi e cifrati in un unico archivio `.backup` AES-256-GCM. La password non viene salvata.
- La password deve avere almeno 8 caratteri, una maiuscola, una minuscola, una cifra e un simbolo speciale.
- I dati temporanei in chiaro e quelli decrittati durante il restore restano in directory nascoste con permessi `700` e vengono rimossi al termine.
- Ogni backup contiene `manifest.json` e `checksums.json` con hash SHA-256.
- Prima del restore viene verificata l'integrità. Un backup corrotto o modificato viene rifiutato.
- Il restore parte in modalità dry-run: calcola i percorsi e mostra le operazioni senza creare, sovrascrivere o cancellare file di sistema.
- L'esecuzione reale richiede la conferma esplicita digitando `RESTORE`.
- Prima di una sostituzione reale, le destinazioni esistenti vengono copiate in `~/Desktop/MacRestore-PreRestore/<timestamp>/`.
- I portachiavi non vengono mai sovrascritti automaticamente: vengono estratti in `~/Desktop/MacRestore-Keychains/` per l'importazione manuale.
- Database, chiavi mobile di produzione, profili VPN, liste applicazioni e Vault Obsidian vengono esportati in cartelle o guide sulla Scrivania quando l'operazione manuale è più sicura. Per MySQL viene creato anche uno script di importazione senza password memorizzata.

### Applicazioni aperte e consistenza

Il backup avvisa o blocca l'operazione quando sono aperte applicazioni coinvolte. Prima del backup finale e del restore reale chiudi Arc, Chrome, Obsidian, AnyDesk, TeamViewer, Termius, FileZilla, MySQL Workbench e le altre applicazioni interessate. La variabile `MAC_RESTORE_ALLOW_OPEN_APPS=1` consente un override per utenti esperti, ma non è consigliata per il backup di migrazione.

### Requisiti

- macOS con Python 3.11 o superiore;
- accesso alla destinazione del backup e, quando necessario, Accesso completo al disco per il terminale;
- applicazioni interessate installate prima di ripristinarne le impostazioni;
- MySQL installato e disponibile quando si importano i database locali.

Per percorsi protetti come portachiavi, database browser e cartelle Application Support, apri **Impostazioni di Sistema > Privacy e Sicurezza > Accesso completo al disco** e abilita il terminale o l'IDE usato. Non pubblicare mai l'archivio, la password, i portachiavi, i file `.env` o le chiavi private.

### Utilizzo

Avvia l'interfaccia interattiva:

```bash
python3 macrestore.py
```

#### Creare un backup

1. Scegli `1. Backup`.
2. Scegli tutti i moduli standard oppure un singolo modulo.
3. Usa `./backups/` oppure scegli con Finder una destinazione, ad esempio un disco esterno.
4. Inserisci e conferma la password di cifratura.
5. Attendi l'archivio `.backup` e il riepilogo `.txt` non sensibile.

Per il backup finale di migrazione chiudi prima le applicazioni coinvolte. Conserva la password separatamente dall'archivio e mantieni almeno una copia aggiuntiva dell'archivio cifrato.

#### Verificare un backup

La verifica decritta temporaneamente l'archivio e controlla tutti gli hash registrati:

```bash
python3 audit.py --verify /percorso/YYYY-MM-DD_HH-MM.backup
```

Un risultato valido termina con `[OK] Backup is valid` e ogni elemento deve risultare `ok`. Esegui il controllo prima di cancellare o formattare il Mac sorgente. Se possibile, copia l'archivio su un secondo disco e verifica anche quella copia.

#### Ispezionare e ripristinare

```bash
python3 macrestore.py
```

Scegli `2. Restore`, seleziona il backup e quindi una modalità:

- **dry-run**: mostra il piano completo e non modifica nulla;
- **live execution**: applica i moduli selezionati dopo la conferma `RESTORE`.

Il menu indica i moduli come `automatic`, `risky`, `manual` o `inventory`. Puoi selezionare moduli singoli per una migrazione a fasi. Ogni restore e dry-run completato genera un report con timestamp accanto al backup selezionato.

Restano disponibili gli script diretti:

```bash
python3 audit.py
python3 restore.py
```

### Ordine consigliato dopo una reinstallazione pulita

1. Installa Python e le applicazioni richieste dai moduli scelti.
2. Collega o copia il backup cifrato verificato ed esegui un dry-run.
3. Ripristina i moduli automatici: sviluppo, Git, Node, SSH e impostazioni IDE.
4. Clona o aggiorna i repository tracciati dalla loro sorgente remota, poi ripristina i file locali ignorati da Git e controlla con attenzione i file `.env`.
5. Installa i driver/software delle stampanti se necessari, controlla `~/Desktop/Install_Lists/PRINTERS.md` ed eventualmente esegui `restore_printers.sh`, selezionando solo le code desiderate.
6. Installa MySQL Community Server per macOS ARM64/Apple Silicon e MySQL Workbench usando i link in `~/Desktop/Install_Lists/APPLICATION_DOWNLOADS.md`.
7. Importa i database usando `~/Desktop/Database_Restored/restore_mysql.sh` oppure `RESTORE_GUIDE.md`. Lo script chiede la password root MySQL senza salvarla nel backup.
8. Importa manualmente i portachiavi da `~/Desktop/MacRestore-Keychains/`.
9. Installa o apri il client VPN e importa i profili da `~/Desktop/VPN_Restored/`.
10. Esegui `~/Desktop/Install_Lists/BOOTSTRAP_MAC.sh` per coordinare Homebrew, pacchetti/cask del Brewfile, pacchetti globali Node ed estensioni IDE quando disponibili.
11. Installa applicazioni/estensioni ed esegui le esportazioni manuali presenti sulla Scrivania.
12. Prova SSH, Git, stampanti, MySQL, VPN, browser, progetti e simulatori prima di eliminare i vecchi backup.

### Moduli e comportamento del restore

Il comportamento dei moduli è quello descritto nella tabella inglese: i moduli automatici ripristinano configurazioni protette da una copia pre-restore, i moduli rischiosi operano su file locali selezionati, i moduli manuali producono esportazioni e guide, mentre i moduli inventory generano elenchi senza modificare il sistema. In particolare `git_ignored` non esegue `git clone` o `git pull`, non ripristina il codice tracciato e non salva i file non tracciati che non risultano ignorati da Git.

Il sistema salva anche l'inventario delle code di stampa CUPS tramite `lpstat -v`, `lpstat -p` e `lpstat -d`. Se sono presenti stampanti, in `~/Desktop/Install_Lists/` vengono creati `PRINTERS.md` e lo script interattivo `restore_printers.sh`. Lo script mostra un menu numerato e ripristina soltanto le code selezionate: non reinstalla automaticamente tutte le stampanti. Per i nomi delle code che contengono Xerox, Zebra o Canon mostra la rispettiva pagina ufficiale di supporto/download, offre l'apertura nel browser e si mette in pausa per consentire l'installazione del driver prima di continuare. Il comando usa `lpadmin`, può chiedere la password di amministratore macOS e richiede che le stampanti siano raggiungibili. La modalità driver generica è `everywhere` solo per ricreare la coda; se non è adatta, il driver va selezionato manualmente. Eventuali credenziali contenute nell'URI non vengono riprodotte nello script.

### File di supporto e fonti di download generati

Il modulo MySQL crea `~/Desktop/Database_Restored/restore_mysql.sh`. Lo script controlla che `mysql` sia installato, richiede la password root senza mostrarla a video, crea gli schemi mancanti, importa tutti i dump `.sql.gz` e rimuove il file temporaneo delle credenziali tramite una trap della shell. La password non viene mai inserita nel backup o nello script. Controlla l'elenco dei dump prima di eseguirlo e assicurati che MySQL sia installato e avviato.

Il ripristino degli emulatori Android dispone già di `recreate_emulators.sh`. Installazione applicazioni, estensioni browser, profili VPN e portachiavi restano guidati/manuali perché richiedono scelte specifiche, autorizzazioni grafiche o conferme di sicurezza.

Il modulo `system_lists` crea anche `~/Desktop/Install_Lists/APPLICATION_DOWNLOADS.md`. Il file elenca le applicazioni di terze parti con la versione del backup e, quando disponibile, il link alla pagina ufficiale del produttore; le app di base di macOS vengono escluse perché fornite dal sistema operativo. Sono sempre presenti le pagine ufficiali per MySQL Community Server (macOS ARM64/Apple Silicon) e MySQL Workbench. I link portano alle pagine di download, non a file con versione fissa, così dopo la migrazione si può scegliere l'ultima release compatibile. Nella stessa cartella sono presenti anche `PRINTERS.md` e `restore_printers.sh` quando il backup contiene code di stampa.

Nella stessa cartella viene creato `BOOTSTRAP_MAC.sh`, che coordina gli script disponibili: `INSTALL_COMMANDS.sh` propone interattivamente l'installer ufficiale Homebrew e poi esegue `brew bundle --file=Brewfile`; `restore_node_globals.sh` ripristina i pacchetti globali npm/pnpm; `install_ide_extensions.sh` installa le estensioni compatibili con VS Code quando il comando `code` è disponibile. Questo è il punto corretto per strumenti da terminale come `wget`: vengono ripristinati dal Brewfile e non confusi con le applicazioni da scaricare. `applications.txt` contiene solo le app da reinstallare; `applications-full.txt` conserva l'inventario completo originale come riferimento.

`RESTORE_GUIDE.md` è la guida padre breve dell'intera migrazione: indica l'ordine consigliato e la funzione delle cartelle/file sulla Scrivania. Le guide MySQL e VPN contengono soltanto i dettagli specifici dei rispettivi moduli.

### Sviluppo e test

I moduli vengono scoperti dinamicamente. I moduli di backup vanno in `audit/modules/`, quelli di restore in `restore/modules/`. Il dry-run deve rimanere privo di effetti collaterali.

Prima di ogni commit esegui:

```bash
pytest -q
python3 -m compileall -q audit restore shared tests
git diff --check
```

I nuovi moduli devono avere test per discovery, sorgenti mancanti, conteggi, errori e comportamento dry-run. Non copiare intere home directory, cache, socket, lock, dipendenze, build o dischi virtuali senza una motivazione documentata.
