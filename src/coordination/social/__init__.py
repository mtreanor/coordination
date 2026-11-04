"""The social layer: swappable components that hold the social world, each implementing SocialLayer."""

from .base import Ask, NoSocial, SocialLayer
from .rue import RueSocial

SOCIAL_LAYERS = {"off": NoSocial, "rue": RueSocial}
"""Every social layer a Run can be configured with, by name. Add a new version here."""

__all__ = ["SOCIAL_LAYERS", "Ask", "NoSocial", "RueSocial", "SocialLayer"]
