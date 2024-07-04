import time
import pygame
import cmath
from math import pi, tau


class Gear:
    def __init__(self, theta, theta_velocity, rotation, radius, inner_radius, pen_holes, parent=None):
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
screen = pygame.display.set_mode([1200, 800])
graph = pygame.surface.Surface([screen.get_width(), screen.get_height()])

# Fill the background
graph.fill((255, 255, 255))

previous = time.time_ns()
frame = 0

center = (screen.get_width() // 2, screen.get_height() // 2)
outer_gear = Gear(0, 0, 0, 550, 473, [])
middle_gear = Gear(0, 0, 0, 550, 473, [])
inner_gear = Gear(0, tau, 0, 200, 0, [(137, 0)], outer_gear)
pen = Pen(inner_gear, inner_gear.pen_holes[0], 2, (255, 0, 0))

previous_pen_position = pen.get_position_on_page()


def to_screen(coords):
    global center
    x, y = coords
    return (
        int(x + center[0]),
        int(y + center[1])
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

    pygame.draw.line(graph, pen.color, to_screen(previous_pen_position), to_screen(pen_position), pen.thickness)
    screen.blit(graph, (0, 0))

    pygame.draw.circle(screen, (0, 0, 255), center, outer_gear.radius, 1)
    pygame.draw.circle(screen, (0, 0, 255), center, outer_gear.inner_radius, 1)

    inner_gear_center = inner_gear.translate_to_page((0, 0))
    inner_gear_top = inner_gear.translate_to_page((inner_gear.radius, 0))
    pygame.draw.circle(screen, (0, 255, 0), to_screen(inner_gear_center), inner_gear.radius, 1)
    pygame.draw.line(screen, (0, 255, 0), to_screen(inner_gear_center), to_screen(inner_gear_top), 1)

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
