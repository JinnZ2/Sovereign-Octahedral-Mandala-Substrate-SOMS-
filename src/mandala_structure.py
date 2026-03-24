import numpy as np


class MandalaMap:
    """Generate Fibonacci-scaled 8-petal mandala geometry in 2D."""

    def __init__(self, u=20, depth=7):
        self.u = u  # Unit scale (nm)
        self.phi = (1 + 5**0.5) / 2
        self.pos = [[0, 0]]  # Root cell at origin

        for d in range(1, depth + 1):
            r = self.u * (self.phi**d)
            for p in range(8):
                theta = (2 * np.pi / 8) * p
                self.pos.append([r * np.cos(theta), r * np.sin(theta)])
        self.pos = np.array(self.pos)
