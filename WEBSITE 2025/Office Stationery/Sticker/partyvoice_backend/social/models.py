"""Aggregates the social app's models so Django discovers them.

Models are defined in topic modules (families.py, feed.py) for readability;
importing them here registers them under the 'social' app label.
"""
from social.families import (  # noqa: F401
    Family, FamilyMember, FamilyJoinRequest, FAMILY_CREATION_COST,
)
from social.feed import (  # noqa: F401
    Relationship, Post, PostLike, PostComment,
)
