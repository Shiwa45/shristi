"""Aggregates the relationships app's models so Django discovers them."""
from relationships.weddings import (  # noqa: F401
    Ring, Marriage, FORCED_DIVORCE_COST, REUNION_GRACE_DAYS,
)
from relationships.mentorship import (  # noqa: F401
    Mentorship, CHARM_THRESHOLD, GRADUATION_GROWTH_POINTS, MAX_DISCIPLES_PER_MASTER,
)
