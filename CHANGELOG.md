# Changelog

## [0.1.1](https://github.com/Albertzc/AlchemyWorks/compare/v0.1.0...v0.1.1) (2026-10-17)


### Bug Fixes

* correct instance workflow command paths ([fe52391](https://github.com/Albertzc/AlchemyWorks/commit/fe52391285d8ecc4228d8c4c44d8b9c3f725b8bd))

## 0.1.0 (2026-10-16)


### Features

* add repository versioning and release CI ([e8ecb05](https://github.com/Albertzc/AlchemyWorks/commit/e8ecb052a0bca729342d6bfc3709969c0c4d94f1))
* add workflow refresh command ([f87e461](https://github.com/Albertzc/AlchemyWorks/commit/f87e461b8546641fca455a94c700984162957b3e))
* auto-generate workspace functionality README ([c251ffa](https://github.com/Albertzc/AlchemyWorks/commit/c251ffad3e0535fe545e70e0b9fd0bb179ce2e08))
* bootstrap Nyxigen workflow tooling (skills + scripts + templates) ([1d92f5e](https://github.com/Albertzc/AlchemyWorks/commit/1d92f5e649eeb2e68c0050ab565d207e8228932f))
* complete workflow governance v1.0 ([1ea3e88](https://github.com/Albertzc/AlchemyWorks/commit/1ea3e886c9444bcf0c81fef473e45630a5cf9460))
* generate instance README from release requirement ([c3bfc52](https://github.com/Albertzc/AlchemyWorks/commit/c3bfc52c88b72c934418ca2e065e18908996e9bf))
* introduce release-log artifact at 05-review-release (existence-only gate) ([82dfcb0](https://github.com/Albertzc/AlchemyWorks/commit/82dfcb0260fa744a7a8cd23b7521ec3e55a11bfa))
* make instance documents project-owned ([108b119](https://github.com/Albertzc/AlchemyWorks/commit/108b11941150446af5b1044ffcdea5b3f5934b42))
* make iteration prototypes conditional ([eb1d30b](https://github.com/Albertzc/AlchemyWorks/commit/eb1d30be80a3f0861b6385b47cdaacfd7a232625))
* protect workflow core files ([e817e9a](https://github.com/Albertzc/AlchemyWorks/commit/e817e9aa890697c9dd9eceae174559f7c5d85168))
* refresh workspace docs on iteration archive ([4a4ffca](https://github.com/Albertzc/AlchemyWorks/commit/4a4ffca04012b0945bade60aaa2b50ad1ce52b6e))
* reorganize workflow instance initialization ([bed165c](https://github.com/Albertzc/AlchemyWorks/commit/bed165cd430a4ba521e98ab6003c538b4ae748e9))
* strengthen workflow governance ([7ec2d00](https://github.com/Albertzc/AlchemyWorks/commit/7ec2d006919e3b90e8def49a81a7a4d359f243af))
* **workflow:** cross-version diff via scripts/diff_versions.py ([38226a6](https://github.com/Albertzc/AlchemyWorks/commit/38226a6b769fe959422ac3be5059e366415e657c))
* **workflow:** expose framework version via __version__, --version, and workflow-version.yaml ([ec2f815](https://github.com/Albertzc/AlchemyWorks/commit/ec2f8159917f15a07d0be13fdf1ecb74437469ca))
* **workflow:** strengthen staged workflow governance ([0d23734](https://github.com/Albertzc/AlchemyWorks/commit/0d23734706d4b750588fe968d934b94705af01db))
* **workflow:** track dashboard/template.html + fix stale brand ([b0c8341](https://github.com/Albertzc/AlchemyWorks/commit/b0c8341e79cf17d9bdf2d3efbf83fc05d0d24e27))


### Bug Fixes

* bootstrap framework release at 0.1.0 ([bbf0e0c](https://github.com/Albertzc/AlchemyWorks/commit/bbf0e0cccd542e9c70ec4caaf32f3b8eb1937b19))
* bump framework version for workflow changes ([2cc8bd0](https://github.com/Albertzc/AlchemyWorks/commit/2cc8bd091d284a6e8f91cc972d3eac04b1b04af7))
* decouple workflow README from product iterations ([1267814](https://github.com/Albertzc/AlchemyWorks/commit/1267814bc49b4cf327db2eb71ecaa732bcfeb562))
* enforce prototype review metadata ([79d67ca](https://github.com/Albertzc/AlchemyWorks/commit/79d67ca81f83128aa9bdc01beb0a159d6fb6fad0))
* expose instance workflow entry point ([563acb1](https://github.com/Albertzc/AlchemyWorks/commit/563acb1aac3ed8bb973adfd560d467ac3500a24f))
* grant release workflow permissions ([0ead8bf](https://github.com/Albertzc/AlchemyWorks/commit/0ead8bfd7aaf1fc6a9e8974126d3df1e47d03842))
* **skills:** remove duplicate design-tokens.json under prototype-design-system skill ([ebe152a](https://github.com/Albertzc/AlchemyWorks/commit/ebe152a4e14100bf617657d051111b9b20a5e00c))
* **templates:** use status: draft in issue-fixes sample frontmatter ([40a6709](https://github.com/Albertzc/AlchemyWorks/commit/40a670991368c35fc4452f4582b16464a61df2d7))
* **workflow:** allow v1.1+ iterations to skip feature-specification.md ([a03cf7c](https://github.com/Albertzc/AlchemyWorks/commit/a03cf7cd9cecf2a9ff919c86f4e64561ee13eb0e))
* **workflow:** atomic write for cache/context-packs.json ([52bdbe3](https://github.com/Albertzc/AlchemyWorks/commit/52bdbe3483ae9eef6fd41275ff514ceca924cbb1))
* **workflow:** refresh non-versioned scaffold READMEs at the end of `sync` ([85f35d1](https://github.com/Albertzc/AlchemyWorks/commit/85f35d11d98955b9d6f68648dc1a00a4f9aece42))
* **workflow:** repair regression fixtures and root ignore ([9676e77](https://github.com/Albertzc/AlchemyWorks/commit/9676e7765b46c1737987fdf0d640a314da084e35))
* **workflow:** replace hardcoded .workflow/ paths with WORKFLOW_DIR.relative_to(ROOT) ([30d51bb](https://github.com/Albertzc/AlchemyWorks/commit/30d51bb8268b010c7b83835f2156ed4d167a3ce1))


### Documentation

* add §14 disclaimer for experimental-phase status ([eb7b325](https://github.com/Albertzc/AlchemyWorks/commit/eb7b325913f332eecf8ca6d630321da73970eee2))
* align README/AGENTS with merged artifact convention ([73c7269](https://github.com/Albertzc/AlchemyWorks/commit/73c72699984ca1c6b386c9041bf2621023406c37))
* clarify workflow and instance directory ownership ([95f7e55](https://github.com/Albertzc/AlchemyWorks/commit/95f7e5532bbe8e99e58a923489456bea6bff41a7))
* drop savings estimate column; add sync-framework.py for multi-project reuse ([ea9b4d3](https://github.com/Albertzc/AlchemyWorks/commit/ea9b4d39e60e2a9ae82483762b044ece009e486f))
* **iterate-implementation:** clarify task-finished default behaviour ([1ed3e9e](https://github.com/Albertzc/AlchemyWorks/commit/1ed3e9e0aa4ff8bd264424bc5a1378a1e1e674af))
* **manage-iteration:** align RC artifact filename with README + workflow.py ([cc9fdcd](https://github.com/Albertzc/AlchemyWorks/commit/cc9fdcdfd3fb9dad545b4a213ef3c232a4c4657c))
* README §6/§9/§11 self-consistency pass ([b2a99b9](https://github.com/Albertzc/AlchemyWorks/commit/b2a99b9db8f10fa4193fbebe3d2ce6cc18c6e4c0))
* remove Hermes-specific wording from README ([6e3f791](https://github.com/Albertzc/AlchemyWorks/commit/6e3f791286d446ba09df42666dbec995ff187c31))
* remove retired changelog workflow reference ([f68b2aa](https://github.com/Albertzc/AlchemyWorks/commit/f68b2aac5fe0f661de6fb61eaf4bb36e63641bc9))
* rename project to Alchemy Works (AW) 软件开发工作流 ([160598d](https://github.com/Albertzc/AlchemyWorks/commit/160598d642e4d4c34409cdb38b916b84a28ef44c))
* update project branding in README ([53ad67c](https://github.com/Albertzc/AlchemyWorks/commit/53ad67c9e236fbb2d634ac959a8b60a45ea87174))
* **workflow:** root README.md is framework-owned and instance-gitignored ([2346e1b](https://github.com/Albertzc/AlchemyWorks/commit/2346e1ba2dc52e9f6c441a933de6035d5422a390))
