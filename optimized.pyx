cimport cython
cimport numpy as np
import numpy as np
import pygame
import pygame.gfxdraw
cimport pygame
from cython cimport double, bint
from libc.math cimport sin, cos, atan2, pi
from array import array
from pygame.math import Vector2

cdef np.ndarray x_offsets0 = np.array([-1.75, -2.0, -1.0, 1.75, 2.0, 1.0], dtype=np.float64)
cdef np.ndarray y_offsets0 = np.array([4.0, 6.0, 7.0], dtype=np.float64)

cdef np.ndarray x_offsets = np.array([-5.5, -6.5, -7.0, 5.5, 6.5, 7.0], dtype=np.float64)
cdef np.ndarray y_offsets = np.array([10.0, 0.5, -10.0], dtype=np.float64)

cdef np.ndarray max_distortions = np.array([5.0, 5.0, 4.0], dtype=np.float64)

# Optional: assign memoryviews for better performance inside loops
#cdef double[:] x_offsets0 = _x_offsets0
#cdef double[:] y_offsets0 = _y_offsets0
#cdef double[:] x_offsets = _x_offsets
#cdef double[:] y_offsets = _y_offsets
#cdef double[:] max_distortions = _max_distortions

cdef int interpolation_frames = 20
cdef double max_rotation_speed = 4.0

cdef np.ndarray eased_t = 3 * np.linspace(0, 1, interpolation_frames)**2 - 2 * np.linspace(0, 1, interpolation_frames)**3

def draw_rotated_ellipse(int cx, int cy, int width, int height, tuple color, float angle, int ss_factor=2):
    """
    Draw an anti-aliased ellipse with supersampling (smooth scaling).
    
    Parameters:
      cx, cy: Center coordinates where the final ellipse should be centered.
      width, height: The desired half-width and half-height of the ellipse.
         (The final ellipse will fit in a box of size 2*width x 2*height.)
      color: A tuple specifying the ellipse color.
      angle: Rotation angle in degrees.
      ss_factor: Supersampling factor (default 2). The ellipse is drawn at
         (width*ss_factor, height*ss_factor) resolution and then scaled down.
    
    Returns:
      A tuple (final_surface, final_rect) where final_surface is a pygame.Surface
      containing the rotated ellipse and final_rect is its rect centered at (cx, cy).
    """
    cdef int high_width = width * ss_factor
    cdef int high_height = height * ss_factor

    # Create a high resolution surface; we double dimensions so the ellipse fits.
    cdef object high_res_surface = pygame.Surface((high_width * 2, high_height * 2), pygame.SRCALPHA)
    
    # Draw the ellipse at high resolution:
    # Center of the ellipse on the high-res surface:
    cdef int high_cx = high_width
    cdef int high_cy = high_height
    pygame.gfxdraw.filled_ellipse(high_res_surface, high_cx, high_cy, high_width, high_height, color)
    pygame.gfxdraw.aaellipse(high_res_surface, high_cx, high_cy, high_width, high_height, color)
    
    # Rotate the high resolution surface
    cdef object rotated_high_res = pygame.transform.rotate(high_res_surface, angle)
    
    # Determine the target size. We want to scale the rotated surface down by the supersampling factor.
    cdef int target_width = rotated_high_res.get_width() // ss_factor
    cdef int target_height = rotated_high_res.get_height() // ss_factor
    
    # Use smoothscale to downscale the rotated surface.
    cdef object final_surface = pygame.transform.smoothscale(rotated_high_res, (target_width, target_height))
    
    # Get a rect for the final surface and center it at (cx, cy)
    cdef object final_rect = final_surface.get_rect(center=(cx, cy))
    
    return final_surface, final_rect

@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline double deg_to_rad(double angle):
    return angle * 3.141592653589793 / 180.0

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef rotate_point(double px, double py, double ox, double oy, double angle):
    cdef double rad = deg_to_rad(angle)
    cdef double s = sin(rad)
    cdef double c = cos(rad)

    px -= ox
    py -= oy

    cdef double xnew = px * c - py * s
    cdef double ynew = px * s + py * c

    return [xnew + ox, ynew + oy]

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef compute_ant_geometry(
    np.ndarray foot_positions,
    double scale,
    np.ndarray geometry_out,
    np.ndarray ant_parts_geometry,
    np.ndarray ant_positions,  # Added: Positions of the ants (x, y)
    np.ndarray ant_directions  # Added: Directions of the ants (direction of movement)
):
    cdef int num_ants = foot_positions.shape[0]
    cdef double size, hr, tr, pl, pw, al, aw, dl, dw, ex
    cdef double head_y, thorax_y, petiole_y, abdomen_y, detail1_y, detail2_y, eye_offset
    cdef double hip0x, hip1x, hip2x, hip3x, hip4x, hip5x, hips0y, hips1y, hips2y
    cdef int i, j
    cdef double angle, cos_angle, sin_angle
    cdef double cx, cy  # Center (x, y) for rotation

    # Loop through each ant
    for i in range(num_ants):
        # Get the size for this ant
        size = ant_parts_geometry[i, 0, 0]  # Assuming 'size' is stored in the first part of geometry

        ant_parts_geometry[i, 0, 0] = 0

        # Calculate body part sizes based on 'size'
        hr = size / 6
        tr = size / 8
        pl = size / 12
        pw = size / 14
        al = size / 2
        aw = size / 3
        dl = size / 14
        dw = size / 11

        # Get the ant's position and direction
        cx, cy = ant_positions[i]  # (x, y) position of the ant
        angle = (ant_directions[i])  # Convert direction + 90

        # Y-offsets for the body parts
        head_y =  cy
        thorax_y = head_y + hr * 3 // 2
        petiole_y = thorax_y + tr + pl // 2
        abdomen_y = petiole_y + pl // 2 + al // 2
        detail1_y = petiole_y - (pl * 4 // 7)
        detail2_y = petiole_y + (pl * 4 // 7)
        eye_offset = hr

        # Hip-offsets
        hip0x = x_offsets0[0]
        hip1x = x_offsets0[1]
        hip2x = x_offsets0[2]
        hip3x = x_offsets0[3]
        hip4x = x_offsets0[4]
        hip5x = x_offsets0[5]

        hips0y = y_offsets0[0]
        hips1y = y_offsets0[1]
        hips2y = y_offsets0[2]

        # Calculate geometry (positions) for body parts based on size and offsets
        # Example of the head position calculation
        '''geometry_out[i, 0] = rotate_point(cx - 2*(ant_parts_geometry[i, 0, 0]), cy - 2*(ant_parts_geometry[i, 0, 1]), cx, cy, angle)  # Head
        geometry_out[i, 1] = rotate_point(cx - 2*(ant_parts_geometry[i, 1, 0]), cy - 2*(ant_parts_geometry[i, 1, 1] + thorax_dy), cx, cy, angle)  # Thorax
        geometry_out[i, 2] = rotate_point(cx - 2*(ant_parts_geometry[i, 2, 0]), cy - 2*(ant_parts_geometry[i, 2, 1] + petiole_dy), cx, cy, angle)  # Petiole
        geometry_out[i, 3] = rotate_point(cx - 2*(ant_parts_geometry[i, 3, 0]), cy - 2*(ant_parts_geometry[i, 3, 1] + detail1_dy), cx, cy, angle)  # Petiole detail 1
        geometry_out[i, 4] = rotate_point(cx - 2*(ant_parts_geometry[i, 4, 0]), cy - 2*(ant_parts_geometry[i, 4, 1] + detail2_dy), cx, cy, angle)  # Petiole detail 2
        geometry_out[i, 5] = rotate_point(cx - 2*(ant_parts_geometry[i, 5, 0]), cy - 2*(ant_parts_geometry[i, 5, 1] + abdomen_dy), cx, cy, angle)  # Abdomen
        geometry_out[i, 6] = rotate_point(cx - 2*(ant_parts_geometry[i, 6, 0] - ex), cy - 2*(ant_parts_geometry[i, 6, 1] + eye_offset), cx, cy, angle)  # Eye 1
        geometry_out[i, 7] = rotate_point(cx - 2*(ant_parts_geometry[i, 7, 0] + ex), cy - 2*(ant_parts_geometry[i, 7, 1] + eye_offset), cx, cy, angle)  # Eye 2

        geometry_out[i, 8] = rotate_point(cx - 2*(ant_parts_geometry[i, 8, 0] + hip0x), cy - ant_parts_geometry[i, 8, 1] + hips0y, cx, cy, angle)  # Top right hip
        geometry_out[i, 9] = rotate_point(cx - 2*(ant_parts_geometry[i, 9, 0] + hip1x), cy - ant_parts_geometry[i, 9, 1] + hips1y, cx, cy, angle)  # Middle right hip
        geometry_out[i, 10] = rotate_point(cx - 2*(ant_parts_geometry[i, 10, 0]) + hip2x, cy - 2*(ant_parts_geometry[i, 10, 1] + hips1y), cx, cy, angle)  # Bottom right hip
        geometry_out[i, 11] = rotate_point(cx - 2*(ant_parts_geometry[i, 11, 0]) + hip3x, cy - 2*(ant_parts_geometry[i, 11, 1] + hips0y), cx, cy, angle)  # Top left hip
        geometry_out[i, 12] = rotate_point(cx - 2*(ant_parts_geometry[i, 12, 0]) + hip4x, cy - 2*(ant_parts_geometry[i, 12, 1] + hips1y), cx, cy, angle)  # Middle left hip
        geometry_out[i, 13] = rotate_point(cx - 2*(ant_parts_geometry[i, 13, 0]) + hip5x, cy - 2*(ant_parts_geometry[i, 13, 1] + hips2y), cx, cy, angle)  # Bottom left hip'''

        geometry_out[i, 0] = (cx, head_y)  # Head
        geometry_out[i, 1] = rotate_point(cx, thorax_y, cx, cy, angle)  # Thorax
        geometry_out[i, 2] = rotate_point(cx, petiole_y, cx, cy, angle)  # Petiole
        geometry_out[i, 3] = rotate_point(cx, detail1_y, cx, cy, angle)  # Petiole detail 1
        geometry_out[i, 4] = rotate_point(cx, detail2_y, cx, cy, angle)  # Petiole detail 2
        geometry_out[i, 5] = rotate_point(cx, abdomen_y, cx, cy, angle)  # Abdomen
        geometry_out[i, 6] = rotate_point(cx - eye_offset - int(hr // 2.5), head_y - eye_offset // 2, cx, cy, angle)  # Eye 1
        geometry_out[i, 7] = rotate_point(cx + eye_offset + int(hr // 2.5), head_y - eye_offset // 2, cx, cy, angle)  # Eye 2

        geometry_out[i, 8] = rotate_point(cx + hip0x, cy + hips0y, cx, cy, angle)  # Top right hip
        geometry_out[i, 9] = rotate_point(cx + hip1x, cy + hips1y, cx, cy, angle)  # Middle right hip
        geometry_out[i, 10] = rotate_point(cx + hip2x, cy + hips1y, cx, cy, angle)  # Bottom right hip
        geometry_out[i, 11] = rotate_point(cx + hip3x, cy + hips0y, cx, cy, angle)  # Top left hip
        geometry_out[i, 12] = rotate_point(cx + hip4x, cy + hips1y, cx, cy, angle)  # Middle left hip
        geometry_out[i, 13] = rotate_point(cx + hip5x, cy + hips2y, cx, cy, angle)  # Bottom left hip

    return geometry_out

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef left_right(
    double x, double y, 
    tuple target, double dir
):
    cdef double tx = float(target[0])
    cdef double ty = float(target[1])

    cdef double rad = dir * (pi / 180.0)
    cdef double vx = cos(rad)
    cdef double vy = sin(rad)

    cdef double dx = tx - x
    cdef double dy = ty - y

    # Cross product of (vx, vy) and (dx, dy)
    cdef double cross = vx * dy - vy * dx

    cdef bint left = False
    cdef bint right = False

    if abs(cross) < 5:
        pass
    elif cross > 0:
        right = True
    elif cross < 0:
        left = True

    return (left, right)

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef turn(ant, bint left, bint right, double max_rotation_speed):
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

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef anti_aliase_line_coords(
    points1, points2, double thickness=1.0
):
    # Ensure points1 and points2 are numpy arrays for element-wise operations
    points1 = np.asarray(points1)
    points2 = np.asarray(points2)

    # Check that points1 and points2 have the correct shape (N, 2)
    if points1.shape[1] != 2 or points2.shape[1] != 2:
        raise ValueError("points1 and points2 should be of shape (N, 2)")

    cdef np.ndarray[double, ndim=2] delta
    cdef np.ndarray[double, ndim=1] length, angle, cos_a, sin_a, dx_l, dy_l, dx_t, dy_t
    cdef np.ndarray[double, ndim=2] center, UL, UR, BR, BL, rectangles
    cdef double half_len, half_thick

    # Perform element-wise subtraction (which works with numpy arrays)
    delta = points1 - points2  # delta should be of shape (N, 2)

    # Compute length of each line segment (magnitude of delta)
    length = np.linalg.norm(delta, axis=1)  # Length is a 1D array of size N

    # Compute angle of each line segment
    angle = np.arctan2(delta[:, 1], delta[:, 0])  # Angle is a 1D array of size N

    # Compute the center of each line segment (midpoint)
    center = (points1 + points2) / 2.0  # Center is a (N, 2) array

    cos_a = np.cos(angle)
    sin_a = np.sin(angle)

    half_len = length / 2.0
    half_thick = thickness / 2.0

    dx_l = half_len * cos_a
    dy_l = half_len * sin_a
    dx_t = half_thick * sin_a
    dy_t = half_thick * cos_a

    # Calculate the four corners of the rectangles (representing the lines)
    UL = np.stack([center[:, 0] + dx_l - dx_t, center[:, 1] + dy_t + dy_l], axis=-1)
    UR = np.stack([center[:, 0] - dx_l - dx_t, center[:, 1] + dy_t - dy_l], axis=-1)
    BR = np.stack([center[:, 0] - dx_l + dx_t, center[:, 1] - dy_t - dy_l], axis=-1)
    BL = np.stack([center[:, 0] + dx_l + dx_t, center[:, 1] - dy_t + dy_l], axis=-1)

    rectangles = np.stack([UL, UR, BR, BL], axis=1)

    return rectangles

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef update_feet(
    object ant,
    np.ndarray x_offsets0,
    np.ndarray y_offsets0,
    np.ndarray x_offsets,
    np.ndarray y_offsets,
    np.ndarray max_distortions,
    np.ndarray eased_t,
    int interpolation_frames
):
    # Use local variables to reduce attribute lookups
    cdef int i
    cdef double x0, y0, ideal_x1, ideal_y1, sq1, sq2
    cdef np.ndarray apos, aideal, positions
    cdef tuple pos, ideal
    cdef double max_leg_length = 16.0
    cdef double min_leg_length = 3.0

    for i in range(6):
        max_distortion = max_distortions[i % 3]

        x0 = ant.x + x_offsets0[i]
        y0 = ant.y + y_offsets0[i % 3]

        ideal_x1 = x0 + x_offsets[i]
        ideal_y1 = y0 - y_offsets[i % 3]

        ideal = rotate_point(ideal_x1, ideal_y1, ant.x, ant.y, ant.dir + 90)
        x0, y0 = rotate_point(x0, y0, ant.x, ant.y, ant.dir + 90)

        pos = ant.feet_positions[i]
        apos = np.array(pos, dtype=np.float64)
        aideal = np.array(ideal, dtype=np.float64)

        sq1 = np.sum((apos - aideal)**2)
        sq2 = np.sum((apos - np.array([x0, y0]))**2)

        if ant.feet_frames[i] > 0:
            positions = apos + (aideal - apos) * eased_t[:, None]
            pos = positions[ant.feet_frames[i] - 1]
            ant.feet_frames[i] += 1

            if ant.feet_frames[i] > interpolation_frames:
                pos = ideal
                ant.feet_frames[i] = 0
        elif max_distortion**2 < sq1 or sq2 < min_leg_length**2 or max_leg_length**2 < sq2:
            ant.feet_frames[i] = 1

        ant.feet_positions[i] = pos

cdef class Ant:
    cdef public double x, y, speed, dir, rotation_speed
    cdef public int WIDTH, HEIGHT
    cdef public object target
    cdef public list feet_positions
    cdef public list feet_frames

    def __init__(self, int WIDTH=750, int HEIGHT=500, x=None, y=None, speed=None, dir=None, target=None):
        import random
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT

        self.x = random.randint(0, WIDTH) if x is None else x
        self.y = random.randint(0, HEIGHT) if y is None else y
        self.speed = 0.5 if speed is None else speed
        self.dir = random.randint(0, 360) if dir is None else dir
        self.rotation_speed = 0.0
        self.target = (random.randint(0, WIDTH), random.randint(0, HEIGHT)) if target is None else target

        self.feet_positions = []
        self.feet_frames = []

        cdef double x0, y0, x1, y1
        cdef int i

        for i in range(6):
            x0 = self.x + x_offsets0[i]
            y0 = self.y + y_offsets0[i % 3]

            x1 = x0 + x_offsets[i]
            y1 = y0 - y_offsets[i % 3]

            x1, y1 = rotate_point(x1, y1, self.x, self.y, self.dir + 90)

            self.feet_positions.append((x1, y1))
            self.feet_frames.append(0)

    cpdef update_feet(self):
        cdef int i
        cdef double x0, y0, ideal_x1, ideal_y1, sq1, sq2
        cdef np.ndarray apos, aideal, positions
        cdef tuple pos, ideal
        cdef double max_leg_length = 16.0
        cdef double min_leg_length = 3.0

        for i in range(6):
            max_distortion = max_distortions[i % 3]

            x0 = self.x + x_offsets0[i]
            y0 = self.y + y_offsets0[i % 3]

            ideal_x1 = x0 + x_offsets[i]
            ideal_y1 = y0 - y_offsets[i % 3]

            ideal = rotate_point(ideal_x1, ideal_y1, self.x, self.y, self.dir + 90)
            x0, y0 = rotate_point(x0, y0, self.x, self.y, self.dir + 90)

            pos = self.feet_positions[i]
            apos = np.array(pos, dtype=np.float64)
            aideal = np.array(ideal, dtype=np.float64)

            sq1 = np.sum((apos - aideal)**2)
            sq2 = np.sum((apos - np.array([x0, y0]))**2)

            if self.feet_frames[i] > 0:
                positions = apos + (aideal - apos) * eased_t[:, None]
                pos = positions[self.feet_frames[i] - 1]
                self.feet_frames[i] += 1

                if self.feet_frames[i] > interpolation_frames:
                    pos = ideal
                    self.feet_frames[i] = 0
            elif max_distortion**2 < sq1 or sq2 < min_leg_length**2 or max_leg_length**2 < sq2:
                self.feet_frames[i] = 1

            self.feet_positions[i] = pos

    cpdef update(self):
        cdef double rad

        if np.dot(np.array(self.target) - np.array([self.x, self.y]), np.array(self.target) - np.array([self.x, self.y])) < 4.0:
            import random
            self.target = (random.randint(0, self.WIDTH), random.randint(0, self.HEIGHT))

        cdef bint left, right
        left, right = left_right(self.x, self.y, self.target, self.dir)
        turn(self, left, right, max_rotation_speed)

        rad = deg_to_rad(self.dir)
        self.x += self.speed * cos(rad)
        self.y += self.speed * sin(rad)

        self.update_feet()