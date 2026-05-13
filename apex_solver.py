import time
import hashlib
from crypto_utils import *

# ==============================================================================
# 🦩 PROJECT FLAMINGO: RK-AMOS TOPOLOGICAL ENGINE (V3.2) 🦩
# ==============================================================================

class ResonantKangarooAMOS:
    """
    Resonant Kangaroo with Adaptive Mirror-Offset Scaling (RK-AMOS).

    A high-performance topological manifold reconstruction engine for solving
    the ECDLP within bounded bit-depth sectors. Optimized using Jacobian
    projective coordinates and batch modular inversion.
    """
    def __init__(self, target_pubkey, min_range, max_range, options=None):
        self.target = target_pubkey
        self.min = min_range
        self.max = max_range
        self.width = max_range - min_range

        opts = options or {}
        self.max_iter = opts.get('max_iterations', 10**6)
        self.dp_bits = opts.get('distinguished_bits', 20)
        self.step_count = 64

        # [OFFSET] Structured Step Table (Linear Congruential Mapping)
        # Prevents Pollard clustering via deterministic modular spacing.
        avg_step = int(self.width**0.5)
        self.step_scalars = []
        self.step_points_j = []

        seed = 0xFA110
        for i in range(self.step_count):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
            s = (seed % (max(1, 2 * avg_step))) + 1
            self.step_scalars.append(s)
            # Use Jacobian for addition speed
            self.step_points_j.append(to_jacobian(scalar_mul(s, G)))

    def hash_point(self, x):
        """Map x-coordinate to a step index using a fast folding hash."""
        return (x ^ (x >> 32) ^ (x >> 64)) % self.step_count

    def is_distinguished(self, x):
        """Check if top bits of x are zero (Adaptive Scaling)."""
        return (x >> (256 - self.dp_bits)) == 0

    def solve(self):
        print(f"--- [INITIATING RK-AMOS LATTICE COLLAPSE] ---")
        print(f"Target X: {self.target[0]:064x}")
        print(f"Range:    [2^{self.min.bit_length()-1}, 2^{self.max.bit_length()-1}]")
        print(f"DP Bits:  {self.dp_bits} | Steps: {self.step_count}")

        # Manifold Cache: Store distinguished points (x -> distance)
        tame_points = {}

        # TAME WALK: Starts at the end of the range (Max Boundary)
        tame_dist = 0
        curr_tame_j = to_jacobian(scalar_mul(self.max, G))

        # WILD WALK: Starts at the target point Q (Fragment Source)
        wild_dist = 0
        curr_wild_j = to_jacobian(self.target)

        start_time = time.time()

        for i in range(1, self.max_iter + 1):
            # [OPTIMIZATION] Batch inversion for dual-kangaroo throughput
            z1, z2 = curr_tame_j[2], curr_wild_j[2]

            if z1 == 0 or z2 == 0:
                print("Error: Encountered point at infinity.")
                return None

            try:
                inv_z1z2 = mod_inv((z1 * z2) % P, P)
                inv_z1 = (inv_z1z2 * z2) % P
                inv_z2 = (inv_z1z2 * z1) % P

                # x = X / Z^2
                tx = (curr_tame_j[0] * inv_z1 * inv_z1) % P
                wx = (curr_wild_j[0] * inv_z2 * inv_z2) % P
            except Exception as e:
                print(f"Topological Error: {e}")
                return None

            # 1. Tame Step
            if self.is_distinguished(tx):
                tame_points[tx] = tame_dist

            t_idx = self.hash_point(tx)
            tame_dist += self.step_scalars[t_idx]
            curr_tame_j = jacobian_add(curr_tame_j, self.step_points_j[t_idx])

            # 2. Wild Step
            if self.is_distinguished(wx):
                if wx in tame_points:
                    print(f"\n✅ [ZENITH PHASE-LOCK DETECTED]")
                    stored_tame_d = tame_points[wx]

                    # [MIRROR] Solve for the scalar d
                    candidate_d = (self.max + stored_tame_d - wild_dist) % N

                    # Verification including curve negation symmetry
                    if scalar_mul(candidate_d, G)[0] == self.target[0]:
                        res_q = scalar_mul(candidate_d, G)
                        if res_q[1] != self.target[1]:
                            candidate_d = N - candidate_d

                        elapsed = time.time() - start_time
                        print(f"Convergence achieved in {elapsed:.2f}s at step {i:,}")
                        print(f"Scalar d: {hex(candidate_d)}")
                        return candidate_d

            w_idx = self.hash_point(wx)
            wild_dist += self.step_scalars[w_idx]
            curr_wild_j = jacobian_add(curr_wild_j, self.step_points_j[w_idx])

            # Progress Reporting
            if i % 10000 == 0:
                now = time.time()
                elapsed = now - start_time
                speed = i / elapsed
                print(f"  Step {i:,} | DP Cache: {len(tame_points)} | Speed: {speed:.0f} it/s", end='\r')

        print("\n[-] Manifold remains rigid. Increase iteration depth.")
        return None

def main():
    # Calibration test on Puzzle #10 (d=514)
    target_d = 514
    target_q = scalar_mul(target_d, G)
    solver = ResonantKangarooAMOS(target_q, 512, 1023, {'max_iterations': 100000, 'distinguished_bits': 8})
    solver.solve()

if __name__ == "__main__":
    main()
