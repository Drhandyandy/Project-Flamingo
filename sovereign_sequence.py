import math
from crypto_utils import N

def a_n(n):
    """
    OEIS A369920: Cubic progression for volumetric manifold expansion.
    Formula: a(n) = (2*n + 1) * (5*n**2 + 5*n + 3) // 3
    """
    return (2*n + 1) * (5*n**2 + 5*n + 3) // 3

def analyze_sovereign_sequence():
    print("--- [OEIS A369920: VOLUMETRIC MANIFOLD ANALYSIS] ---")
    print("Mapping the first 65 shells of the Sovereign Matrix:\n")

    pulse_656 = pow(2, 656, N)

    for n in range(65):
        val = a_n(n)
        drift = abs(val - (pulse_656 % val)) if val > 0 else 0
        print(f"Shell {n:02}: {val:10d} | Alignment Drift: {drift:10d}")

    print("\n[!] GEOMETRIC OBSERVATION:")
    print("Shell 5 = 561 (Resonance Node)")
    print("Shell 6 = 923 (Search Boundary)")
    print("Target 656 lies within the (561, 923) gap (26.1% Depth).")

if __name__ == "__main__":
    analyze_sovereign_sequence()
