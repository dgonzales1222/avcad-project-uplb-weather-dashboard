"""NWS heat index + PAGASA danger-band classification — the project's core math.

Implemented and tested in Phase 3. See docs/PROJECT_CONTEXT.md for the exact formula
(simple form + Rothfusz regression + both adjustments) and the PAGASA bands.

To implement:
    heat_index_f(temp_f, rh)   # NWS formula, °F
    heat_index_c(temp_c, rh)   # °C wrapper
    classify(hi_c)             # Caution / Extreme Caution / Danger / Extreme Danger
"""
