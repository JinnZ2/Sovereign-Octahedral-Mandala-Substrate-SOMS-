"""
Prime generation and octahedral mapping.

Primes are grouped into octahedra of 3. Each octahedron has 3 vertices,
and each vertex corresponds to a prime. The exponent parity for each prime
lives on its vertex.
"""

def generate_primes(limit):
    """
    Generate primes up to limit.
    Simple sieve, works on any hardware.
    """
    if limit < 2:
        return []
    
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, limit+1, i):
                sieve[j] = False
                
    return [i for i, is_prime in enumerate(sieve) if is_prime]


def octahedral_mapping(primes):
    """
    Map primes to octahedral coordinates.
    
    Returns:
        prime_to_octa: dict {prime: octahedron_index}
        prime_to_vertex: dict {prime: vertex_index (0,1,2)}
        octa_to_primes: list of lists [[p0,p1,p2], ...]
    """
    prime_to_octa = {}
    prime_to_vertex = {}
    octa_to_primes = []
    
    for i, p in enumerate(primes):
        octa_idx = i // 3
        vertex_idx = i % 3
        prime_to_octa[p] = octa_idx
        prime_to_vertex[p] = vertex_idx
        
        if vertex_idx == 0:
            octa_to_primes.append([p, None, None])
        else:
            octa_to_primes[octa_idx][vertex_idx] = p
            
    return prime_to_octa, prime_to_vertex, octa_to_primes
