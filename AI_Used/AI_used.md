# AI Usage Documentation (Team 21)— TLS Fingerprinting (Project ID 11)

## Tools

- Claude Haiku 4.5 model from Claude Code extension in VS Code (for code)
- GPT - 5.6 Luna from Copilot in VS Code(for report) 

After using the Claude Code on the intial project folder, we transformed this folder by changes like renaming,restructuring, deleting and coling again from guthub. Since the original folder doesn't exists now, the claude code session will remain lost. We followed this method as we unware of documenting the AI usage by then.  
Since we already mentioned that we used AI for generating everything except the files in the folder `public_implemented` which were taken directly from [salesforce](https://github.com/salesforce/ja3) and [FoxIO](https://github.com/FoxIO-LLC/ja4) to get the published reference hashes for known clients and also `tls_parser.py`and `ja3.py` were taken from salesforce and adapted to our need.
We feel we are honest about our AI usage and we will try to put the detailed prompts as much as we remember.

## Prompts

`tls_fingerprint/tls_parser.py` and `tls_fingerprint/ja3.py` were **not** built from AI prompts — they were manually adapted from a public reference repo (details in "Originality Check" below). Every other module was built with AI, from prompts describing the required behavior:

Prompt 1: I will send you a Project Description analyze it and just propose me a folder strcurure for it.
Build a tool that passively captures TLS ClientHello and ServerHello messages and computes JA3/JA3S fingerprints (with JA4/JA4S as a stretch goal) to identify the client or server application/library generating the traffic. Curate a small reference database and demonstrate distinguishing real clients (browsers, curl, custom scripts) purely from their handshake fingerprint.  
Tools/Technologies: : libpcap/Scapy (or raw sockets) for capture; fingerprint computation implemented per the JA3/JA4 specifications, eBPF/XDP, Packet/Flow Generators like TRex, KV-stores (Redis, Valkey).
Expected Outcome: Demonstrate the working JA3/JA3S fingerprint extractor, validated against published reference JA3 hashes for known clients; A curated database correctly identifying at least 5 distinct clients/tools by fingerprint alone. Demonstrate distinguishing, e.g., curl vs. a browser vs. a custom TLS client on the wire.
Outcome: Project structure.

Prompt 2: The files tls_parser.py and ja3.py are made now we need a way to actually sniff live traffic with scapy and also read from a pcap file, and handle the case where the clienthello is split across a couple tcp packets
Outcome: code in `tls_fingerprint/capture.py`

Prompt 3: how do we store the fingerprints we find so we can match them later, just something simple like a json file mapping hash to a label, and let us add new ones while capturing
Outcome: code in `tls_fingerprint/database.py`

Prompt 4: can you wire everything into a cli, like `identify --live` or `--pcap`, a `--learn` flag to label whatever it captures, and a db command to list/add fingerprints manually
Outcome: code in `tls_fingerprint/cli.py`

Prompt 5: we have ja3 working but chrome randomizes extension order so it keeps changing, can you add ja4 too since that one sorts stuff before hashing so it should stay stable
Outcome: code in `tls_fingerprint/ja4.py`

Prompt 6: we need a 5th client for the demo, something that doesn't look like curl/requests/browser, maybe a python script using ssl with a weird cipher list so its fingerprint is unique
Outcome: code in `clients/custom_tls_client.py`

Prompt 7: we don't have a pcap to test with, can you write some tests that just build a fake clienthello in bytes and check the parser/fingerprints work on it
Outcome: files with codes in `tests/` (`builders.py` + `test_*.py`)

prompt 8:
give latex code for report write a very good report
1. **Problem Statement & Objectives**
2. **Architecture / Mechanism** — your design and how it works
3. **Extension / Issues Fixed / Evaluation** — what you built on top, bugs resolved, and results
4. **Non-Functional Testing Parameters** — performance, scalability, reliability, etc.
5. **Challenges Faced**
TLS Fingerprinting
"Project Description:  Build a tool that passively captures TLS ClientHello and ServerHello messages and computes JA3/JA3S fingerprints (with JA4/JA4S as a stretch goal) to identify the client or server application/library generating the traffic. Curate a small reference database and demonstrate distinguishing real clients (browsers, curl, custom scripts) purely from their handshake fingerprint.  
Tools/Technologies: : libpcap/Scapy (or raw sockets) for capture; fingerprint computation implemented per the JA3/JA4 specifications, eBPF/XDP, Packet/Flow Generators like TRex, KV-stores (Redis, Valkey).
Expected Outcome: Demonstrate the working JA3/JA3S fingerprint extractor, validated against published reference JA3 hashes for known clients; A curated database correctly identifying at least 5 distinct clients/tools by fingerprint alone. Demonstrate distinguishing, e.g., curl vs. a browser vs. a custom TLS client on the wire.
Understanding on the fingerprinting's role in security monitoring (malware C2 detection, client identification) and its limitations, including fingerprint randomization in modern browsers as an evasion technique."
Analyze the project folder we have currently to understand our project implementation and write the report.

## Thought Process

The core fingerprinting logic (`tls_parser.py`, `ja3.py`) was adpated from reference rather than AI-generated.
- `tls_fingerprint/ja3.py` vs. salesforce/ja3: same list of GREASE values, same JA3 formula and field order, same extension codes used for curves/point-formats. 
- `tls_fingerprint/tls_parser.py` vs. salesforce/ja3: parses the ClientHello in the same order (version, session id, ciphers, compression, extensions). Dropped the `dpkt` dependency the reference uses.

AI was used for the surrounding infrastructure (capture, storage, CLI, custom client, tests).

Each AI-built module was reviewed and tested on its own before moving to the next, rather than generating everything at once and debugging it as a whole.

## Step-by-Step Details

1. Searched Github for TLS fingerprinting repos for reference and selected Salesforce repo. Decided to take their `ja3.py` directly and adapt it.
2. Gave the AI the project brief (Project ID 11 — TLS Fingerprinting) and asked it to propose a project structure/module layout for it.
4. Used AI to build the remaining modules (`ja4.py`, `capture.py`, `database.py`, `cli.py`, `custom_tls_client.py`, `tests/`) from the prompts.
5. Ran the full test suite (`pytest -v`, 9 tests, all passing) to validate the AI-built modules before accepting them.
6. Report was made using Ai.
7. Slides were made us us without AI.