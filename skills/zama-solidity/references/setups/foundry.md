# Foundry

Use `@fhevm/forge`, the FHEVM companion to `forge-std`: tests inherit `TestFhevm` instead of `Test`. Its source and README live in [fhevm-mocks](https://github.com/zama-ai/fhevm-mocks) under `foundry/`. Use the `release/*` branch that matches the protocol version you target, and follow the README for dependencies, remappings and execution modes. The older standalone `forge-fhevm` template uses a different setup. Do not mix the two.

- Tests run in cleartext. Forks do not know plaintexts computed outside the test. Check the README's fork-mode limits.
- Test transferred amounts, overflow and rounding, access in later transactions, and replayed or forged reveals.
- Add `fs_permissions` only for files the setup actually writes. `via_ir` is not an FHEVM requirement.
