import numpy as np

class Mandala_Map:
    def __init__(self, u=20, depth=7):
        self.u = u # Unit scale 20nm
        self.phi = (1 + 5**0.5) / 2
        self.pos = [[0, 0]] # Root
        
        for d in range(1, depth + 1):
            r = self.u * (self.phi**d)
            for p in range(8):
                theta = (2 * np.pi / 8) * p
                self.pos.append([r * np.cos(theta), r * np.sin(theta)])
        self.pos = np.array(self.pos)
