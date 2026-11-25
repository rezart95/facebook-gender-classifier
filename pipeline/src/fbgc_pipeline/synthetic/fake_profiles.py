"""Deterministic fake profiles: invented Italian names (Faker it_IT) and phrase-bank chats.

Every profile is fake. The same (index, seed) always gives the same profile, so the
committed fixtures can be regenerated with `fbgc fake-profiles`.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from faker import Faker

from fbgc_pipeline.synthetic.fake_export import write_fake_export
from fbgc_pipeline.synthetic.fake_records import (
    FakeMessage,
    FakeProfile,
    FakeThread,
    FakeWallItem,
)
from fbgc_pipeline.synthetic.phrase_bank import (
    EVENT_NAMES,
    EVENT_REPLIES,
    PHRASES,
    RELATIONSHIP_LABELS,
    WALL_ACTIONS,
)
from fbgc_pipeline.synthetic.timestamp_format import format_fb_timestamp

FAKE_SEED = 2015
FIRST_DOWNLOAD = datetime(2015, 11, 20, 10, 0)
EVENING_HOURS = (9, 11, 13, 15, 17, 18, 19, 20, 21, 21, 22, 22, 23, 0, 1)


def rome(moment: datetime) -> datetime:
    """Attach the Rome offset of the month (summer time April to October, close enough)."""
    return moment.replace(tzinfo=timezone(timedelta(hours=2 if 4 <= moment.month <= 10 else 1)))


def invented_person(faker: Faker, female: bool) -> str:
    first = faker.first_name_female() if female else faker.first_name_male()
    return f"{first} {faker.last_name()}"


def invented_friends(faker: Faker, count: int, owner: str) -> list[str]:
    friends: list[str] = []
    while len(friends) < count:
        name = invented_person(faker, female=len(friends) % 2 == 0)
        if name != owner and name not in friends:
            friends.append(name)
    return friends


def moment_before(download: datetime, rng: random.Random) -> datetime:
    """A wall-clock moment in the 11 months before the download, mostly in the evening."""
    day = download - timedelta(days=rng.randint(1, 330))
    return rome(day.replace(hour=rng.choice(EVENING_HOURS), minute=rng.randint(0, 59)))


def chat(people: tuple[str, ...], download: datetime, rng: random.Random, n: int) -> FakeThread:
    messages = [
        FakeMessage(rng.choice(people), moment_before(download, rng), rng.choice(PHRASES))
        for _ in range(n)
    ]
    return FakeThread(people, tuple(sorted(messages, key=lambda message: message.sent_at)))


def generate_fake_profile(index: int, seed: int = FAKE_SEED) -> FakeProfile:
    """Fake profile number `index` (1-based): odd numbers are women, even numbers men."""
    rng = random.Random(seed * 1000 + index)
    faker = Faker("it_IT")
    faker.seed_instance(seed * 1000 + index)
    female = index % 2 == 1
    owner = invented_person(faker, female)
    friends = invented_friends(faker, 6, owner)
    download = rome(FIRST_DOWNLOAD + timedelta(days=9 * index))
    personal = [chat((owner, friend), download, rng, rng.randint(6, 12)) for friend in friends[:4]]
    group = chat((owner, *friends[3:]), download, rng, rng.randint(10, 16))
    wall = tuple(
        FakeWallItem(
            moment_before(download, rng),
            action.format(owner=owner, friend=rng.choice(friends)),
            rng.choice(PHRASES),
        )
        for action in WALL_ACTIONS
    )
    events = tuple(
        f"{name} - {format_fb_timestamp(moment_before(download, rng), 'it')} - "
        f"{rng.choice(EVENT_REPLIES)}"
        for name in EVENT_NAMES[: rng.randint(2, len(EVENT_NAMES))]
    )
    return FakeProfile(
        owner=owner,
        gender_label="Donna" if female else "Uomo",
        birthday=f"{rng.randint(13, 28):02d}/{rng.randint(1, 12):02d}/{rng.randint(1990, 1997)}",
        registered_at=rome(datetime(rng.randint(2008, 2012), rng.randint(1, 12), 15, 18, 30)),
        downloaded_at=download,
        relationship=rng.choice(RELATIONSHIP_LABELS),
        threads=(*personal, group),
        wall=wall,
        friend_sections=(
            ("Amici", rng.randint(40, 120)),
            ("Richieste di amicizia inviate", rng.randint(0, 5)),
            ("Richieste di amicizia ricevute", rng.randint(0, 8)),
            ("Amici rimossi", rng.randint(0, 3)),
        ),
        events=events,
    )


def write_fake_profiles(out_dir: Path, count: int, seed: int = FAKE_SEED) -> list[Path]:
    """Write fake-01, fake-02, ... under `out_dir` in the layout of a real export."""
    return [
        write_fake_export(out_dir / f"fake-{index:02d}", generate_fake_profile(index, seed))
        for index in range(1, count + 1)
    ]
