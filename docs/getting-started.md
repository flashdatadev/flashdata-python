# Getting started

This is the local source release of the official FlashData SDK. Use your own account's
API key from [API Keys](https://flashdata.dev/app/api-keys). Queries consume FlashData
Credits; current account pricing is available through the free pricing read. Downloads
settle by delivered bytes and your storage provider charges separately.

Requires Python 3.10 or newer. From this repository:

```sh
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
```

Set your key in the same terminal that starts the program:

```sh
export FLASHDATA_API_KEY='YOUR_FLASHDATA_API_KEY'
```

PowerShell:

```powershell
$env:FLASHDATA_API_KEY = 'YOUR_FLASHDATA_API_KEY'
```

The SDK reads this environment variable; it does not read `.env` files automatically.
Run an example only when you intend to submit its query. The default offline example
uses a simulated transport and needs no credentials or network connection.
