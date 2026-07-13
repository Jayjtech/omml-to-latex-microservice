# Known issues (filed 2026-07-12, from codebase study)

Low-severity items surfaced while studying the codebase against `CLAUDE.md` §6/§11. This service is never publicly reachable (only `njs-backend` calls it over the internal network), so neither item is urgent — filing for later cleanup, not fixing now.

## 1. XML entity-expansion ("billion laughs") not guarded against
`omml_converter.py`'s `_extract_math_elements` parses attacker-controlled XML with stdlib `xml.etree.ElementTree.fromstring`. Classic XXE isn't exploitable (stdlib doesn't resolve external entities by default), but there's no protection against entity-expansion DoS. Consider `defusedxml` if this service's trust boundary ever changes (e.g. if it stops being internal-only).

## 2. CORS config is spec-invalid
`main.py`'s `CORSMiddleware(allow_origins=["*"], allow_credentials=True)` — browsers ignore the wildcard origin when credentials are enabled, so this combination doesn't actually do what it looks like it does. Currently inert (correctly, per CLAUDE.md §11, since nothing external can reach this service), but worth tightening to a real allowlist or dropping `allow_credentials` if this ever needs to mean something.
