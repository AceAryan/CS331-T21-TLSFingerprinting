# TLS Fingerprinting

A tool that passively captures TLS `ClientHello`/`ServerHello` handshakes
(live or from a `.pcap`), computes **JA3 / JA3S / JA4** fingerprints, and
matches them against a locally curated reference database to identify the
client application -- purely from its handshake, with no decryption involved.

## Project structure

All paths below are relative to this `code/` directory (a sibling of
`public_implemented/`, which holds the reference implementations and pcaps).

```
code/
  tls_fingerprint/
    tls_parser.py   # raw TLS record/handshake parsing (no external deps)
    ja3.py           # JA3 / JA3S (MD5, Salesforce spec)
    ja4.py           # JA4 client fingerprint (simplified FoxIO spec)
    capture.py       # live sniff + pcap replay, with TCP reassembly
    database.py      # JSON-backed fingerprint -> label store
    cli.py           # command-line entry point
  clients/
    custom_tls_client.py  # hand-rolled TLS client for a 5th, distinct fingerprint
  data/known_fingerprints.json   # validation DB: seeded from the Salesforce/FoxIO
                                  #   reference implementations, used to check the
                                  #   extractor's output against a trusted source
  data/learned_fingerprints.json # curated via our own CLI against the same
                                  #   reference pcaps (public_implemented/)
  data/live_learned.json         # curated via our own CLI against real live
                                  #   traffic captured on a real machine
  tests/             # unit tests (synthetic ClientHello builders, no network needed)
  main.py
  pytest.ini         # scopes `pytest` to tests/ (public_implemented/ has its own vendored suite)
  public_implemented/  # sibling directory: reference JA3/JA4 scripts + pcaps
```

## Setup

Run these commands from inside `code/`:

```powershell
pip install -r requirements-dev.txt
```

Npcap (bundled with Wireshark) is required for **live** capture on Windows.
Live capture also requires the terminal to
be running **as Administrator**.

## Usage

`--db` tells the tool which database file to read/write. If you omit it, it
defaults to `data/live_learned.json` -- the database meant to keep growing
from real traffic. Pass `--db` explicitly whenever you want to target one of
the other two databases instead (`data/known_fingerprints.json`, the static
validation set seeded from the reference implementations -- never write into
it; or `data/learned_fingerprints.json`, built from replaying the reference
pcaps through this tool).

Identify traffic from a pcap file (no admin needed), matching against the
database curated from our own CLI run against the reference pcaps:

```powershell
python main.py identify --pcap sample.pcap --db data/learned_fingerprints.json
```

Capture live traffic for 20 seconds and label the resulting fingerprint into
the live-learned database (run this *while* the target client makes an HTTPS
request):

```powershell
# in an elevated (Administrator) PowerShell
python main.py identify --live --duration 20 --learn curl --db data/live_learned.json
```

Inspect what's been learned so far:

```powershell
python main.py db --db data/live_learned.json list
```

Manually register a fingerprint you already know:

```powershell
python main.py db --db data/live_learned.json add ja3 <hash> "some-client"
```

## Building a 6-client reference database (`data/live_learned.json`)

The expected outcome is identifying **at least 5 distinct clients** purely
from their handshake. `data/live_learned.json` was built entirely this way --
no pcaps, just real live traffic from 6 real clients on one machine, each
learned with its own command while that client made an HTTPS connection:

```powershell
# Terminal 1 (run each of these one at a time)          # Terminal 2 (while it's running)
python main.py identify --live --duration 8  --filter "tcp port 443" --learn custom_client
                                                          python clients/custom_tls_client.py example.com

python main.py identify --live --duration 8  --filter "tcp port 443" --learn git
                                                          git ls-remote https://github.com/octocat/Hello-World.git HEAD

python main.py identify --live --duration 8  --filter "tcp port 443" --learn curl
                                                          curl.exe https://example.com

python main.py identify --live --duration 12 --filter "tcp port 443" --learn brave
                                                          & "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe" https://example.com

python main.py identify --live --duration 12 --filter "tcp port 443" --learn edge
                                                          & "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" https://example.com

python main.py identify --live --duration 12 --filter "tcp port 443" --learn chrome
                                                          & "C:\Program Files\Google\Chrome\Application\chrome.exe" https://example.com
```

(no `--db` needed -- these all write to the default `data/live_learned.json`)

**Cleaning up contamination.** A live capture with a broad `tcp port 443`
filter picks up *every* TLS connection on the machine during that window --
not just the one client you're trying to learn. In practice this meant
unrelated background processes (a logging/telemetry agent hitting
`*.datadoghq.com`, a McAfee updater, Windows/Microsoft background services)
got swept up and mislabeled under whatever `--learn` label was active at the
time. After each learn pass, inspect the result before trusting it:

```powershell
python main.py db --db data/live_learned.json list
```

...and for any hash whose flow clearly isn't the client you were testing
(cross-check the `sni=` printed during capture), remove or correct it, e.g.:

```powershell
python -c "import json; d=json.load(open('data/live_learned.json')); del d['ja4']['<bad-hash>']; json.dump(d, open('data/live_learned.json','w'), indent=2, sort_keys=True)"
```

One entry is *not* contamination and should be kept as a shared label:
Brave and Edge, with no distinguishing browser extension active, produce the
**exact same** JA4 hash (`t13d1516h2_8daaf6152771_806a8c22fdea`) -- the same
convergence your teammate's independently-captured `known_fingerprints.json`
already records as `"Brave/chrome/edge"`. That entry is labeled `"Brave/Edge"`
here rather than overwritten to just one browser's name.

**Verifying the matches.** Re-run `identify --live` against the same database
with **no `--learn` flag**, while re-triggering each client, and confirm every
flow now resolves instead of showing `UNKNOWN`:

```powershell
python main.py identify --live --duration 10 --filter "tcp port 443" --db data/live_learned.json
```

Result from doing exactly this for all 6 clients (fresh connections, sites
never visited during learning included):

| Client | JA3 matched | JA4 matched |
|---|---|---|
| custom_client | Yes -- deterministic client, no randomization | Yes |
| git | Yes | Yes |
| curl | Yes | Yes |
| Brave | No -- randomizes extension order every connection | Yes (5/5) |
| Edge | No -- same reason | Yes (8/8) |
| Chrome | No -- same reason | Yes (11/11) |

This is the core result the project sets out to demonstrate: for the three
Chromium-based browsers, **JA3 never matches** a fresh connection (each one
produces a hash never seen before, even to the same site visited during
learning), while **JA4 matches every time** -- because it sorts ciphers and
extensions before hashing, so browser-side randomization doesn't change the
result. For the three simple, non-randomizing clients (curl, git,
custom_client), both JA3 and JA4 match reliably, since there's no per-connection
shuffling to defeat in the first place.

All 6 clients were correctly identified purely from their handshake by JA4,
satisfying the brief's "at least 5 distinct clients" requirement using real
live traffic end-to-end through our own extractor, not pcap replay.

## Why JA3 *and* JA4?

JA3 hashes the ClientHello's cipher list, extension list (in the order they
appear), curves, and point formats. It's simple and was long used in
IDS/EDR products (Suricata, Zeek, Cisco) to flag malware C2 traffic --
hand-rolled TLS clients (e.g. bots, off-the-shelf C2 frameworks) tend to
produce unusual, static JA3 hashes that stand out from mainstream browser
traffic.

**Limitation this project is meant to surface:** since ~2020, Chrome (and
Chromium-based browsers) intentionally *randomizes the order* of TLS
extensions per connection (a deliberate anti-ossification/anti-fingerprinting
measure). Because JA3 is order-sensitive, the *same* installation of Chrome
produces a *different* JA3 hash on every connection -- breaking naive
single-hash matching. JA4 was designed specifically to address this: it
sorts cipher suites and extensions before hashing, so it stays stable across
Chrome's extension-order permutation. You should be able to demonstrate this
directly: capture the same browser twice and show JA3 changing while JA4
(mostly) doesn't.

This also means JA3/JA4 alone are a *weak signal*, not proof -- CDNs/proxies
terminating TLS on behalf of many different clients, and legitimate software
built on the same TLS library as malware, can produce false positives or
collide. Real detection pipelines combine fingerprints with other signals
(destination reputation, timing, volume).

## Notes on the JA4 implementation

`ja4.py` implements the ClientHello (`t`/`q` + version + sni + counts + alpn,
followed by sorted-cipher and sorted-extension/sig-algs hashes) case of the
publicly documented [JA4 spec](https://github.com/FoxIO-LLC/ja4). It is a
simplified reference implementation for learning purposes, not a byte-exact
port of the official library -- for production use, use FoxIO's own tooling.

## Running tests

```powershell
pytest
```

Tests build synthetic ClientHello/ServerHello byte buffers by hand (see
`tests/builders.py`) so parsing and hashing logic can be verified without a
live capture or a checked-in pcap file.
