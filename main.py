import time
import pygame
import cmath
import math
from math import pi, tau


class Gear:
    def __init__(self, theta, theta_velocity, rotation, radius, inner_radius, pen_holes, color, parent=None):
        # Theta and theta velocity relative to the parent
        self.theta = theta
        self.theta_velocity = theta_velocity
        # Rotation of the gear
        self.rotation = rotation
        # Radius of the gear
        self.radius = radius
        # Inner radius of the gear (or zero if the gear is solid)
        self.inner_radius = inner_radius
        # Holes for the pen in polar coordinates from the center of the gear
        self.pen_holes = pen_holes or []
        # Color of the gear
        self.color = color
        # The parent gear to which this one is attached
        self.parent = parent

    # Updates this gear and its parents after the given elapsed time
    def update(self, elapsed):
        # The gear moves at a constant theta velocity relative to its parent
        theta_delta = self.theta_velocity * elapsed
        self.theta += theta_delta

        # The gear rotates proportional to the ratio of its radius to the parent gear's inner radius
        if self.parent is not None:
            rotation_delta = theta_delta * (self.parent.inner_radius / self.radius)  # ??
            self.rotation -= rotation_delta

            self.parent.update(elapsed)

    # Translates a position in this gear's polar coordinates to page coordinates
    def translate_to_page(self, position) -> tuple:
        eccentricity, phi = position

        if self.parent is not None:
            # Convert the center of this gear into rect coords in the parent's coordinate system
            center = cmath.rect(self.parent.inner_radius - self.radius, self.theta)

            # Convert the position above into rect coords in parent's coordinate system
            position_rect = cmath.rect(eccentricity, phi + self.rotation)  # ??

            # Add these two vectors together and convert back to polar in parent's coordinates
            parent_position = cmath.polar(center + position_rect)

            return self.parent.translate_to_page(parent_position)
        else:
            # No parent, so just convert to rectangular coordinates
            rect = cmath.rect(eccentricity, phi)
            return rect.real, rect.imag


class Pen:
    def __init__(self, gear, pen_hole, thickness, color):
        self.gear = gear
        self.pen_hole = pen_hole
        self.thickness = thickness
        self.color = color

    # Update the pen and all gears after the given elapsed time
    def update(self, elapsed):
        # Update the gear (and all its parents) first
        self.gear.update(elapsed)

    # Return the (x, y) coordinate on the page of the pen
    def get_position_on_page(self) -> tuple:
        return self.gear.translate_to_page(self.pen_hole)


pygame.init()
clock = pygame.time.Clock()

# Set up the drawing window
screen = pygame.display.set_mode([1400, 1000])
graph = pygame.surface.Surface([screen.get_width(), screen.get_height()])

# Fill the background
graph.fill((255, 255, 255))

start = time.time_ns()
previous = time.time_ns()
frame = 0

center = (screen.get_width() // 2, screen.get_height() // 2)

outer_gear = Gear(0, 0, 0, 550, 473, [], (0, 0, 255))
middle_gear = Gear(0, tau, 0, 350, 275, [], (0, 255, 255), outer_gear)
inner_gear = Gear(0, tau, 0, 150, 0, [(97, 0)], (0, 255, 0), middle_gear)
gears = [outer_gear, middle_gear, inner_gear]

pen = Pen(inner_gear, inner_gear.pen_holes[0], 2, (255, 0, 0))

previous_pen_position = pen.get_position_on_page()


def to_screen(coords):
    global center
    x, y = coords
    return (
        int(x + center[0]),
        int(y + center[1])
    )


def color_for_time(time):
    period = (2, 1, 4)
    return (
        int((math.sin(time / period[0]) + 1) * 0.5 * 200),
        int((math.sin(time / period[1]) + 1) * 0.5 * 200),
        int((math.sin(time / period[2]) + 1) * 0.5 * 200)
    )


# Run until the user asks to quit
running = True
while running:
    now = time.time_ns()
    elapsed = (now - previous) / 1e9
    previous = now

    # Did the user click the window close button?
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update the position of the pen
    pen.update(elapsed)
    pen_position = pen.get_position_on_page()

    total_time = (time.time_ns() - start) / 1e9
    changing_color = color_for_time(total_time)
    pygame.draw.line(graph, changing_color, to_screen(previous_pen_position), to_screen(pen_position), pen.thickness)
    screen.blit(graph, (0, 0))

    for gear in gears:
        gear_center = to_screen(gear.translate_to_page((0, 0)))
        gear_top = to_screen(gear.translate_to_page((gear.radius, pi / 2)))

        pygame.draw.circle(screen, gear.color, gear_center, gear.radius, 3)
        if gear.inner_radius > 0:
            pygame.draw.circle(screen, gear.color, gear_center, gear.inner_radius, 3)

        pygame.draw.line(screen, gear.color, to_screen(gear_center), to_screen(gear_top), 1)

    # Remember the current pen position for next loop
    previous_pen_position = pen_position

    # Flip the display
    pygame.display.flip()

    frame += 1
    if frame % 60 == 0:
        print(clock.get_fps())
    clock.tick(600)

# Done! Time to quit.
pygame.quit()
