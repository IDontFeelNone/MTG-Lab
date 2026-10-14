# Explicit historical auxiliary dependencies

The frozen historical catalog manifest continues to bind the original data bytes.
Some retained artifacts additionally bound non-data files. Such dependencies need
their own original bytes, revision and immutable manifest identity; current files
cannot substitute merely because they occupy the same path.

`card-acquisition-pilot/` retains exactly `docs/ARCHITECTURE.md` from the pilot's
declared baseline `3cf6ad35fcb54ed5a4b640e36af6fa2ecf99a747`:

- 3,430 bytes; SHA-256
  `53b2818c428901b9dcb46f0eee54017527bc6088fd08fe7aa47aab010afa00f5`.
- Auxiliary manifest SHA-256
  `360d732fa3ec9d4b784eef9c25f4afbec9c645cb7b983c34e25e0b4b248e85d7`.
- Original protected inventory remains
  `sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`.

Only the Card Acquisition pilot explicitly selects this auxiliary fixture through
`bind_replay_builder`. Other historical roots keep their existing behavior. No
production builder, protected inventory filter or retained artifact is changed.
Tests require exact original artifact replay and reject changed/missing historical
dependencies, including replacement by the current Architecture proposal.

The test helper verifies the manifest and bytes before every selection, including
cached roots, rejects unsafe/symlink paths, and never uses live Git or current docs
to recover a missing dependency. Git was used once to establish the original bytes;
ordinary CI uses only the retained fixture. The old data manifest/archive remain
unchanged. The fixture is independent of PR #175's new architecture examples.

This is historical replay isolation, not permanent protection of future current
architecture bytes. Current governance tests independently preserve historical
decision text and the owner-accepted Decision 017 status. Architecture v13 is now
approved governance; no v13 runtime is installed. This acceptance leaves the
original Architecture-v12 fixture and all its integrity bindings unchanged.
