# Changelog

## [1.0.21] - 2025-09-17

### Fixed:

- Correct an error that occurred when trying to delete models with a OneToOneField relationship. This resolves a bug where the django-softdelete package would fail to correctly handle cascading deletes for OneToOneField instances when the related model was soft-deleted.
- Correct a missing import for OneToOneField relations, which was causing issues when checking for one-to-one relationships.

### Changed:

- Modify the hard_delete_selected_items Django admin action to perform individual deletions instead of a bulk operation. This change ensures that all signals are correctly triggered and cascading deletions are properly handled for related models.

## [1.0.20] - 2025-01-31

### Added:

- Add the CHANGELOG.md file to the project root to track notable changes.
- Transition all project configuration, building, and testing to use pyproject.toml and Hatch.
- Add the hard_delete method to DeletedQuerySet to enable the permanent deletion of objects in Django Admin. This change resolves Issue #47.
