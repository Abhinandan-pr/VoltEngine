# VoltEngine review and enhancement notes

## Scope

`test.py` is the Streamlit entry point (`streamlit run test.py`). It contains the PDF generator, in-memory session-state storage, consumer model, migration logic, daily prepaid billing, monthly settlement, and all eight UI tabs. The package directories contain a second modular billing engine, so the repository currently has two overlapping implementations.

## Initial enhancement made

Added validation to the isolated Streamlit copy for non-finite or negative usage, invalid migration amounts/readings, invalid arrear payments, zero-day recovery periods, unknown migration tariffs, and duplicate migrated consumer IDs. The UI now displays validation errors for migration and payments and prevents negative amounts in payment controls.

## Findings to prioritize

1. **Billing logic is embedded in the UI script.** `test.py` imports Streamlit and mutates `st.session_state` from domain classes. This makes calculations hard to reuse and requires the app context even for basic billing logic. Move engines/models to package modules, leave `test.py` for UI wiring, and keep calculation functions pure.
2. **State is temporary.** Consumers, readings, ledger entries, and settlements exist only in Streamlit session state. They disappear when the session resets and are not shared across users. Persistent storage and transaction boundaries are needed before using this for real accounts.
3. **Tariff calculations need explicit policy review.** Daily ToD adjustments use the minimum slab rate for all peak/off-peak units, then settlement recalculates slab energy charges monthly and reapplies aggregate ToD amounts. Confirm this matches the applicable tariff rules; the code comments and README do not define the policy sufficiently.
4. **Settlement date selection is implicit.** Daily postings can be made for any date in the active billing month, including earlier dates, while month selection is advanced automatically after settlement. The UI should prevent accidental backdated/duplicate postings and provide an auditable close/reopen process.
5. **Financial precision and auditability.** Calculations use binary floats and `datetime.now()` for posting dates/timestamps. Use decimal currency arithmetic, explicit business timezone/date inputs, stable transaction IDs, and immutable ledger records.
6. **Input and tariff validation are incomplete.** Tariff slabs are not checked for positive rates, increasing limits, coverage, or non-overlap; the UI has hard-coded example consumers and migration identity/address values; several operations have no confirmation or undo path.
7. **PDF generation uses temporary files.** `_get_clean_pdf_bytes` writes a temporary file for every invoice. Verify library versions and use a supported in-memory output API where possible; also handle non-ASCII text/fonts consistently.
8. **Run instructions/dependencies are inconsistent.** The README calls the project a FastAPI/Pydantic system, but `test.py` is a standalone Streamlit app and the listed requirements do not include those packages. Document the actual app startup and keep runtime dependencies aligned with code.

## Suggested next steps

1. Confirm the tariff rules for slab and ToD interaction, monthly fixed charge proration, duty, and subsidy.
2. Separate calculation engines from `test.py` and add deterministic examples for each billing scenario.
3. Add persistent storage and a ledger reconciliation/export view.
4. Improve the operator flow: real consumer fields, tariff editing/validation, date controls, duplicate-posting prevention, and clear error states.
