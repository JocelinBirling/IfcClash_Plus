"""The engine backends (SPEC_OptimisationInCPP, "Côté Python").

    orchestrator.compute_rule -> backends.python_backend (reference)
                              -> backends.cpp_backend    (libifcclash_engine)

The backend of each rule is chosen from the "implementation" field of the
catalogue (registry.py): a rule moves to C++ once its parity is green,
nothing else changes. The C++ module _ifcclash_engine is built by
engine/CMakeLists.txt into this folder; without it every rule runs on the
Python backend.
"""
