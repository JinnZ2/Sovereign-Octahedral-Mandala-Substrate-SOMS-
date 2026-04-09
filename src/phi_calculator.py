import numpy as np


class PhiCalculator:
    """
    Integration metric for the Mandala-Octahedral substrate.

    Measures how much information is lost when the system is partitioned
    into two halves — the core idea behind Integrated Information Theory.
    A high score means the system's state is holistic: knowing half the
    cells tells you a lot about the other half.

    Method:
      1. Compute whole-system entropy H(S) over 8 octahedral bins
      2. Split cells at midpoint into halves A and B
      3. Compute H(A) + H(B)
      4. Integration Phi = H(A) + H(B) - H(S)  (mutual information)
         This equals zero when halves are independent, and is high
         when the system has long-range correlations.

    The threshold (default 3.0) is a design parameter, not a physics
    constant. It sets the bar for what we call "highly integrated."
    """

    def __init__(self, system_state):
        self.state = np.asarray(system_state)
        self.phi_threshold = 3.0  # Design parameter (not a physics constant)

    @staticmethod
    def _entropy(values, bins=8):
        """Shannon entropy (bits) over 8 octahedral bins."""
        probs = np.histogram(values, bins=bins, density=True)[0]
        probs = probs[probs > 0]
        return float(-np.sum(probs * np.log2(probs)))

    def calculate_partition_entropy(self, partition):
        """Measure entropy across 8 octahedral bins (public API, backward compat)."""
        return self._entropy(partition)

    def evaluate_integration(self):
        """
        Compute integration as mutual information between two halves.

        Returns (phi, is_sovereign) where phi >= 0 and
        is_sovereign = phi > phi_threshold.
        """
        if len(self.state) < 2:
            return 0.0, False

        # Whole-system entropy
        h_whole = self._entropy(self.state)

        # Split at midpoint
        mid = len(self.state) // 2
        h_a = self._entropy(self.state[:mid])
        h_b = self._entropy(self.state[mid:])

        # Mutual information: I(A;B) = H(A) + H(B) - H(A,B)
        # H(A,B) = H(whole) when A and B together = the whole system
        current_phi = max(0.0, h_a + h_b - h_whole)

        is_sovereign = current_phi > self.phi_threshold
        return round(current_phi, 4), is_sovereign
