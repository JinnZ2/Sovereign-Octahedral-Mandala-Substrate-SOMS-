"""
Holographic smoothness detection.

Instead of trial division by all primes, check coherence level by level.
"""

from collections import defaultdict

def build_holographic_tables(factor_base, levels=None):
    """
    Precompute residue tables for each octahedral level.
    
    Tables map: residue mod product(level) -> possible prime factors
    """
    if levels is None:
        # Group primes into levels of 3
        levels = [factor_base[i:i+3] for i in range(0, len(factor_base), 3)]
    
    level_tables = []
    level_products = []
    
    for level in levels:
        if not level:
            level_tables.append({})
            level_products.append(1)
            continue
            
        prod = 1
        for p in level:
            prod *= p
            
        # Build residue map
        residue_map = defaultdict(list)
        for p in level:
            for residue in range(0, prod, p):
                residue_map[residue].append(p)
                
        level_tables.append(residue_map)
        level_products.append(prod)
        
    return level_tables, level_products


def is_smooth_holographic(n, factor_base, level_tables, level_products):
    """
    Test if n is smooth over factor_base using holographic detection.
    
    Returns:
        (True, exponents) if smooth
        (False, None) otherwise
    """
    if n == 0:
        return False, None
        
    exponents = {}
    remaining = n
    
    # Process each octahedral level
    for level_idx, (level, prod, table) in enumerate(zip(
        [factor_base[i:i+3] for i in range(0, len(factor_base), 3)],
        level_products, level_tables
    )):
        if remaining == 1:
            break
            
        # Get candidate primes from residue
        residue = remaining % prod
        candidates = table.get(residue, [])
        
        # Test candidates
        for p in candidates:
            if p > remaining:
                continue
            cnt = 0
            while remaining % p == 0:
                cnt += 1
                remaining //= p
            if cnt > 0:
                exponents[p] = cnt
                
        # If remaining is a prime in factor base
        if remaining > 1 and remaining <= factor_base[-1]:
            # Binary search or set membership
            if remaining in set(factor_base):
                exponents[remaining] = exponents.get(remaining, 0) + 1
                remaining = 1
                break
                
    if remaining == 1:
        return True, exponents
    return False, None
