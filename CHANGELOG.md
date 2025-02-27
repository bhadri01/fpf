# Changelog

## [Unreleased]

### Added
- Dynamic model mapping for CRUD operations.
- Auto-generated templates for create, update, view, and list operations.
- Auto-generated `assign_roles.html` template.
- Role-based route assignment functionality.
- Periodic token cleanup task.
- Middleware for user permissions and CORS.
- Static file serving from the "public" directory.

### Changed
- Updated routes to perform actual create, update, and delete operations in the database.
- Updated templates to ensure create, update, and delete operations happen using the POST method.
- Updated templates to retrieve `id` value from the URL for update and delete operations.

### Fixed
- Fixed issues with model mapping and dynamic router generation.