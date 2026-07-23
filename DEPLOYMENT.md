# Deploying DOCBOT to your own domain

This runs the same stack as local Docker, plus [Caddy](https://caddyserver.com/)
in front for automatic HTTPS — no manual certificate wrangling.

## Before you start: a real constraint, not a technicality

DOCBOT runs its own LLM (Ollama) locally — that's the whole point (privacy,
no API costs). But that means **whatever server you deploy to has to
actually run that model**, not just serve a website. `llama3` needs roughly
**8GB of RAM at minimum** to run at all, and will be slow (tens of seconds
per answer) on a CPU-only budget VPS. A $5/mo box will likely struggle or
fail outright.

Realistic options, cheapest to most capable:
- A VPS with **16GB+ RAM**, CPU-only — works, but expect chat answers to
  take 20-60+ seconds each.
- A VPS with a **GPU** (e.g. a cloud GPU instance) — much faster, also
  meaningfully more expensive.
- Keep Ollama running on your own machine (or a home server) and only
  deploy the frontend + backend to the cheap VPS, pointing `OLLAMA_BASE_URL`
  at your machine's address — cheaper, but means your machine has to stay
  on and reachable for chat/AI features to work.

If you just want to *show people* DOCBOT works, a small VPS is fine — just
expect to wait a bit per answer. If you want it to feel snappy, budget for
the bigger box.

## Steps

### 1. Get a server and point your domain at it

- Provision a VPS (DigitalOcean, Linode, Hetzner, etc.) running Ubuntu.
- In your domain registrar's DNS settings, add an **A record** pointing
  your domain (e.g. `docbot.yourdomain.com`) at the VPS's public IP.
- Wait for DNS to propagate (`ping yourdomain.com` should show the VPS IP)
  before continuing — Caddy needs this to work to get a TLS certificate.

### 2. Install Docker on the server

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# log out and back in for the group change to apply
```

### 3. Get the project onto the server

```bash
git clone <your-repo-url> docbot   # or scp the folder up
cd docbot
```

### 4. Configure environment

```bash
cp backend/.env.example backend/.env
# edit backend/.env -- set a real random SECRET_KEY, not the placeholder

cp .env.prod.example .env
# edit .env -- set DOMAIN=yourdomain.com (the one you pointed at this server)
```

### 5. Open the firewall

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow OpenSSH   # don't lock yourself out
sudo ufw enable
```

### 6. Build and start

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

This will take a while the first time (same as local — compiling the
backend image with all the ML dependencies).

### 7. Pull the model

```bash
docker exec docbot-ollama ollama pull llama3
```

### 8. Check everything's healthy

```bash
docker compose -f docker-compose.prod.yml ps
```

All four containers (`ollama`, `backend`, `frontend`, `caddy`) should show
healthy. Caddy will automatically request and install a Let's Encrypt
certificate for your domain on first request — visit `https://yourdomain.com`
and it should just work, no manual cert setup.

## Updating later

```bash
git pull   # or re-upload changed files
docker compose -f docker-compose.prod.yml up --build -d
```

## Logs / troubleshooting

```bash
docker compose -f docker-compose.prod.yml logs -f caddy     # TLS / domain issues
docker compose -f docker-compose.prod.yml logs -f backend    # app errors
```

If Caddy can't get a certificate, the most common cause is DNS not pointing
at the server yet, or port 80/443 not actually reachable (firewall, cloud
provider security group, etc.) — Let's Encrypt needs to reach your server
on those ports to verify domain ownership.
