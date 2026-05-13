import time
from crypto_utils import *

# ==============================================================================
# PROJECT FLAMINGO: Optimized Pollard's Kangaroo Solver
# ==============================================================================

class KangarooSolver:
    """
    Optimized implementation of Pollard's Kangaroo algorithm (Lambda method)
    for solving ECDLP within a known range.
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

        # Precompute structured steps
        avg_step = int(self.width**0.5)
        self.step_scalars = []
        self.step_points_j = []

        seed = 0xFA110
        for i in range(self.step_count):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
            s = (seed % (2 * avg_step)) + 1
            self.step_scalars.append(s)
            self.step_points_j.append(to_jacobian(scalar_mul(s, G)))

    def hash_point(self, x):
        """Maps x-coordinate to a step index."""
        return x % self.step_count

    def is_distinguished(self, x):
        """Checks if a point is distinguished (prefix of zero bits)."""
        return (x >> (256 - self.dp_bits)) == 0

    def solve(self):
        print(f"--- [INITIATING KANGAROO SOLVER] ---")
        print(f"Target X: {self.target[0]:064x}")
        print(f"Range:    [2^{self.min.bit_length()-1}, 2^{self.max.bit_length()-1}]")
        print(f"DP Bits:  {self.dp_bits}")

        tame_points = {}
        tame_dist = 0
        curr_tame_j = to_jacobian(scalar_mul(self.max, G))

        wild_dist = 0
        curr_wild_j = to_jacobian(self.target)

        start_time = time.time()
        for i in range(1, self.max_iter + 1):
            # Batch inversion for speed
            z1, z2 = curr_tame_j[2], curr_wild_j[2]
            if z1 == 0 or z2 == 0: return None

            inv_z1z2 = mod_inv((z1 * z2) % P, P)
            inv_z1 = (inv_z1z2 * z2) % P
            inv_z2 = (inv_z1z2 * z1) % P

            tx = (curr_tame_j[0] * inv_z1 * inv_z1) % P
            wx = (curr_wild_j[0] * inv_z2 * inv_z2) % P

            if self.is_distinguished(tx):
                tame_points[tx] = tame_dist

            if self.is_distinguished(wx):
                if wx in tame_points:
                    print(f"\n[+] COLLISION DETECTED at step {i:,}")
                    stored_tame_d = tame_points[wx]
                    candidate_d = (self.max + stored_tame_d - wild_dist) % N

                    if scalar_mul(candidate_d, G)[0] == self.target[0]:
                        if scalar_mul(candidate_d, G)[1] != self.target[1]:
                            candidate_d = N - candidate_d

                        elapsed = time.time() - start_time
                        print(f"Convergence in {elapsed:.2f}s")
                        return candidate_d

            t_idx = self.hash_point(tx)
            tame_dist += self.step_scalars[t_idx]
            curr_tame_j = jacobian_add(curr_tame_j, self.step_points_j[t_idx])

            w_idx = self.hash_point(wx)
            wild_dist += self.step_scalars[w_idx]
            curr_wild_j = jacobian_add(curr_wild_j, self.step_points_j[w_idx])

            if i % 10000 == 0:
                speed = i / (time.time() - start_time)
                print(f"  Step {i:,} | DP Cache: {len(tame_points)} | Speed: {speed:.0f} it/s", end='\r')

        return None

def main():
    # Puzzle #10 Calibration
    target_d = 514
    target_q = scalar_mul(target_d, G)
    solver = KangarooSolver(target_q, 512, 1023, {'max_iterations': 100000, 'distinguished_bits': 8})
    result = solver.solve()
    if result: print(f"Recovered Scalar: {hex(result)}")

if __name__ == "__main__":
    main()
