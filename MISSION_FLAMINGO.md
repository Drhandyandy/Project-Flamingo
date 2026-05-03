# 🦩 Technical Whitepaper: Project Flamingo

**Title:** Optimized Pollard's Kangaroo for secp256k1 Range Challenges.
**Version:** 3.2 (RK-AMOS Optimization)

## I. ABSTRACT
Project Flamingo implements a high-performance ECDLP solver specifically designed for Bitcoin puzzle challenges. By utilizing the **Resonant Kangaroo with Adaptive Mirror-Offset Scaling (RK-AMOS)** algorithm, this engine optimizes search efficiency within bounded ranges on the secp256k1 elliptic curve.

## II. METHODOLOGY

The RK-AMOS engine builds upon Pollard's Kangaroo algorithm with several key optimizations for the Python execution environment.

### 2.1 Mirror Optimization (Curve Negation)
The algorithm exploits the point negation symmetry $P = (x, y) \implies -P = (x, -y)$. By tracking only $x$-coordinates in the collision map, we effectively double the collision probability without increasing memory overhead.

### 2.2 Jacobian Projective Coordinates
To maximize throughput, all elliptic curve point additions are performed in **Jacobian Projective Coordinates** $(X:Y:Z)$. This mathematical representation allows point additions to be computed using only modular multiplications and subtractions, delaying the computationally expensive modular inversion until a distinguished point is encountered.

### 2.3 Batch Inversion
The solver further optimizes the inner loop by performing **batch modular inversions** for both the tame and wild kangaroos. This technique allows multiple coordinates to be converted from projective back to affine space using only a single modular inverse operation, significantly reducing the bottleneck of modular arithmetic.

### 2.4 Adaptive Scaling (Distinguished Points)
The search manifold is managed via a distinguished point filter. Only coordinates satisfying a specific bit-mask are stored in the manifold cache, allowing for a tunable trade-off between memory consumption and collision detection frequency.

## III. IMPLEMENTATION STATUS

The current implementation provides a robust foundation for distributed solving. The engine has been validated against low-bit targets (e.g., Puzzle #10) and is ready for deployment against higher-entropy ranges.

| Challenge Range | Status | Methodology |
| :--- | :--- | :--- |
| **1 - 66** | Solved (Historical) | Community Distributed Computing |
| **67 - 160** | Unsolved | RK-AMOS Engine / Swarm Search |

## IV. CONCLUSION
Project Flamingo demonstrates that secp256k1 range challenges can be approached with high efficiency by leveraging optimized group law primitives and advanced collision detection algorithms. The RK-AMOS engine provides a professional-grade framework for cryptographic research and asset recovery.

**Just. Deriving. It. ⚡️✔️**
