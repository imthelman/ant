from __future__ import annotations
import numpy as np # type: ignore
import math
from typing import TYPE_CHECKING

def rotate_point(
        px: int | float,
        py: int | float,
        cx: int |float,
        cy: int | float,
        angle: int | float
    ) -> tuple[float, float]:
        rad = math.radians(angle)
        dx, dy = px - cx, py - cy
        new_x = cx + dx * math.cos(rad) - dy * math.sin(rad)
        new_y = cy + dx * math.sin(rad) + dy * math.cos(rad)
        return (new_x, new_y)

def left_right(
        x: int | float,
        y: int | float,
        target: tuple[float, float],
        dir: int | float
    ) -> tuple[bool, bool]:
        rad = math.radians(dir)
        P3 = np.array(target)
        
        left, right = False, False
    
        vector_P1_P2 = np.array([np.cos(rad), np.sin(rad)])
    
        # Calculate the vectors from P1 to P2 and P1 to P3
        vector_P1_P3 = P3 - (x, y)
    
        # Compute the cross product
        cross_product = vector_P1_P2[0] * vector_P1_P3[1] - vector_P1_P2[1] * vector_P1_P3[0]
    
        # Determine the direction based on the cross product
        if abs(cross_product) < 5:
            pass
        if cross_product > 0:
            right = True
        elif cross_product < 0:
            left = True
        
        return (left, right)

if TYPE_CHECKING:
    from ant import Ant

def turn(
        ant: Ant,
        left: bool,
        right: bool,
        max_rotation_speed: int | float
    ) -> None:
        if left and not right:
            ant.rotation_speed = max(ant.rotation_speed - 0.75, -max_rotation_speed)
        elif right and not left:
            ant.rotation_speed = min(ant.rotation_speed + 0.75, max_rotation_speed)
        elif not left and not right:
            if ant.rotation_speed > 0:
                ant.rotation_speed = max(ant.rotation_speed - 0.75, 0.0)
            elif ant.rotation_speed < 0:
                ant.rotation_speed = min(ant.rotation_speed + 0.75, 0.0)

        ant.dir += ant.rotation_speed
        ant.dir %= 360
