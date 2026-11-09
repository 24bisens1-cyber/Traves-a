# Upload TRAVESÍA to GitHub

This folder is the repository root. It includes `.gitignore`, `.gitattributes`, GitHub Actions checks, Dependabot configuration, a license, security guidance and Render/Docker deployment configuration.

## 1. Review before publishing

- Keep `.env` out of the repository. Commit only `.env.example` with blank values.
- Do not add `instance/citypulsex.sqlite3`, SQLite `-wal`/`-shm` files, user exports, backups, `.venv`, `node_modules` or local logs.
- Confirm that you own or have permission to redistribute the six supplied entertainment-character images and any other third-party media. The MIT license covers original project code only; it does not grant rights to Pokémon, Marvel, Spider-Man, Harry Potter or other third-party characters or artwork. Keep the repository private until you have confirmed the rights needed for your intended distribution.
- Review `.env.example` and remove any real email, API key, password, private URL or token.

## 2. Create and push the repository

Create an empty GitHub repository in your own account, then run these commands from this folder:

```bash
git init
git add .
git status --short
git diff --cached --stat
git commit -m "Initial TRAVESÍA full-stack release"
git branch -M main
git remote add origin https://github.com/YOUR-ACCOUNT/YOUR-REPOSITORY.git
git push -u origin main
```

Review `git status` and the staged file list before committing. The `.github/workflows/tests.yml` workflow runs on pushes and pull requests. A successful workflow is the gate for merging/publishing code changes. The current CI run includes 15 mandatory Flask HTTP/auth integration tests; they cannot be treated as passed until the remote workflow returns green.

## 3. Configure deployment secrets

Connect the repository to Render and apply the included `render.yaml` Blueprint. Supply the prompted environment values in Render's secret manager. Never paste real secrets into this file or GitHub source code. Use the deployment guide and provider setup docs for exact variables.

## 4. Verify the hosted deployment

After deployment, run:

```bash
python scripts/smoke_deployed.py https://YOUR-SERVICE.onrender.com
```

Then manually test account registration/login/logout, two separate accounts, shared-trip read-only access, editor-token writes, stale-update conflict, database persistence after restart and all configured provider fallbacks.
