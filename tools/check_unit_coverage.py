#!/usr/bin/env python3
"""Check that each source module has >=98% coverage from its mirror unit test file."""

from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET_PCT = 98

SOURCES = """\
src/ceres/__init__.py
src/ceres/adapters/__init__.py
src/ceres/adapters/travellermap.py
src/ceres/character/__init__.py
src/ceres/character/domain/__init__.py
src/ceres/character/domain/benefits.py
src/ceres/character/domain/career/__init__.py
src/ceres/character/domain/career/advancement.py
src/ceres/character/domain/career/agent.py
src/ceres/character/domain/career/army.py
src/ceres/character/domain/career/career_data.py
src/ceres/character/domain/career/career_events.py
src/ceres/character/domain/career/citizen.py
src/ceres/character/domain/career/common.py
src/ceres/character/domain/career/common_pending.py
src/ceres/character/domain/career/draft.py
src/ceres/character/domain/career/drifter.py
src/ceres/character/domain/career/entertainer.py
src/ceres/character/domain/career/entry.py
src/ceres/character/domain/career/loader.py
src/ceres/character/domain/career/marines.py
src/ceres/character/domain/career/merchant.py
src/ceres/character/domain/career/muster_out.py
src/ceres/character/domain/career/navy.py
src/ceres/character/domain/career/noble.py
src/ceres/character/domain/career/prisoner.py
src/ceres/character/domain/career/prisoner_events.py
src/ceres/character/domain/career/psion.py
src/ceres/character/domain/career/rogue.py
src/ceres/character/domain/career/scholar.py
src/ceres/character/domain/career/scout.py
src/ceres/character/domain/character_start.py
src/ceres/character/domain/character_state.py
src/ceres/character/domain/characteristics.py
src/ceres/character/domain/choice_events.py
src/ceres/character/domain/connection.py
src/ceres/character/domain/connection_events.py
src/ceres/character/domain/dice.py
src/ceres/character/domain/event_handlers.py
src/ceres/character/domain/health/__init__.py
src/ceres/character/domain/health/health_events.py
src/ceres/character/domain/homeworld/__init__.py
src/ceres/character/domain/homeworld/homeworld_events.py
src/ceres/character/domain/life_events.py
src/ceres/character/domain/precareer/__init__.py
src/ceres/character/domain/precareer/colonial_upbringing.py
src/ceres/character/domain/precareer/loader.py
src/ceres/character/domain/precareer/merchant_academy.py
src/ceres/character/domain/precareer/military_academy.py
src/ceres/character/domain/precareer/precareer_data.py
src/ceres/character/domain/precareer/precareer_events.py
src/ceres/character/domain/precareer/psionic_community.py
src/ceres/character/domain/precareer/school_of_hard_knocks.py
src/ceres/character/domain/precareer/spacer_community.py
src/ceres/character/domain/precareer/university.py
src/ceres/character/domain/psionics.py
src/ceres/character/domain/skill_events.py
src/ceres/character/domain/skills.py
src/ceres/character/domain/sophont/__init__.py
src/ceres/character/domain/sophont/humaniti.py
src/ceres/character/domain/spec.py
src/ceres/character/domain/term_data.py
src/ceres/character/input_specs.py
src/ceres/character/mechanism/__init__.py
src/ceres/character/mechanism/errors.py
src/ceres/character/mechanism/event_base.py
src/ceres/character/mechanism/pending_input.py
src/ceres/character/mechanism/replay.py
src/ceres/character/mechanism/store.py
src/ceres/character/notes.py
src/ceres/character/report.py
src/ceres/character/web/__init__.py
src/ceres/character/web/app.py
src/ceres/character/web/routes.py
src/ceres/gear/__init__.py
src/ceres/gear/catalog.py
src/ceres/gear/comm.py
src/ceres/gear/computer.py
src/ceres/gear/skill_keys.py
src/ceres/gear/software.py
src/ceres/make/__init__.py
src/ceres/make/robot/__init__.py
src/ceres/make/robot/_facades.py
src/ceres/make/robot/_robot_skill_base.py
src/ceres/make/robot/base.py
src/ceres/make/robot/brain.py
src/ceres/make/robot/chassis.py
src/ceres/make/robot/locomotion.py
src/ceres/make/robot/manipulators.py
src/ceres/make/robot/options.py
src/ceres/make/robot/parts.py
src/ceres/make/robot/report.py
src/ceres/make/robot/robot.py
src/ceres/make/robot/skills.py
src/ceres/make/robot/spec.py
src/ceres/make/robot/text.py
src/ceres/make/ship/__init__.py
src/ceres/make/ship/armour.py
src/ceres/make/ship/automation.py
src/ceres/make/ship/base.py
src/ceres/make/ship/bridge.py
src/ceres/make/ship/catalog.py
src/ceres/make/ship/computer.py
src/ceres/make/ship/crafts.py
src/ceres/make/ship/crew.py
src/ceres/make/ship/drives/__init__.py
src/ceres/make/ship/drives/spinext.py
src/ceres/make/ship/drives/standard.py
src/ceres/make/ship/expense.py
src/ceres/make/ship/habitation.py
src/ceres/make/ship/hull/__init__.py
src/ceres/make/ship/hull/spinext.py
src/ceres/make/ship/hull/standard.py
src/ceres/make/ship/occupants.py
src/ceres/make/ship/parts.py
src/ceres/make/ship/power.py
src/ceres/make/ship/report.py
src/ceres/make/ship/screens.py
src/ceres/make/ship/sensors.py
src/ceres/make/ship/ship.py
src/ceres/make/ship/software.py
src/ceres/make/ship/spec.py
src/ceres/make/ship/storage.py
src/ceres/make/ship/systems/__init__.py
src/ceres/make/ship/systems/acceleration.py
src/ceres/make/ship/systems/access.py
src/ceres/make/ship/systems/advanced.py
src/ceres/make/ship/systems/command.py
src/ceres/make/ship/systems/common.py
src/ceres/make/ship/systems/common_areas.py
src/ceres/make/ship/systems/drones.py
src/ceres/make/ship/systems/external.py
src/ceres/make/ship/systems/facilities.py
src/ceres/make/ship/systems/logistics.py
src/ceres/make/ship/systems/medical.py
src/ceres/make/ship/systems/reentry.py
src/ceres/make/ship/systems/section.py
src/ceres/make/ship/systems/security.py
src/ceres/make/ship/text.py
src/ceres/make/ship/view.py
src/ceres/make/ship/weapons/__init__.py
src/ceres/make/ship/weapons/barbettes.py
src/ceres/make/ship/weapons/bays.py
src/ceres/make/ship/weapons/common.py
src/ceres/make/ship/weapons/magazines.py
src/ceres/make/ship/weapons/mounts.py
src/ceres/make/ship/weapons/point_defense.py
src/ceres/make/ship/weapons/section.py
src/ceres/make/ship/weapons/spinal.py
src/ceres/report/__init__.py
src/ceres/report/render.py
src/ceres/settings.py
src/ceres/shared.py
src/ceres/worlds/__init__.py
src/ceres/worlds/sector_filters.py\
""".splitlines()


def is_empty_init(path: Path) -> bool:
    return path.name == '__init__.py' and path.stat().st_size == 0


def test_path_for(src: Path) -> Path:
    rel = src.relative_to(REPO_ROOT / 'src' / 'ceres')
    return REPO_ROOT / 'tests' / 'unit' / rel.parent / f'test_{rel.name}'


def measure_coverage(test_file: Path, src_file: Path) -> int | None:
    result = subprocess.run(
        [
            'uv',
            'run',
            'pytest',
            f'--cov={src_file.relative_to(REPO_ROOT)}',
            '--cov-branch',
            '--cov-report=term-missing',
            '-q',
            '--tb=no',
            str(test_file.relative_to(REPO_ROOT)),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    target = str(src_file.relative_to(REPO_ROOT))
    for line in (result.stdout + result.stderr).splitlines():
        if target in line:
            parts = line.split()
            try:
                return int(parts[-1].rstrip('%'))
            except ValueError, IndexError:
                return None
    return None


def main() -> int:
    rows: list[tuple[str, str, str]] = []
    passes = fails = no_test = skipped = 0

    for src_str in SOURCES:
        src = REPO_ROOT / src_str

        if is_empty_init(src):
            skipped += 1
            continue

        test_file = test_path_for(src)

        if not test_file.exists():
            rows.append(('NO TEST', src_str, str(test_file.relative_to(REPO_ROOT))))
            no_test += 1
            continue

        pct = measure_coverage(test_file, src)

        if pct is None:
            rows.append(('NO DATA', src_str, str(test_file.relative_to(REPO_ROOT))))
            fails += 1
        elif pct < TARGET_PCT:
            rows.append((f'{pct}%', src_str, str(test_file.relative_to(REPO_ROOT))))
            fails += 1
        else:
            rows.append((f'{pct}%', src_str, ''))
            passes += 1

    src_w = max((len(r[1]) for r in rows), default=40)

    for status, src_label, detail in rows:
        ok = status.endswith('%') and int(status[:-1]) >= TARGET_PCT
        marker = 'PASS' if ok else 'FAIL'
        print(f'{marker}  {status:>7}  {src_label:<{src_w}}  {detail}')

    print()
    print(f'passed={passes}  failed={fails}  no_test={no_test}  skipped_empty_init={skipped}')
    return 0 if (fails == 0 and no_test == 0) else 1


if __name__ == '__main__':
    sys.exit(main())
