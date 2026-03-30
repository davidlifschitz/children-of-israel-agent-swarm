"""Tribe registry — maps tribe_id to LangGraph node function."""

from .tribe_reuben import reuben_node
from .tribe_simeon import simeon_node
from .tribe_levi import levi_node
from .tribe_judah import judah_node
from .tribe_issachar import issachar_node
from .tribe_zebulun import zebulun_node
from .tribe_dan import dan_node
from .tribe_naphtali import naphtali_node
from .tribe_gad import gad_node
from .tribe_asher import asher_node
from .tribe_joseph import joseph_node
from .tribe_benjamin import benjamin_node

TRIBE_REGISTRY = {
    "reuben": reuben_node,
    "simeon": simeon_node,
    "levi": levi_node,
    "judah": judah_node,
    "issachar": issachar_node,
    "zebulun": zebulun_node,
    "dan": dan_node,
    "naphtali": naphtali_node,
    "gad": gad_node,
    "asher": asher_node,
    "joseph": joseph_node,
    "benjamin": benjamin_node,
}

__all__ = ["TRIBE_REGISTRY"]
