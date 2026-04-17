from __future__ import annotations

from typing import Any, Callable


class StructTypeRegistry:
    def __init__(self) -> None:
        self._decoders: dict[str, Callable[[bytes], Any]] = {}

    def register(self, type_str: str, decoder: Callable[[bytes], Any]) -> None:
        self._decoders[type_str] = decoder

    def decode(self, type_str: str, raw: bytes) -> Any:
        return self._decoders[type_str](raw)

    def can_decode(self, type_str: str) -> bool:
        return type_str in self._decoders


def _build_default_registry() -> StructTypeRegistry:
    registry = StructTypeRegistry()
    try:
        from wpimath.geometry import Pose2d, Rotation2d, Translation2d, Transform2d, Twist2d
        from wpimath.kinematics import ChassisSpeeds, SwerveModuleState, SwerveModulePosition
        from wpiutil import wpistruct

        for cls in [
            Pose2d,
            Rotation2d,
            Translation2d,
            Transform2d,
            Twist2d,
            ChassisSpeeds,
            SwerveModuleState,
            SwerveModulePosition,
        ]:
            type_str = "struct:" + wpistruct.getTypeName(cls)
            registry.register(type_str, lambda b, c=cls: wpistruct.unpack(c, b))
    except ImportError:
        pass
    return registry


default_registry = _build_default_registry()
