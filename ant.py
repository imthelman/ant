import math
import numpy as np # type: ignore
from to_be_optimized import rotate_point, left_right, turn

x_offsets0 = np.array([-5, -7.5, -4.5, 5, 7.5, 4.5])
y_offsets0 = np.array([4, 10, 16])

x_offsets = np.array([-5.5, -11, -7, 5.5, 11, 7])
y_offsets = np.array([15, 1.5, -10.5])

max_distortions = np.array([6, 7 , 4])

interpolation_frames = 20
max_rotation_speed = 4

t_values = np.linspace(0, 1, interpolation_frames)
eased_t = 3 * t_values**2 - 2 * t_values**3

WIDTH, HEIGHT = 750, 500

class Ant:
    def __init__(
        self, 
        x: int | float | None = None, 
        y: int | float | None = None, 
        speed: int | float | None = None, 
        dir: int | float | None = None, 
        target: tuple[int | float, int | float] | None = None, 
        WIDTH: int = WIDTH, 
        HEIGHT: int = HEIGHT
    ) -> None:
        self.x = np.random.randint(0, WIDTH) if x == None else x
        self.y = np.random.randint(0, HEIGHT) if y == None else y
        self.speed = 0.5 if speed == None else speed
        self.dir = np.random.randint(0,360) if dir == None else dir
        self.target = (np.random.randint(0, WIDTH), np.random.randint(0, HEIGHT)) if target == None else target

        self.rotation_speed = 0

        self.feet_positions = []
        self.feet_frames = []
        self.hip_positions = []

        # Adjust foot position calculation to ensure proper symmetry on both sides
        for i in range(6):
            x0 = self.x + x_offsets0[i]
            y0 = self.y + y_offsets0[i%3]#4 + (i % 3) * 6

            x1 = x0 + x_offsets[i]  # + (12 * (-1 if i < 3 else 1))  # Forward step
            y1 = y0 - y_offsets[i%3] #+ (5 if i % 2 == 0 else 0)

            #x1, y1 = rotate_point(x1, y1, x0, y0, (-10 if i % 3 == 0 else -5 if i % 3 ==1 else 5) * (-1 if i < 3 else 1))

            x1, y1 = rotate_point(x1, y1, self.x, self.y, self.dir+90)

            #x2, y2 = rotate_point(x0, y0, self.x, self.y, self.dir)
            #x, y = rotate_point(x, y, x0, y0, (45 if i % 2 == 0 else 0) * (-1 if i < 3 else 1))
            x0, y0 = rotate_point(x0, y0, self.x, self.y, self.dir+90)
            self.feet_positions.append((x1, y1))
            self.feet_frames.append(0)
            self.hip_positions.append((x0, y0))

    def update_feet(self) -> None:
        for i in range(6):
            max_distortion = max_distortions[i%3]
            max_leg_length = 16
            min_leg_length = 3

            x0 = self.x + x_offsets0[i]
            y0 = self.y + y_offsets0[i%3]#4 + (i % 3) * 6

            ideal_x1 = x0 + x_offsets[i]  # + (12 * (-1 if i < 3 else 1))  # Forward step
            ideal_y1 = y0 - y_offsets[i%3]

            #ideal_x1, ideal_y1 = rotate_point(ideal_x1, ideal_y1, x0, y0, (-10 if i % 3 == 0 else -5 if i % 3 ==1 else 5) * (-1 if i < 3 else 1))

            ideal = rotate_point(ideal_x1, ideal_y1, self.x, self.y, self.dir+90)
    
            x0, y0 = rotate_point(x0, y0, self.x, self.y, self.dir+90)
            self.hip_positions[i] = (x0, y0)

            pos = self.feet_positions[i]
            apos = np.array(pos)
            aideal = np.array(ideal)
            sq1 = np.sum(np.square(apos - aideal))
            sq2 = np.sum(np.square(np.array(pos) - np.array([x0, y0])))

            if self.feet_frames[i] > 0:
                positions = apos + (aideal - apos) * eased_t[:, None]

                pos = positions[self.feet_frames[i] - 1]
                self.feet_frames[i] += 1

                if self.feet_frames[i] > interpolation_frames:
                    #pos = (int(ideal_x1), int(ideal_y1))
                    #feet_positions[i] = [(ideal_x1, ideal_y1), 0]
                    pos = ideal
                    self.feet_frames[i] = 0
            elif max_distortion**2 < sq1 or sq2 < min_leg_length**2 or max_leg_length**2 < sq2:
                self.feet_frames[i] = 1
            
            self.feet_positions[i] = pos

    def update(self):
        if np.sum(np.square(np.array(self.target) - np.array([self.x, self.y]))) < 4:
            self.target = (np.random.randint(50, WIDTH-49), np.random.randint(50, HEIGHT-49))

        left, right = left_right(self.x, self.y, self.target, self.dir)

        turn(self, left, right, max_rotation_speed)

        rad = math.radians(self.dir)
        self.x += self.speed * math.cos(rad)
        self.y += self.speed * math.sin(rad)

        self.update_feet()
        '''
        if self.y < -20:
            self.y = HEIGHT + 20
            for i in range(6):
                x, y = self.feet_positions[i][0]
                y = HEIGHT - y
                self.feet_positions[i][0] = (x, y)
        elif self.y > HEIGHT + 20:
            self.y = -20
            for i in range(6):
                x, y = self.feet_positions[i][0]
                y = y - HEIGHT - 20
                self.feet_positions[i][0] = (x, y)

        if self.x < -20:
            self.x = WIDTH + 20
            for i in range(6):
                x, y = self.feet_positions[i][0]
                x = WIDTH - x
                self.feet_positions[i][0] = (x, y)
        elif self.x > WIDTH + 20:
            self.x = -20
            for i in range(6):
                x, y = self.feet_positions[i][0]
                x = x - WIDTH - 20
                self.feet_positions[i][0] = (x, y)
        '''

