# env-vault

> Lightweight utility to encrypt and manage project-level `.env` files using local key storage.

---

## Installation

```bash
pip install env-vault
```

Or with [Poetry](https://python-poetry.org/):

```bash
poetry add env-vault
```

---

## Usage

Initialize a vault for your project and encrypt your `.env` file:

```bash
# Initialize env-vault in your project (generates a local key)
env-vault init

# Encrypt your .env file
env-vault lock .env

# Decrypt back to .env
env-vault unlock .env.vault

# Load encrypted env vars directly into a command
env-vault run -- python app.py
```

You can also use it programmatically:

```python
from env_vault import Vault

vault = Vault()
vault.lock(".env")           # Encrypts .env → .env.vault
vault.unlock(".env.vault")   # Decrypts .env.vault → .env
secrets = vault.load()       # Returns dict of decrypted key/value pairs
```

> **Note:** The generated key is stored locally at `~/.env-vault/keys/<project-id>`. Never commit `.env` or your key file to version control. Add `.env` to your `.gitignore` and commit `.env.vault` instead.

---

## How It Works

- Uses **AES-256-GCM** encryption via the `cryptography` library
- Keys are stored per-project in your home directory
- `.env.vault` files are safe to commit to version control

---

## License

[MIT](LICENSE) © 2024 env-vault contributors