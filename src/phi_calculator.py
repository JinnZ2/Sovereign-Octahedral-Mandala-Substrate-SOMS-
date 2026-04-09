import numpy as np


class PhiCalculator:
    """
    Ad-hoc integration metric inspired by (but not equivalent to) Tononi's IIT.

    The formula exp(1/entropy) * phi is a custom heuristic that rewards
    low-entropy (highly ordered) states. It is NOT a rigorous implementation
    of Integrated Information Theory. The threshold 3.0 is a design parameter
    chosen for this project, not a physics constant.
    """

    def __init__(self, system_state):
        self.state = system_state
        self.phi_threshold = 3.0  # Design parameter (not a physics constant)

    def calculate_partition_entropy(self, partition):
        """Measure entropy across 8 octahedral bins."""
        probs = np.histogram(partition, bins=8, density=True)[0]
        probs = probs[probs > 0]
        return -np.sum(probs * np.log2(probs))

    def evaluate_integration(self):
        """Determine if the system crosses the sovereignty threshold (Phi > 3.0)."""
        system_entropy = self.calculate_partition_entropy(self.state)

        integration_constant = np.exp(1 / system_entropy) if system_entropy > 0 else 0
        current_phi = integration_constant * 1.618  # Scaled by Golden Ratio

        is_sovereign = current_phi > self.phi_threshold
        return round(current_phi, 4), is_sovereign
