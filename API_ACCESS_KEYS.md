# Walmart Affiliate API – Keys, Env, and One-Page Setup

This single document contains everything you need to configure access to the Walmart US Affiliate Product APIs in this repo.

## What you need (credentials and keys)

- Consumer ID (WM_CONSUMER.ID) – from your Walmart Developer Portal app
- Key Version (WM_SEC.KEY_VERSION) – shown next to the uploaded public key (often "1")
- RSA key pair (2048-bit)
  - Public key: uploaded to the Walmart Developer Portal for your app
  - Private key: kept locally and used to sign requests (never share)
- Optional affiliate tracking IDs: PUBLISHER_ID, CAMPAIGN_ID, AD_ID

Auth model: Each request is RSA-SHA256 signed over this canonical string (sorted header names, newline separated, trailing newline):

```
WM_CONSUMER.ID
WM_CONSUMER.INTIMESTAMP
WM_SEC.KEY_VERSION
```

The signature becomes `WM_SEC.AUTH_SIGNATURE` (base64).

## Required environment variables (with purpose)

- WALMART_CONSUMER_ID – Your app’s Consumer ID
- WALMART_PRIVATE_KEY_VERSION – Key version (e.g., 1), must match the version in the portal
- ONE of the following for your private key:
  - WALMART_PRIVATE_KEY_PATH – Absolute path to your PEM private key file; or
  - WALMART_PRIVATE_KEY – Base64-encoded DER of your private key (PKCS#8, unencrypted)

Optional (but supported):
- PUBLISHER_ID, CAMPAIGN_ID, AD_ID – Affiliate tracking parameters
- BASE_URL – Paginated catalog endpoint (default provided)
- ITEMS_BY_IDS_URL – Items-by-ID/UPC/GTIN endpoint (default provided)
- MAX_RETRIES, REQUEST_TIMEOUT, DELAY_BETWEEN_REQUESTS – Client behavior tuning

## Copy-paste .env template

Create a `.env` file at the repo root based on the template below (never commit secrets):

```bash
# Walmart Affiliate API (RSA-signed)

# Required
WALMART_CONSUMER_ID=
WALMART_PRIVATE_KEY_VERSION=1

# Provide ONE of the following for the private key (prefer PATH)
WALMART_PRIVATE_KEY_PATH=
# WALMART_PRIVATE_KEY=

# Optional affiliate tracking
PUBLISHER_ID=
CAMPAIGN_ID=
AD_ID=

# Endpoints
BASE_URL=https://developer.api.walmart.com/api-proxy/service/affil/product/v2/paginated/items
ITEMS_BY_IDS_URL=https://developer.api.walmart.com/api-proxy/service/affil/product/v2/items

# Client behavior
MAX_RETRIES=3
REQUEST_TIMEOUT=30
DELAY_BETWEEN_REQUESTS=1
```

You can also copy `.env.example` to `.env` and fill in the values.

## How to obtain each value

1) In the Walmart Developer Portal
- Create or open your app for the US Affiliate Product API.
- Upload your 2048-bit RSA public key (PEM/DER).
- Note your Consumer ID and the Key Version.

2) Generate or locate your RSA keys (macOS)

```bash
# Generate a new 2048-bit private key (PEM)
openssl genrsa -out WM_IO_private_key.pem 2048

# Export public key from private key (PEM)
openssl rsa -in WM_IO_private_key.pem -pubout -out WM_IO_public_key.pem
```

Upload `WM_IO_public_key.pem` in the portal. Keep `WM_IO_private_key.pem` safe and reference its absolute path in `.env` as `WALMART_PRIVATE_KEY_PATH`.

If you prefer `WALMART_PRIVATE_KEY` instead of a file path, convert your private key to base64-encoded DER:

```bash
openssl pkcs8 -topk8 -inform PEM -outform DER -in WM_IO_private_key.pem -nocrypt -out WM_IO_private_key.der
base64 WM_IO_private_key.der
```

Paste the base64 output into `WALMART_PRIVATE_KEY` in `.env`.

## Endpoints in this repo

- Paginated items (catalog): `https://developer.api.walmart.com/api-proxy/service/affil/product/v2/paginated/items`
- Items by ID/UPC/GTIN: `https://developer.api.walmart.com/api-proxy/service/affil/product/v2/items`

## Sanity check (optional)

With your `.env` in place:

```bash
./setup.sh
source venv/bin/activate
python quick_test.py
```

Expected: HTTP 200, a few items returned, response timing printed. Logs go to `walmart_api_test.log`.

## Notes and best practices

- Never share your private key or commit it to git.
- Ensure `WALMART_PRIVATE_KEY_VERSION` matches the key version in the portal.
- If you hit 429 (rate limiting), increase `DELAY_BETWEEN_REQUESTS`.
- Use `get_items_by_upc` or `get_items_by_ids` for exact lookups; use `get_products` for browsing the catalog.

## From scratch: what to tell someone (10‑minute setup)

Prereqs
- Walmart Developer account with US Affiliate Product API access
- macOS or Linux, Python 3.8+, git, and OpenSSL

Steps
1) Clone the repo
```bash
git clone https://github.com/shinertx/walmart_affiliate.git
cd walmart_affiliate
```

2) Create/prepare credentials in Walmart Developer Portal
- Create an app and enable US Affiliate Product API
- Generate a 2048-bit RSA key pair locally
```bash
openssl genrsa -out WM_private.pem 2048
openssl rsa -in WM_private.pem -pubout -out WM_public.pem
```
- Upload WM_public.pem in the portal
- Copy your Consumer ID and Key Version (e.g., 1)

3) Set up `.env`
```bash
cp .env.example .env
```
Edit `.env` and set:
- WALMART_CONSUMER_ID=<your_consumer_id>
- WALMART_PRIVATE_KEY_VERSION=1
- WALMART_PRIVATE_KEY_PATH=/absolute/path/to/WM_private.pem

4) Install and test
```bash
./setup.sh
source venv/bin/activate
python quick_test.py
```

Acceptance criteria
- quick_test prints “API test successful!” with status 200 and returns a few items
- Log file `walmart_api_test.log` shows request/response info

Troubleshooting fast
- 401/403: Key Version mismatch or wrong private key; verify the private key matches the uploaded public key
- Signature error: ensure timestamp is current and in ms (the client does this for you)
- 429: increase `DELAY_BETWEEN_REQUESTS` in `.env`

What to say in one paragraph
“Create a Walmart Developer app for the US Affiliate Product API, upload your RSA public key, and note your Consumer ID + Key Version. Put those in `.env` along with the path to your private key, run `./setup.sh`, activate the venv, and run `python quick_test.py`. You should see a 200 and a few items. For exact lookups use `get_items_by_upc`/`get_items_by_ids`; for browsing use `get_products`.”
