import time
import hashlib
from crypto_utils import *

# ==============================================================================
# PROJECT FLAMINGO: Optimized Pollard's Kangaroo Solver (RK-AMOS)
# ==============================================================================

class KangarooSolver:
    """
    Resonant Kangaroo with Adaptive Mirror-Offset Scaling (RK-AMOS).

    Optimized implementation of Pollard's Kangaroo algorithm for ECDLP range
    challenges on secp256k1. Uses Jacobian coordinates and batch inversion
    to maximize throughput in a Python environment.
    """
    def __init__(self, target_pubkey, min_range, max_range, options=None):
        self.target = target_pubkey
        self.min = min_range
        self.max = max_range
        self.width = max_range - min_range

        opts = options or {}
        self.max_iter = opts.get('max_iterations', 10**6)
        self.dp_bits = opts.get('distinguished_bits', 20)
        self.step_count = 32

        # [OFFSET] Precompute structured steps
        # Average step size should be approximately sqrt(width)
        avg_step = int(self.width**0.5)
        self.step_scalars = []
        self.step_points_j = []

        # Use a deterministic sequence for step sizes
        seed = 0xFA110
        for i in range(self.step_count):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
            s = (seed % (2 * avg_step)) + 1
            self.step_scalars.append(s)
            self.step_points_j.append(to_jacobian(scalar_mul(s, G)))

    def hash_point(self, x):
        """Maps x-coordinate to a step index for the random walk."""
        return x % self.step_count

    def is_distinguished(self, x):
        """Checks if a point is distinguished (prefix of zero bits)."""
        # We check the top bits to stay consistent with the "Scaled" theory
        return (x >> (256 - self.dp_bits)) == 0

    def solve(self):
        print(f"--- [INITIATING RK-AMOS SOLVER] ---")
        print(f"Target X: {self.target[0]:064x}")
        print(f"Range:    [2^{self.min.bit_length()-1}, 2^{self.max.bit_length()-1}]")
        print(f"Width:    {self.width:e}")
        print(f"DP Bits:  {self.dp_bits}")

        # Manifold Cache: Store distinguished points (x -> distance)
        tame_points = {}

        # TAME Kangaroo: Starts at the end of the range
        tame_dist = 0
        curr_tame_j = to_jacobian(scalar_mul(self.max, G))

        # WILD Kangaroo: Starts at the target point Q
        wild_dist = 0
        curr_wild_j = to_jacobian(self.target)

        start_time = time.time()
        checkpoint_time = start_time

        for i in range(1, self.max_iter + 1):
            # [OPTIMIZATION] Batch inversion to get affine x-coordinates for both kangaroos
            z1, z2 = curr_tame_j[2], curr_wild_j[2]

            if z1 == 0 or z2 == 0:
                print("Error: Encountered point at infinity.")
                return None

            try:
                # Combined inversion trick: 1/z1 and 1/z2 with one modular inverse
                # 1. tmp = z1 * z2
                # 2. inv_tmp = 1/tmp
                # 3. inv_z1 = inv_tmp * z2
                # 4. inv_z2 = inv_tmp * z1
                inv_z1z2 = mod_inv((z1 * z2) % P, P)
                inv_z1 = (inv_z1z2 * z2) % P
                inv_z2 = (inv_z1z2 * z1) % P

                # x = X / Z^2
                tx = (curr_tame_j[0] * inv_z1 * inv_z1) % P
                wx = (curr_wild_j[0] * inv_z2 * inv_z2) % P
            except Exception as e:
                print(f"Arithmetic Error: {e}")
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
                    print(f"\n[+] COLLISION DETECTED at step {i:,}")
                    stored_tame_d = tame_points[wx]

                    # [MIRROR] Solve for the scalar d
                    # Q + wild_dist*G = (max + tame_dist)*G
                    # Q = (max + tame_dist - wild_dist)*G
                    candidate_d = (self.max + stored_tame_d - wild_dist) % N

                    # Verification including curve negation symmetry
                    if scalar_mul(candidate_d, G)[0] == self.target[0]:
                        # Check Y coordinate for exact match or negation
                        res_q = scalar_mul(candidate_d, G)
                        if res_q[1] != self.target[1]:
                            candidate_d = N - candidate_d

                        elapsed = time.time() - start_time
                        print(f"Convergence achieved in {elapsed:.2f}s")
                        print(f"Recovered Scalar d: {hex(candidate_d)}")
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

        print("\n[-] Search exhausted iteration limit without convergence.")
        return None

def main():
    # Calibration test on Puzzle #10 (d=514)
    target_d = 514
    target_q = scalar_mul(target_d, G)
    # Using small DP bits for quick convergence in demo
    solver = KangarooSolver(target_q, 512, 1023, {'max_iterations': 100000, 'distinguished_bits': 8})
    solver.solve()

if __name__ == "__main__":
    main()
