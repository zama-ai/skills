# Foundry

Use `@fhevm/forge`, the FHEVM companion to `forge-std`: tests inherit `TestFhevm` instead of `Test`. Its README is the reference for the version you install: run `npm view @fhevm/forge@<version> readme`, or open `node_modules/@fhevm/forge/README.md`. It covers dependencies, remappings, execution modes and fork limits. The older standalone `forge-fhevm` template uses a different setup. Do not mix the two.

Add `fs_permissions` only for files the setup actually writes. `via_ir` is not an FHEVM requirement.
