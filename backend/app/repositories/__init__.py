"""Capa de repositorios: el acceso a datos vive aqui, no en los endpoints.

Patron *repository*: los endpoints de FastAPI orquestan, pero todo el SQL y la
logica de persistencia se concentra en estos modulos. Asi el endpoint queda
delgado y las consultas se pueden probar sin levantar HTTP.
"""

from __future__ import annotations
