import pygame  # type: ignore
import pygame.gfxdraw  # type: ignore
import math
import numpy as np

# Initialize Pygame
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

class Keyboard:
    def __init__(self):
        self.currentKeyStates = None
        self.previousKeyStates = None
    def processInput(self):
        self.previousKeyStates = self.currentKeyStates
        self.currentKeyStates = pygame.key.get_pressed()
    def isKeyDown(self, keyCode):
        if self.currentKeyStates is None or self.previousKeyStates is None:
            return False
        return self.currentKeyStates[keyCode] == True
    def isKeyPressed(self, keyCode):
        if self.currentKeyStates is None or self.previousKeyStates is None:
            return False
        return self.currentKeyStates[keyCode] == True and self.previousKeyStates[keyCode] == False
    def isKeyReleased(self, keyCode):
        if self.currentKeyStates is None or self.previousKeyStates is None:
            return False
        return self.currentKeyStates[keyCode] == False and self.previousKeyStates[keyCode] == True

class Camera:
    def __init__(self, world_size, screen_size, border_margin=50, scale=1.0, max_scale=5.0, pan_speed=5, zoom_speed=0.1):
        self.world_size = world_size  # world size (width, height) in world units
        self.border_margin = border_margin  # margin around the world (border size in pixels)
        self.screen_size = pygame.Vector2(screen_size)  # screen size (width, height)
        self.offset = pygame.Vector2(0, 0)
        self.target_offset = pygame.Vector2(0, 0)

        self.scale = scale
        self.target_scale = scale
        self.min_scale = None
        self.max_scale = max_scale

        self.pan_speed = pan_speed  # speed for panning
        self.zoom_speed = zoom_speed

        self._dragging = False
        self._last_mouse_pos = pygame.Vector2(0, 0)
        self.use_world_panning = False

        self.lerp_speed = 0.15  # smoothness factor

        # Adjust the min_scale based on the world size + border
        self.calculate_min_scale()

    def calculate_min_scale(self):
        """Calculate the minimum scale to ensure the world + border is always visible."""
        world_width_with_border = self.world_size[0] + self.border_margin * 2
        world_height_with_border = self.world_size[1] + self.border_margin * 2

        # Ensure the world + border is visible when zooming out
        self.min_scale = min(self.screen_size.x / world_width_with_border, self.screen_size.y / world_height_with_border)

    def apply(self, world_pos):
        """Convert world coordinates to screen coordinates."""
        return pygame.Vector2(world_pos) * self.scale - self.offset

    def to_world(self, screen_pos):
        """Convert screen coordinates to world coordinates."""
        return (pygame.Vector2(screen_pos) + self.offset) / self.scale

    def zoom(self, zoom_factor, zoom_pos):
        pos = pygame.Vector2(zoom_pos)
        world_before = self.to_world(pos)
        self.target_scale = max(min(self.target_scale * zoom_factor, self.max_scale), self.min_scale)

        # Recalculate offset to zoom toward mouse
        world_after = world_before * self.target_scale
        self.target_offset = world_after - pos

    def handle_event(self, event, keyboard):
        """Handle mouse and wheel events, including zooming logic."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._dragging = True
            self._last_mouse_pos = pygame.Vector2(pygame.mouse.get_pos())

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False

        elif event.type == pygame.MOUSEWHEEL:
            zoom_factor = 1.1 if event.y > 0 else 0.9

            # Check if Shift key is pressed
            if keyboard.isKeyDown(pygame.K_LSHIFT) or keyboard.isKeyDown(pygame.K_RSHIFT):
                self.zoom(zoom_factor, (WIDTH // 2, HEIGHT // 2))
            else:
                self.zoom(zoom_factor, pygame.mouse.get_pos())
            

    def update(self, keyboard):
        """Update the camera position and scale."""
        if self.use_world_panning:
            movement = self.pan_speed * self.scale
        else:
            movement = self.pan_speed  # screen-space panning

        zoom_factor = 1
        if keyboard.isKeyDown(pygame.K_EQUALS):
            zoom_factor += self.zoom_speed
        if keyboard.isKeyDown(pygame.K_MINUS):
            zoom_factor -= self.zoom_speed

        if zoom_factor != 1:
            if keyboard.isKeyDown(pygame.K_LSHIFT) or keyboard.isKeyDown(pygame.K_RSHIFT):
                self.zoom(zoom_factor, (WIDTH // 2, HEIGHT // 2))
            else:
                self.zoom(zoom_factor, pygame.mouse.get_pos())

        if self._dragging:
            # Mouse drag panning
            mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
            delta = mouse_pos - self._last_mouse_pos
            self.offset -= delta
            self.target_offset = self.offset  # Sync target to avoid conflict
            self._last_mouse_pos = mouse_pos

        else:
            # Keyboard panning
            if keyboard.isKeyDown(pygame.K_LEFT):
                self.target_offset.x -= movement
            if keyboard.isKeyDown(pygame.K_RIGHT):
                self.target_offset.x += movement
            if keyboard.isKeyDown(pygame.K_UP):
                self.target_offset.y -= movement
            if keyboard.isKeyDown(pygame.K_DOWN):
                self.target_offset.y += movement

        # Smooth interpolation for camera movement
        self.offset += (self.target_offset - self.offset) * self.lerp_speed
        self.scale += (self.target_scale - self.scale) * self.lerp_speed

        # Clamp camera to the world bounds + border
        self.clamp_to_world()

    def toggle_panning_mode(self):
        """Toggle between world-space and screen-space panning."""
        self.use_world_panning = not self.use_world_panning
        print("Panning mode:", "World-space" if self.use_world_panning else "Screen-space")

    def follow_ant(self, x, y, target_scale=None, zoom_speed=0.1):
        """Focus the camera on an ant's position and optionally zoom in/out to a specific scale."""
        # Set the target scale if specified
        if target_scale is not None:
            self.target_scale = target_scale

        # Smoothly move camera to the ant's position
        screen_center = self.screen_size / 2

        # Update camera target position
        self.target_offset = pygame.Vector2(x, y) * self.scale - screen_center


    def clamp_to_world(self):
        """Prevent the camera from going out of bounds of the world + border."""
        # World bounds including the border
        world_width_with_border = self.world_size[0] + self.border_margin * 2
        world_height_with_border = self.world_size[1] + self.border_margin * 2

        # Max offset: the camera should never show more than the world + border
        max_offset = pygame.Vector2(world_width_with_border, world_height_with_border) * self.scale - self.screen_size
        self.target_offset.x = max(-self.border_margin * self.scale, min(self.target_offset.x, max_offset.x))
        self.target_offset.y = max(-self.border_margin * self.scale, min(self.target_offset.y, max_offset.y))

    def set_world_size(self, world_size):
        """Update the world size and recalculate the min_scale."""
        self.world_size = world_size
        self.calculate_min_scale()

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

def draw_ant(surface, x, y, camera):
    """Draws a realistic fire ant at (x, y) with the given scale and view offset."""

    scale, offset = camera.scale, camera.offset

    size = int(20 * scale)
    
    x, y = camera.apply((x, y))

    head_radius = size // 6
    thorax_radius = size // 8
    petiole_length = size // 12
    petiole_width = size // 14
    abdomen_length = size // 2
    abdomen_width = size // 3

    detail_length = size // 14
    detail_width = size // 11

    head_x, head_y = x, y

    thorax_x, thorax_y = x, head_y + head_radius * 3 // 2

    petiole_x, petiole_y = x, thorax_y + thorax_radius + petiole_length // 2

    abdomen_x, abdomen_y = x, petiole_y + petiole_length // 2 + abdomen_length // 2

    detail1_x, detail1_y = x, petiole_y - (petiole_length * 4 // 7)

    detail2_x, detail2_y = x, petiole_y + (petiole_length * 4 // 7)

    if abdomen_x - abdomen_width // 2 > WIDTH + abdomen_width or abdomen_x + abdomen_width // 2 < -abdomen_width or \
       head_y - head_radius > HEIGHT + abdomen_width or abdomen_y + abdomen_length // 2 < 0:
        return

    pygame.gfxdraw.aaellipse(surface, 
                             int(head_x), int(head_y), int(head_radius), int(head_radius), FIRE_ANT_RED)
    pygame.gfxdraw.filled_ellipse(surface, 
                                  int(head_x), int(head_y), int(head_radius), int(head_radius), FIRE_ANT_RED)

    pygame.gfxdraw.aaellipse(surface, 
                             int(petiole_x), int(petiole_y), int(petiole_width // 2), int(petiole_length // 2), FIRE_ANT_RED)
    pygame.gfxdraw.filled_ellipse(surface, 
                                  int(petiole_x), int(petiole_y), int(petiole_width // 2), int(petiole_length // 2), FIRE_ANT_RED)

    pygame.gfxdraw.aaellipse(surface, 
                             int(detail1_x), int(detail1_y), int(detail_width // 2), int(detail_length // 2), FIRE_ANT_RED)
    pygame.gfxdraw.filled_ellipse(surface, 
                                  int(detail1_x), int(detail1_y), int(detail_width // 2), int(detail_length // 2), FIRE_ANT_RED)

    pygame.gfxdraw.aaellipse(surface, 
                             int(detail2_x), int(detail2_y), int(detail_width // 2), int(detail_length // 2), DARK_RED)
    pygame.gfxdraw.filled_ellipse(surface, 
                                  int(detail2_x), int(detail2_y), int(detail_width // 2), int(detail_length // 2), DARK_RED)

    pygame.gfxdraw.aaellipse(surface, 
                             int(thorax_x), int(thorax_y), int(thorax_radius), int(thorax_radius), LIGHT_RED)
    pygame.gfxdraw.filled_ellipse(surface, 
                                  int(thorax_x), int(thorax_y), int(thorax_radius), int(thorax_radius), LIGHT_RED)

    pygame.gfxdraw.aaellipse(surface, 
                             int(abdomen_x), int(abdomen_y), int(abdomen_width // 2), int(abdomen_length // 2), DARK_RED)
    pygame.gfxdraw.filled_ellipse(surface, 
                                  int(abdomen_x), int(abdomen_y), int(abdomen_width // 2), int(abdomen_length // 2), DARK_RED)

    # Eyes (larger, positioned more to the sides of the head)
    eye_offset = head_radius // 2  # Place eyes more on the sides
    eye1_x = head_x - eye_offset - int(head_radius // 2.5)
    eye2_x = head_x + eye_offset + int(head_radius // 2.5)
    eyes_y = head_y - eye_offset // 2

    pygame.gfxdraw.aacircle(surface, 
                            int(eye1_x), int(eyes_y), int(head_radius // 3), BLACK)
    pygame.gfxdraw.filled_circle(surface, 
                            int(eye1_x), int(eyes_y), int(head_radius // 3), BLACK)
    
    pygame.gfxdraw.aacircle(surface, 
                            int(eye2_x), int(eyes_y), int(head_radius // 3), BLACK)
    pygame.gfxdraw.filled_circle(surface, 
                            int(eye2_x), int(eyes_y), int(head_radius // 3), BLACK)

    # Antennae
    ant_length = int(head_radius * 2.5)

    A0_X0 = pygame.Vector2(head_x - head_radius, head_y - head_radius)
    A0_X1 = pygame.Vector2(head_x - ant_length, head_y - ant_length)

    A1_X0 = pygame.Vector2(head_x + head_radius, head_y - head_radius)
    A1_X1 = pygame.Vector2(head_x + ant_length, head_y - ant_length)

    thickness = max(1, int(scale / 2))

    p1s = (A0_X0, A1_X0)
    p2s = (A0_X1, A1_X1)

    corners = anti_aliase_line_coords(p1s, p2s, thickness)

    for rectangle in corners:
        pygame.gfxdraw.aapolygon(screen, rectangle, FIRE_ANT_RED)
        pygame.gfxdraw.filled_polygon(screen, rectangle, FIRE_ANT_RED)

    #points = np.array([[1, 2], [4, 6], [7, 10]])
    #deltas = points[:, None, :] - points[None, :, :]
    #distances = np.sqrt(np.einsum('ijk,ijk->ij', deltas, deltas))

    leg_length = size // 3
    angles = [-math.pi / 4, 0, math.pi / 4]  # Front, middle, back legs

    for side in [-1, 1]:  # Left and right
        for i, angle in enumerate(angles):
            # Leg base position on thorax
            leg_x = thorax_x + side * thorax_radius
            leg_y = thorax_y - thorax_radius // 2 + (i * thorax_radius // 2)

            # First segment (angled outward)
            seg1_len = leg_length // 2
            mid_angle = angle  # Keep this outward
            mid_x = leg_x + side * int(math.cos(mid_angle) * seg1_len)
            mid_y = leg_y + int(math.sin(mid_angle) * seg1_len)

            # Second segment (angled downward)
            seg2_len = leg_length // 2
            end_angle = math.pi / 2  # Vertical down
            end_x = mid_x + side * int(math.cos(end_angle) * seg2_len)
            end_y = mid_y + int(math.sin(end_angle) * seg2_len)

            # Draw the segmented leg with bend
            pygame.draw.line(surface, DARK_RED, (leg_x, leg_y), (mid_x, mid_y), max(1, int(scale / 2)))
            pygame.draw.line(surface, DARK_RED, (mid_x, mid_y), (end_x, end_y), max(1, int(scale / 2)))


# Game Loop
running = True

camera = Camera(scale=scale_factor, max_scale=MAX_SCALE, pan_speed=2, zoom_speed=0.1, world_size=WORLD_SIZE, screen_size=pygame.Vector2(WIDTH,HEIGHT), border_margin=BORDER_MARGIN)
camera.target_scale = camera.min_scale
keyboard = Keyboard()

while running:
    screen.fill(WHITE)  # Clear screen
    
    draw_ant(screen, WIDTH // 2, HEIGHT // 2, camera=camera)  # Draw scaled fire ant

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
    
    pygame.display.flip()  # Update display

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        camera.handle_event(event=event, keyboard=keyboard)
    
    keyboard.processInput()
    camera.update(keyboard=keyboard)
    clock.tick(60)

pygame.quit()
