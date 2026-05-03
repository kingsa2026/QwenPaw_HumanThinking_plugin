# Changelog

All notable changes to the HumanThinking Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.4.2] - 2026-05-04

### Fixed
- **Docker Compatibility**: Added `_resolve_qwenpaw_dir()` unified path resolution function in `plugin.py`, `memory_manager.py`, `routes.py`, and `sleep_manager.py`.
- Replaced all `Path.home()` hardcoded path references with `_resolve_qwenpaw_dir()` to ensure correct config file and database creation in Docker environments.
- In Docker, `QWENPAW_WORKING_DIR=/app/working` is now correctly resolved instead of falling back to `~/.qwenpaw`.
- Fallback chain: `QWENPAW_WORKING_DIR` env var -> `qwenpaw.constant.WORKING_DIR` -> legacy `~/.copaw` -> `~/.qwenpaw`.

### Added
- Full channel adapter implementations for XiaoYi, OneBot, MQTT, Mattermost, and Matrix adapters with proper `extract_user_id`, `extract_session_id`, `extract_group_info`, and `extract_target_id` methods.

---

## [1.4.1] - 2026-04-25

### Added
- Compatibility with QwenPaw v1.1.4.post2.
- Fixed dropdown menu injection and configuration features.

---

## [1.2.0] - 2026-04-20

### Added
- Complete sidebar UI with Memory Management, Sleep Management, and Backup tabs.
- Sidebar language switching (zh/en/ja/ru).
- Memory statistics offline mode.
- Agent list with Table component and Tabs navigation.

### Fixed
- Multiple bug fixes across UI and backend.

---

## [1.1.5-beta.1] - 2026-04-15

### Changed
- Adapted for QwenPaw v1.1.5-beta.1 API changes.

---

## [1.1.4.post2] - 2026-04-10

### Fixed
- Fixed hardcoded Python version paths in one-click uninstall functionality.
- Enhanced uninstall restoration mechanism with original file cross-comparison.
- Python cache clearing logic during uninstall.

---

## [1.1.1-backup] - 2026-03-28

### Added
- Agent config refresh on switch.
- SQL syntax fixes.
- UI injection improvements.

---

## [1.0.0] - 2026-03-20

### Added
- Initial release of HumanThinking Memory Manager plugin.
- Cross-session memory support.
- Emotional state tracking.
- Sleep management system.
- Memory lifecycle management (cold storage -> archive -> delete).
- Forgetting curve implementation.
- Event-driven sleep mode with configurable triggers.
- Database structure optimized for human-like memory model.
