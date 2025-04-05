import pygame # type: ignore
import pygame.gfxdraw  # type: ignore
import math
import numpy as np # type: ignore
from ant import Ant
from to_be_optimized import rotate_point
from camera import Camera
from keyboard import Keyboard

pygame.init()

# Set up display
WIDTH, HEIGHT = 750, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Realistic Fire Ant with Scroll")
clock = pygame.time.Clock()

# Sim
WORLD_SIZE = pygame.Vector2(1875, 1250)
BORDER_MARGIN = 10 # Doesn't affect world size

# Colors
FIRE_ANT_RED = (139, 69, 19)  # Reddish-brown for fire ants
LIGHT_RED = (168, 117, 35)  # Slightly lighter red for shading
DARK_RED = (120, 40, 15)  # Slightly darker red for shading
BLACK = (0, 0, 0)  # Color for eyes
WHITE = (255, 255, 255)  # Color for background

# Initializations for movement and zooming
scale_factor = 1.0  # Initial scale factor
MAX_SCALE = 10.0

ants = [Ant(x=375, y=250, dir=-90)]

def anti_aliase_line_coords(points1, points2, thickness=1.0):
    points1 = np.asarray(points1)
    points2 = np.asarray(points2)

    delta = points1 - points2
    length = np.linalg.norm(delta, axis=1)
    angle = np.arctan2(delta[:, 1], delta[:, 0])
    center = (points1 + points2) / 2.0

    # Precompute sin and cos for angles
    cos_a = np.cos(angle)
    sin_a = np.sin(angle)

    half_len = length / 2.0
    half_thick = thickness / 2.0

    # Vectorized offset components for each corner
    dx_l = half_len * cos_a
    dy_l = half_len * sin_a
    dx_t = half_thick * sin_a
    dy_t = half_thick * cos_a

    # Compute all corners in bulk (shape: [N, 4, 2])
    UL = np.stack([center[:, 0] + dx_l - dx_t,
                   center[:, 1] + dy_t + dy_l], axis=-1)

    UR = np.stack([center[:, 0] - dx_l - dx_t,
                   center[:, 1] + dy_t - dy_l], axis=-1)

    BR = np.stack([center[:, 0] - dx_l + dx_t,
                   center[:, 1] - dy_t - dy_l], axis=-1)

    BL = np.stack([center[:, 0] + dx_l + dx_t,
                   center[:, 1] - dy_t + dy_l], axis=-1)

    # Combine all into a single array: shape [N, 4, 2]
    rectangles = np.stack([UL, UR, BR, BL], axis=1)

    return rectangles

def draw_ant(ant, surface, camera):

    angle = ant.dir + 90

    scale, offset = camera.scale, camera.offset

    size = int(20 * scale)

    x, y = camera.apply((ant.x, ant.y))

    head_radius = size // 6
    thorax_radius = size // 8
    petiole_length = size // 12
    petiole_width = size // 14
    abdomen_length = size // 2
    abdomen_width = size // 3

    detail_length = size // 14
    detail_width = size // 11

    head_x0, head_y0 = x, y

    thorax_x0, thorax_y0 = x, head_y0 + head_radius * 3 // 2

    petiole_x0, petiole_y0 = x, thorax_y0 + thorax_radius + petiole_length // 2

    abdomen_x0, abdomen_y0 = x, petiole_y0 + petiole_length // 2 + abdomen_length // 2

    detail1_x0, detail1_y0 = x, petiole_y0 - (petiole_length * 4 // 7)

    detail2_x0, detail2_y0 = x, petiole_y0 + (petiole_length * 4 // 7)

    eye_offset = head_radius // 2  # Place eyes more on the sides
    eye1_x0 = head_x0 - eye_offset - int(head_radius // 2.5)
    eye2_x0 = head_x0 + eye_offset + int(head_radius // 2.5)
    eyes_y = head_y0 - eye_offset // 2

    head_x, head_y = rotate_point(head_x0, head_y0, x, y, angle)
    thorax_x, thorax_y = rotate_point(thorax_x0, thorax_y0, x, y, angle)
    petiole_x, petiole_y = rotate_point(petiole_x0, petiole_y0, x, y, angle)
    abdomen_x, abdomen_y = rotate_point(abdomen_x0, abdomen_y0, x, y, angle)
    detail1_x, detail1_y = rotate_point(detail1_x0, detail1_y0, x, y, angle)
    detail2_x, detail2_y = rotate_point(detail2_x0, detail2_y0, x, y, angle)
    eye1_x, eye1_y = rotate_point(eye1_x0, eyes_y, x, y, angle)
    eye2_x, eye2_y = rotate_point(eye2_x0, eyes_y, x, y, angle)





    # Rotate and draw body parts
    #for px, py, radius, color in parts:
    #    rx, ry = rotate_point(px, py, x, y, angle)
    #    pygame.draw.circle(screen, color, (int(rx), int(ry)), radius)

    # Draw legs using original offsets and rotation
    thickness = max(1, int(scale * 2))

    p1sL = (tuple(map(int, ant.hip_positions[0])), tuple(map(int, ant.hip_positions[1])), tuple(map(int, ant.hip_positions[2])))
    p2sL = (tuple(map(int, ant.feet_positions[0])), tuple(map(int, ant.feet_positions[1])), tuple(map(int, ant.feet_positions[2])))

    cornersL = anti_aliase_line_coords(p1sL, p2sL, thickness)

    for rectangle in cornersL:
        pygame.gfxdraw.aapolygon(screen, rectangle, DARK_RED)
        pygame.gfxdraw.filled_polygon(screen, rectangle, DARK_RED)
    
    #for i in range(6):
    #    hip = tuple(map(int, ant.hip_positions[i]))
    #    foot = tuple(map(int, ant.feet_positions[i]))
    #    pygame.draw.line(screen, DARK_RED, hip, foot, 2)

    # Draw rotated antennae
    A0_X0 = pygame.Vector2(rotate_point(x-4, y-14, x, y, angle))
    A0_X1 = pygame.Vector2(rotate_point(x-10, y-20, x, y, angle))
    A1_X0 = pygame.Vector2(rotate_point(x+4, y-14, x, y, angle))
    A1_X1 = pygame.Vector2(rotate_point(x+10, y-20, x, y, angle))

    p1sA = (A0_X0, A1_X0)
    p2sA = (A0_X1, A1_X1)

    cornersA = anti_aliase_line_coords(p1sA, p2sA, thickness)

    for rectangle in cornersA:
        pygame.gfxdraw.aapolygon(screen, rectangle, FIRE_ANT_RED)
        pygame.gfxdraw.filled_polygon(screen, rectangle, FIRE_ANT_RED)

    tx, ty = ant.target

    #pygame.draw.circle(screen, (255, 0, 0), (int(ant.x), int(ant.y)), 3)
    #pygame.draw.circle(screen, (0, 0, 255), (int(tx), int(ty)), 3)


running = True

camera = Camera(scale=scale_factor, max_scale=MAX_SCALE, pan_speed=2, zoom_speed=0.1, world_size=WORLD_SIZE, screen_size=pygame.Vector2(WIDTH,HEIGHT), border_margin=BORDER_MARGIN)
camera.target_scale = camera.min_scale
keyboard = Keyboard()

while running:
    screen.fill((200, 200, 200))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        camera.handle_event(event=event, keyboard=keyboard)

    for ant in ants:
        ant.update()
        draw_ant(ant=ant, surface=screen, camera=camera)

    # Draw border
    thickness = max(1, int(camera.scale * BORDER_MARGIN))

    UL = camera.apply(pygame.Vector2(-thickness, -thickness))
    UR = camera.apply(pygame.Vector2(WORLD_SIZE[0]+thickness, -thickness))
    BR = camera.apply(pygame.Vector2(WORLD_SIZE[0]+thickness, WORLD_SIZE[1]+thickness))
    BL = camera.apply(pygame.Vector2(-thickness, WORLD_SIZE[1]+thickness))

    p1s = (UL, UR, BR, BL)
    p2s = (UR, BR, BL, UL)

    corners = anti_aliase_line_coords(p1s, p2s, thickness)

    for rectangle in corners:
        pygame.gfxdraw.aapolygon(screen, rectangle, BLACK)
        pygame.gfxdraw.filled_polygon(screen, rectangle, BLACK)

    pygame.display.flip()
    keyboard.processInput()
    camera.update(keyboard=keyboard)
    clock.tick(60)

pygame.quit()
