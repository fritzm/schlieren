"""The BOM's schema and row checks, shared by the workbook builder, the reconciler, and the tests.

bom/bom.csv is authoritative. These are the invariants any set of BOM rows must meet before it may replace
it; the reconciler runs them on an edited workbook before writing anything.
"""

HEADER = [
    "ID",
    "Subsystem",
    "Qty",
    "Item",
    "Purpose",
    "Vendor",
    "SKU",
    "Pkg Size",
    "Purchase Unit",
    "Procurement state",
    "Source section",
    "Notes",
]
ID_COLUMN = "ID"
SUBSYSTEM_COLUMN = "Subsystem"
STATE_COLUMN = "Procurement state"
NUMERIC_COLUMNS = {"Qty", "Pkg Size"}

# Procurement states, in Summary display order.
STATES = ("In hand", "On order", "To procure", "Specified", "CAD ready", "CAD open")

SUBSYSTEMS = (
    "Tabletop frame",
    "Optical supports",
    "Light source",
    "Source slit",
    "Carriages",
    "Cassettes",
    "Imager",
    "Mirror cell",
    "Shop supplies",
)


def _is_number(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return False
    return True


def check_rows(header: list[str], rows: list[list[str]]) -> list[str]:
    """Problems with a BOM as header and rows of text, as a list of messages; empty when it is sound."""
    if header != HEADER:
        return [f"The columns are {header}, not {HEADER}"]
    problems = []
    column = {name: i for i, name in enumerate(header)}
    seen = set()
    prefixes: dict[str, set[str]] = {}
    for n, row in enumerate(rows, start=2):  # Row 1 is the header, as in the spreadsheet.
        if len(row) != len(header):
            problems.append(f"Row {n} has {len(row)} fields, not {len(header)}")
            continue
        row_id = row[column[ID_COLUMN]]
        where = f"Row {n} ({row_id or 'no ID'})"
        if not row_id:
            problems.append(f"Row {n} has no ID")
        elif row_id in seen:
            problems.append(f"{where}: the ID is used more than once")
        seen.add(row_id)
        state = row[column[STATE_COLUMN]]
        if state not in STATES:
            problems.append(f"{where}: procurement state {state!r} is not one of {', '.join(STATES)}")
        subsystem = row[column[SUBSYSTEM_COLUMN]]
        if subsystem not in SUBSYSTEMS:
            problems.append(f"{where}: subsystem {subsystem!r} is not a known subsystem")
        for name in NUMERIC_COLUMNS:
            value = row[column[name]]
            if value != "" and not _is_number(value):
                problems.append(f"{where}: {name} {value!r} is not a number")
        if row_id and "-" in row_id:
            prefixes.setdefault(subsystem, set()).add(row_id.split("-")[0])
    problems += [
        f"Subsystem {subsystem!r} has more than one ID prefix: {', '.join(sorted(found))}"
        for subsystem, found in prefixes.items()
        if len(found) > 1
    ]
    return problems
