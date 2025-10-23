## 🧨 Istruzioni per distruggere tutto e ripartire pulito

```bash
docker compose down --volumes --remove-orphans
docker network rm cloudetta_internal cloudetta_web 2>/dev/null || true
docker system prune -a --volumes -f
docker ps -aq --filter "label=com.docker.compose.project=cloudetta" | xargs -r docker rm -f
docker rm -f caddy 2>/dev/null || true
docker network ls -q --filter "label=com.docker.compose.project=cloudetta" | xargs -r docker network rm
docker volume ls -q --filter "label=com.docker.compose.project=cloudetta" | xargs -r docker volume rm
docker rm -f $(docker ps -aq --filter "name=^cloudetta-") 2>/dev/null || true
docker compose down --volumes --remove-orphans
docker compose --profile monitoring --profile logging --profile backup --profile office --profile sso --profile errors --profile uptime down --volumes --remove-orphans
docker system prune -a --volumes -f
```

Ricevuto. Procedo con le istruzioni per **spianare tutto Docker** (contenitori, volumi, reti, immagini “dangling”) e poi rilanciare InboxBrain pulito. ⚠️ **ATTENZIONE**: perderai i dati MySQL nei volumi (anche di altri progetti).

## A) “Nuke mode” — Bash / WSL / macOS / Linux
Copia-incolla in una shell Bash:
```bash
# 1) Spegni e ripulisci il progetto corrente (dalla cartella InboxBrain)
docker compose down -v --remove-orphans

# 2) Ferma e rimuovi TUTTI i container del sistema
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm -vf $(docker ps -aq) 2>/dev/null || true

# 3) Pulisci reti e volumi non usati (ora saranno tutti "unused")
docker network prune -f
docker volume prune -f

# 4) Pulisci immagini/cache/builder
docker system prune -af --volumes
docker builder prune -af
```

## B) “Nuke mode” — Windows PowerShell
Se stai usando PowerShell:
```powershell
# 1) Spegni e ripulisci il progetto corrente (da cartella InboxBrain)
docker compose down -v --remove-orphans

# 2) Ferma e rimuovi TUTTI i container
$all = docker ps -aq
if ($all) { docker stop $all; docker rm -vf $all }

# 3) Pulisci reti e volumi non usati
docker network prune -f
docker volume prune -f

# 4) Pulisci immagini/cache/builder
docker system prune -af --volumes
docker builder prune -af
```

## C) Rilancio di InboxBrain (pulito)
Dalla cartella del progetto:
```bash
# opzionale: pulizia workspace (attenzione: rimuove file non tracciati)
# git clean -xfd

# rebuild e avvio
docker compose up -d --build

# attesa MySQL ready
docker compose logs -f mysql

# log di controllo
docker compose logs -f app
```

Se vuoi evitare conflitti porta, puoi mappare l’app su **8080** modificando in `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"
```
e poi:
```bash
docker compose down
docker compose up -d --build
curl http://localhost:8080/health
```

Se serve, ti preparo anche uno **script “nuke.sh / nuke.ps1”** dentro il repo per farlo con un solo comando.