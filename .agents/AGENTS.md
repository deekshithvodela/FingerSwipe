# Workspace Rules & Conventions

## Author Attribution
- The default author for all projects is **Deekshith Vodela** (<deekshithvodela@gmail.com>) unless explicitly specified otherwise.
- All package manifests, CLI metadata, documentation, and web assets must attribute **Deekshith Vodela** as the author/maintainer.

## Clean URLs & Web Routing
- Always generate and use clean URLs without `.html` or file extensions for web applications and documentation portals (e.g. use directory-based routing like `/docs/` with `index.html`, and clean relative links like `./` and `docs/`).

## Git Push Policy
- **HARD CONSTRAINT:** NEVER execute `git push` under any circumstances unless the user explicitly commands it in their current prompt.

