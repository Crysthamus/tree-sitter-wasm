# tree-sitter-wasm [![npm version](https://img.shields.io/npm/v/tree-sitter-wasm.svg?style=flat-square)](https://www.npmjs.com/package/tree-sitter-wasm)
Prebuilt WASM binaries and query files(`.scm`) for tree-sitter's language parsers.
You can find a list of supported languages [here](https://app.unpkg.com/tree-sitter-wasm/files/out)

## Table of Content
* [Installation](#installation)
* [Usage](#usage)
* **[Security](#security)**
    + [Build Security](#build-security)
    + [Cryptography](#cryptography)
    + [Verifications of binaries](#verifications-of-binaries)
        - [Verifying the entire archive (GitHub CLI)](#verifying-the-entire-archive-github-cli)
        - [Verifying individual files (Cosign)](#verifying-individual-files-cosign)
* [Licenses](#licenses)

## Installation
```bash
pnpm add tree-sitter-wasm
# or
bun install tree-sitter-wasm
```

## Usage
A type-safe API is provided for accessing grammars and queries at runtime
```typescript
import { getWasmPath, getQueryPath } from "tree-sitter-wasm";

const wasmPath = getWasmPath("python");
const queryPath = getQueryPath("python", "highlights");
const pythonQueries = getAvailableQueries("python");
```

You can also import the assets directly via your bundler
```typescript
import wasmUrl from "tree-sitter-wasm/python/tree-sitter-python.wasm?url";
import wasmHighlights from "tree-sitter-wasm/python/highlights.scm?raw";

// This JSON object acts as table of content for all available languages
// and their queries.
import manifest from "tree-sitter-wasm/manifest.json"
```

Each language directory includes a `tree-sitter-<lang>.wasm` file but may also include:
- `highlights.scm`
- `injections.scm`
- `locals.scm`
- `tags.scm`
- `folds.scm`
- `indents.scm`

Certain languages also contain special queries like: `nova-symbols`, please refer to the manifest.json or to the out dir in unpkg. 

```txt
python/
├── tree-sitter-python.wasm
├── tree-sitter-python.wasm.sigstore.json
├── folds.scm
├── highlights.scm
├── indents.scm
├── injections.scm
├── locals.scm
└── tags.scm
```

## Security
This project takes security seriously (a lot more so than other sources), all WASMs are compiled and distributed through github actions with strict guardrails to prevent
malicious code injection and tampered artifacts.
You can read about wasm security features [here](https://webassembly.org/docs/security/)

### Build Security
* Pinned Dependencies: All upstream grammar repositories are pinned to explicit, immutable git commit hashes.
* Delayed Updates: A parser is only updated after atleast 7 days have passed from the date of commit.
* Manual Review: Before any commit is bumped, the diffs are manually checked by me and run on a VM.
* Isolated CI: All binaries are compiled strictly within ephemeral, isolated Github action runner.

### Cryptography
* Cosign Signage: All compiled `.wasm` blobs are individually cryptographically signed using [cosign](https://github.com/sigstore/cosign).
* Github Provenance: All artifacts published to npm are done with provenance.
* SLSA 3: Releases are published with SLSA level 3.

### Verifications of binaries
To verify the integrity of a `.wasm` file fetched from this package, you can verify its signature against the github workflow.

#### Verifying the entire archive (GitHub CLI)
If you downloaded the release tarball, you can verify its SLSA provenance attestation:
```bash
gh attestation verify build.tar.gz -R Crysthamus/tree-sitter-wasm
```

#### Verifying individual files (Cosign)
Every .wasm file is distributed alongside a .sigstore.json bundle containing its signature and certificate. You can verify individual files locally like this:
```bash
cosign verify-blob \
  --bundle path/to/tree-sitter-python.wasm.sigstore.json \
  --certificate-identity-regexp "^https://github.com/Crysthamus/tree-sitter-wasm/\.github/workflows/publish\.yaml@" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  path/to/tree-sitter-python.wasm
```

## Licenses
The licenses for the generated .wasm and .scm files belong to their respective upstream grammar authors and can be found on their github repos.

The code in this repository is licensed under MIT.
If you maintain an upstream grammar and have a problem with this licensing, please open an issue.

