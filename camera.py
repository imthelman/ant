import pygame  # type: ignore

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
