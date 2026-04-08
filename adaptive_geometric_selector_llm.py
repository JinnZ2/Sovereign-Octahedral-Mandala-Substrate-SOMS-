#!/usr/bin/env python3
"""
Adaptive Geometric Computation Selector with LLM Interface
===========================================================
- Selects optimal method based on problem characteristics + learned benchmarks.
- Learns from actual runtimes (adaptive scoring).
- Provides LLM harness with natural language ↔ compact grammar translation.
"""

import json
import math
import time
import hashlib
import random
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# ----------------------------------------------------------------------
# Problem types (same as before)
# ----------------------------------------------------------------------
class ProblemType(Enum):
    LINEAR_GF2 = "linear_gf2"
    POLYNOMIAL_ROOT = "polynomial_root"
    FACTORIZATION = "factorization"
    EIGENVALUE = "eigenvalue"
    LATTICE_REDUCTION = "lattice_reduction"
    POLYNOMIAL_SYSTEM = "polynomial_system"
    CONVOLUTION = "convolution"
    DISCRETE_LOG = "discrete_log"
    SPARSE_LINEAR_REAL = "sparse_linear_real"
    UNKNOWN = "unknown"

@dataclass
class Problem:
    type: ProblemType
    data: Any
    size: int
    sparsity: float
    structure: str

# ----------------------------------------------------------------------
# Method definition (with benchmark storage)
# ----------------------------------------------------------------------
@dataclass
class Method:
    name: str
    applicable_types: List[ProblemType]
    complexity: str
    min_size: int
    max_size: int
    max_sparsity: float
    min_sparsity: float
    parallel: bool
    memory_mb_estimate: float
    fallback: bool
    description: str = ""
    # Adaptive fields
    benchmark_runtimes: Dict[str, float] = field(default_factory=dict)  # key: "size_sparsity" -> runtime
    avg_score: float = 0.0   # learned average score

# ----------------------------------------------------------------------
# Method registry (extended)
# ----------------------------------------------------------------------
METHODS = [
    Method("sparse_gf2_gauss", [ProblemType.LINEAR_GF2], "O(R * D^2)", 10, 1_000_000, 0.05, 0.0, False, 200.0, False,
           "Set-based Gaussian elimination over GF(2)"),
    Method("geometric_null_search", [ProblemType.LINEAR_GF2, ProblemType.FACTORIZATION], "O(R * W * 8)", 100, 10_000_000, 0.1, 0.0, False, 100.0, False,
           "Octahedral state cancellation"),
    Method("cube_hashing", [ProblemType.LINEAR_GF2, ProblemType.FACTORIZATION], "O(R)", 27, 10_000_000, 0.2, 0.0, True, 50.0, False,
           "3D cube canonical hashing"),
    Method("geometric_nfs", [ProblemType.FACTORIZATION], "exp(O(sqrt(log N log log N)))", 32, 500, 1.0, 0.0, False, 500.0, False,
           "Geometric Number Field Sieve"),
    Method("tensor_eigen", [ProblemType.EIGENVALUE], "O(n^3)", 2, 1000, 1.0, 0.0, True, 100.0, False,
           "Tensor projection eigenvalues"),
    Method("lll_lattice", [ProblemType.LATTICE_REDUCTION], "O(n^4 log B)", 2, 500, 1.0, 0.0, False, 50.0, False,
           "LLL lattice reduction"),
    Method("groebner_basis", [ProblemType.POLYNOMIAL_SYSTEM], "O(d^O(n))", 2, 10, 1.0, 0.0, False, 200.0, False,
           "Buchberger algorithm"),
    Method("fft_convolution", [ProblemType.CONVOLUTION], "O(n log n)", 64, 10_000_000, 1.0, 0.0, True, 10.0, False,
           "FFT convolution"),
    Method("pollards_rho", [ProblemType.FACTORIZATION, ProblemType.DISCRETE_LOG], "O(sqrt(n))", 16, 100, 1.0, 0.0, False, 1.0, False,
           "Pollard's rho"),
    Method("conjugate_gradient", [ProblemType.SPARSE_LINEAR_REAL], "O(n * k)", 100, 1_000_000, 0.1, 0.0, True, 50.0, False,
           "Conjugate gradient"),
    Method("bloom_cube_3d", [ProblemType.LINEAR_GF2, ProblemType.FACTORIZATION, ProblemType.SPARSE_LINEAR_REAL],
           "O(R * s^3 + s^3)", 1000, 10_000_000, 0.3, 0.0, True, 150.0, False,
           "Probabilistic 3D Bloom cube"),
    Method("sympy_solve", [ProblemType.LINEAR_GF2, ProblemType.POLYNOMIAL_ROOT, ProblemType.EIGENVALUE,
                           ProblemType.POLYNOMIAL_SYSTEM, ProblemType.DISCRETE_LOG],
           "polynomial", 0, 100, 1.0, 0.0, False, 50.0, True,
           "SymPy fallback"),
]

# ----------------------------------------------------------------------
# Benchmark collector & adaptive scorer
# ----------------------------------------------------------------------
class BenchmarkCollector:
    def __init__(self, db_path="benchmark_db.json"):
        self.db_path = db_path
        self.load()

    def load(self):
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                for name, runtimes in data.items():
                    method = next((m for m in METHODS if m.name == name), None)
                    if method:
                        method.benchmark_runtimes = runtimes
        except FileNotFoundError:
            pass

    def save(self):
        data = {m.name: m.benchmark_runtimes for m in METHODS}
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)

    def add_benchmark(self, method_name: str, size: int, sparsity: float, runtime: float):
        method = next((m for m in METHODS if m.name == method_name), None)
        if method:
            key = f"{size}_{sparsity:.3f}"
            method.benchmark_runtimes[key] = runtime
            self.save()

    def estimate_runtime(self, method: Method, size: int, sparsity: float) -> Optional[float]:
        """Find closest benchmark by size and sparsity."""
        best_key = None
        best_dist = float('inf')
        for key, runtime in method.benchmark_runtimes.items():
            s, sp = map(float, key.split('_'))
            dist = abs(s - size) + abs(sp - sparsity)
            if dist < best_dist:
                best_dist = dist
                best_key = key
        if best_key:
            return method.benchmark_runtimes[best_key]
        return None

class AdaptiveScorer:
    def __init__(self, collector: BenchmarkCollector):
        self.collector = collector
        self.alpha = 0.7  # weight for benchmark vs theoretical

    def score(self, method: Method, problem: Problem) -> float:
        # Theoretical score (as before)
        theo = self._theoretical_score(method, problem)
        # Empirical score if available
        emp = self.collector.estimate_runtime(method, problem.size, problem.sparsity)
        if emp is not None:
            # Normalize empirical runtime (lower is better)
            # Assume baseline: size^2 as reference
            baseline = max(1, problem.size ** 2)
            emp_norm = emp / baseline
            return self.alpha * theo + (1 - self.alpha) * emp_norm
        else:
            return theo

    def _theoretical_score(self, method: Method, problem: Problem) -> float:
        # Same scoring as previous version
        if "O(1)" in method.complexity:
            score = 1
        elif "O(log n)" in method.complexity:
            score = math.log2(problem.size + 1)
        elif "O(n)" in method.complexity:
            score = problem.size
        elif "O(n log n)" in method.complexity:
            score = problem.size * math.log2(problem.size + 1)
        elif "O(n^2)" in method.complexity:
            score = problem.size ** 2
        elif "O(n^3)" in method.complexity:
            score = problem.size ** 3
        elif "O(n^4)" in method.complexity:
            score = problem.size ** 4
        elif "exp" in method.complexity:
            score = 1e12
        elif "sqrt(n)" in method.complexity:
            score = math.sqrt(problem.size)
        else:
            score = problem.size ** 2
        # Adjust for sparsity and parallelism
        if problem.sparsity < 0.05 and "sparse" in method.name.lower():
            score *= 0.6
        if method.parallel:
            score *= 0.7
        if method.fallback:
            score *= 2.0
        return score

# ----------------------------------------------------------------------
# Problem analyzer (same)
# ----------------------------------------------------------------------
def analyze_problem(description: str, data: Any = None) -> Problem:
    desc = description.lower()
    if "gf(2)" in desc or "linear over gf2" in desc:
        ptype = ProblemType.LINEAR_GF2
    elif "polynomial root" in desc:
        ptype = ProblemType.POLYNOMIAL_ROOT
    elif "factor" in desc and "integer" in desc:
        ptype = ProblemType.FACTORIZATION
    elif "eigenvalue" in desc:
        ptype = ProblemType.EIGENVALUE
    elif "lattice reduction" in desc:
        ptype = ProblemType.LATTICE_REDUCTION
    elif "groebner" in desc:
        ptype = ProblemType.POLYNOMIAL_SYSTEM
    elif "convolution" in desc:
        ptype = ProblemType.CONVOLUTION
    elif "discrete log" in desc:
        ptype = ProblemType.DISCRETE_LOG
    elif "sparse linear" in desc and "real" in desc:
        ptype = ProblemType.SPARSE_LINEAR_REAL
    else:
        ptype = ProblemType.UNKNOWN
    # size estimation (simplified)
    size = 0
    sparsity = 0.0
    if data is not None:
        if isinstance(data, (list, tuple)):
            size = len(data)
            sparsity = 0.5  # placeholder
        elif isinstance(data, int):
            size = data.bit_length()
            sparsity = 1.0
    return Problem(type=ptype, data=data, size=size, sparsity=sparsity, structure="unknown")

# ----------------------------------------------------------------------
# LLM Interface Harness & Translator (Compact Grammar v2)
# ----------------------------------------------------------------------
class CompactGrammarV2:
    @staticmethod
    def parse_command(line: str) -> Tuple[str, dict]:
        line = line.strip()
        if line.startswith("QUERY"):
            parts = line.split()
            if len(parts) == 2 and (parts[1] == "all" or parts[1].isalnum()):
                return ("QUERY", {"target": parts[1]})
        elif line.startswith("ACT"):
            parts = line.split()
            if len(parts) == 3:
                return ("ACT", {"method": parts[1], "problem_desc": parts[2]})
        elif line == "RESET":
            return ("RESET", {})
        elif line.startswith("BENCH"):
            parts = line.split()
            if len(parts) == 4:
                return ("BENCH", {"method": parts[1], "size": int(parts[2]), "sparsity": float(parts[3])})
        elif line == "HELP":
            return ("HELP", {})
        return ("ERROR", {"code": "4", "message": "syntax error"})

    @staticmethod
    def format_result(method: str, result: Any, runtime: float) -> str:
        return f"RES {method} {runtime:.3f}s"

    @staticmethod
    def format_error(code: str, msg: str) -> str:
        return f"ERR {code} {msg}"

class LLMInterfaceHarness:
    def __init__(self, selector, scorer, collector):
        self.selector = selector
        self.scorer = scorer
        self.collector = collector
        self.grammar = CompactGrammarV2()

    def process_nl(self, nl_query: str, data: Any = None) -> str:
        """Convert natural language to compact command, execute, return compact result."""
        # Simple NL to command translation (keyword based)
        cmd = self._nl_to_command(nl_query, data)
        if cmd.startswith("ERROR"):
            return cmd
        return self.process_command(cmd, data)

    def _nl_to_command(self, nl: str, data: Any = None) -> str:
        nl = nl.lower()
        if "select" in nl or "choose" in nl or "solve" in nl:
            # Extract problem description (remainder after keyword)
            # For simplicity, use entire nl as problem description
            return f"ACT solve {nl}"
        elif "benchmark" in nl:
            # parse "benchmark method_name size sparsity"
            parts = nl.split()
            for m in METHODS:
                if m.name in nl:
                    method = m.name
                    # find size and sparsity
                    size = 100
                    sparsity = 0.1
                    for p in parts:
                        if p.isdigit():
                            size = int(p)
                        elif '.' in p and p.replace('.','').isdigit():
                            sparsity = float(p)
                    return f"BENCH {method} {size} {sparsity}"
        elif "help" in nl:
            return "HELP"
        elif "reset" in nl:
            return "RESET"
        return "ERROR 4 unknown natural language"

    def process_command(self, cmd: str, data: Any = None) -> str:
        cmd_type, args = self.grammar.parse_command(cmd)
        if cmd_type == "QUERY":
            # Return info about available methods
            return "METHODS: " + ", ".join(m.name for m in METHODS)
        elif cmd_type == "ACT":
            method_name = args["method"]
            problem_desc = args["problem_desc"]
            problem = analyze_problem(problem_desc, data)
            # Find method
            method = next((m for m in METHODS if m.name == method_name), None)
            if not method:
                return self.grammar.format_error("3", f"unknown method {method_name}")
            # Run method (stub)
            t0 = time.time()
            result = self._run_method_stub(method, problem)
            runtime = time.time() - t0
            # Optionally record benchmark
            if result.get("success", False):
                self.collector.add_benchmark(method.name, problem.size, problem.sparsity, runtime)
            return self.grammar.format_result(method.name, result, runtime)
        elif cmd_type == "BENCH":
            method_name = args["method"]
            size = args["size"]
            sparsity = args["sparsity"]
            # Run benchmark (stub)
            method = next((m for m in METHODS if m.name == method_name), None)
            if method:
                t0 = time.time()
                # Simulate runtime based on complexity
                # In real usage, run actual method on synthetic problem
                runtime = self._simulate_runtime(method, size, sparsity)
                self.collector.add_benchmark(method_name, size, sparsity, runtime)
                return f"BENCH DONE {method_name} size={size} sparsity={sparsity} time={runtime:.3f}s"
            else:
                return self.grammar.format_error("3", f"unknown method {method_name}")
        elif cmd_type == "RESET":
            self.collector.load()  # reload from disk (or clear)
            return "RESET OK"
        elif cmd_type == "HELP":
            return self.grammar.HELP_TEXT
        else:
            return self.grammar.format_error("4", "unknown command")

    def _run_method_stub(self, method: Method, problem: Problem) -> dict:
        """Stub – replace with actual method call."""
        # Simulate runtime based on complexity
        runtime = self._simulate_runtime(method, problem.size, problem.sparsity)
        time.sleep(0.1)  # simulate work
        return {"success": True, "runtime": runtime, "result": f"simulated_{method.name}"}

    def _simulate_runtime(self, method: Method, size: int, sparsity: float) -> float:
        # Use theoretical complexity to generate plausible runtime
        if "O(1)" in method.complexity:
            base = 0.001
        elif "O(log n)" in method.complexity:
            base = math.log2(size+1) * 0.0001
        elif "O(n)" in method.complexity:
            base = size * 1e-6
        elif "O(n log n)" in method.complexity:
            base = size * math.log2(size+1) * 1e-6
        elif "O(n^2)" in method.complexity:
            base = (size ** 2) * 1e-8
        elif "O(n^3)" in method.complexity:
            base = (size ** 3) * 1e-10
        elif "exp" in method.complexity:
            base = math.exp(size/100) * 1e-6
        elif "sqrt(n)" in method.complexity:
            base = math.sqrt(size) * 1e-5
        else:
            base = size * 1e-6
        # Add noise
        return base * (0.5 + random.random())

# ----------------------------------------------------------------------
# Adaptive Selector (main API)
# ----------------------------------------------------------------------
class AdaptiveGeometricSelector:
    def __init__(self):
        self.collector = BenchmarkCollector()
        self.scorer = AdaptiveScorer(self.collector)
        self.llm = LLMInterfaceHarness(self, self.scorer, self.collector)

    def select_method(self, problem: Problem) -> Tuple[Method, float]:
        best_method = None
        best_score = float('inf')
        for method in METHODS:
            if problem.type not in method.applicable_types:
                continue
            if problem.size < method.min_size or problem.size > method.max_size:
                continue
            if problem.sparsity < method.min_sparsity or problem.sparsity > method.max_sparsity:
                continue
            score = self.scorer.score(method, problem)
            if score < best_score:
                best_score = score
                best_method = method
        if best_method is None:
            best_method = next(m for m in METHODS if m.fallback)
        return best_method, best_score

    def solve(self, description: str, data: Any = None) -> Any:
        problem = analyze_problem(description, data)
        method, _ = self.select_method(problem)
        # In real usage, call actual method implementation
        print(f"Selected {method.name} for {description}")
        # Stub return
        return {"method": method.name, "result": "simulated"}

    def interact_llm(self, nl_query: str, data: Any = None) -> str:
        return self.llm.process_nl(nl_query, data)

# ----------------------------------------------------------------------
# Demo
# ----------------------------------------------------------------------
if __name__ == "__main__":
    selector = AdaptiveGeometricSelector()

    # Example 1: Natural language query
    print("=== LLM Interface ===")
    response = selector.interact_llm("Solve linear system over GF(2) with 1000 variables")
    print(response)

    # Example 2: Benchmark a method
    response = selector.interact_llm("benchmark geometric_null_search size 5000 sparsity 0.02")
    print(response)

    # Example 3: Query methods
    response = selector.interact_llm("list methods")
    print(response)

    # Example 4: Solve a factorization problem
    response = selector.interact_llm("factor integer 123456789012345678901234567890")
    print(response)

    # Show adaptive scoring after benchmark
    print("\n=== Adaptive Scoring Demo ===")
    prob = Problem(ProblemType.LINEAR_GF2, None, size=5000, sparsity=0.02, structure="sparse")
    method, score = selector.select_method(prob)
    print(f"Selected {method.name} with score {score:.2e}")
