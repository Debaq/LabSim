# Changelog

All notable changes to LabSim. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.3] — 2026-05-11

### Fixed
- **UI**: `Select` dropdowns no longer render behind floating windows. The popup z-index was `z-50` while LabSim windows use a dynamic stack starting at 100, so menus were hidden under the active window. Bumped popup/positioner to `z-[99999]` and switched the popup background/border/text to `--ls-panel`/`--ls-border`/`--ls-text` so contrast follows the active theme. Affects Género, Severidad, Exposición a ruido (Ocupacional/Recreacional/Protección), OAE Resultados, Maspetiol, Fowler, PEATC estímulos, Tipo de audífono y molde. (#11)

### Added
- **Audiometry**: LDL editor in the audiometry module — new **LDL** tab next to Vía Aérea / Ósea, editable per ear and frequency. Verbal instructions `pitos_fuertes` and `solo_si_molesta` relabeled with `LDL:` prefix so students find them when taking the LDL test. (#14)
- **Audiometry**: PTP (Promedio Tonal Puro, 500/1k/2k Hz) panel visible during case creation, showing OD/OI × VA/VO computed live from the entered thresholds. (#16)
- **Anamnesis**: tinnitus *Presencia* now accepts `Negativo` / `Ocasional` / `Permanente` (in addition to the legacy `Presente`), and *Tipo* includes `Tono` and `NBN`. Detail subfields show for any non-`ausente` value. (#15)

### Open / pending
- #12 Impedanciometría shows "SIN SEÑAL" when no patient is loaded — pending the broader "call patient to box" flow.
- #13 Microphone and TTS voices on Windows — requires a Windows environment to debug.
- #16 / #17 — PTP / SDT-SRT-UMD reports awaiting a reproducible case.

## [3.1.2] — earlier

- MIT license + Zenodo metadata, citation/DOI work.

## [3.1.1] — earlier

- Fix espeak-ng data path for TTS on Windows.

## [3.1.0] — earlier

- Panel Docente, activity management, session backend.

## [3.0.1] — earlier

- Desktop repair pass, demo user with write blocks, centralized versioning via `VERSION` file.
