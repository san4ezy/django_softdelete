# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- This CHANGELOG file to track project changes

### Fixed

- `on_delete=DO_NOTHING` is now a true no-op during a soft-delete cascade. The
  unconditional `related_object.save()` at the tail of `__delete_related_object`
  used to fire for every related object regardless of `on_delete`, mutating
  `auto_now` fields and triggering save side-effects on objects the caller had
  asked us not to touch. The trailing save was also a duplicate write for the
  `SET_NULL` / `SET_DEFAULT` / `SET` branches, which already save inside their
  own dispatch.
