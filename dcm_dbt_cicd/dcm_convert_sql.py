from snowflake.snowpark.context import get_active_session
from pathlib import Path
import re

session = get_active_session()

# ============================================================
# CONFIG
# ============================================================

DATABASE = "CICD_DEMO_DEV"
SCHEMA = "PROJECTS"
TARGET_DB = "CICD_DEMO{{env_suffix}}"

# ============================================================
# PATH
# ============================================================

def get_repo_root():
    current = Path.cwd()

    if "dcm_automation" in current.parts:
        idx = current.parts.index("dcm_automation")
        return Path(*current.parts[:idx])

    return current

BASE_DIR = get_repo_root()
TARGET_ROOT = BASE_DIR / "dcm_automation" / "sources" / "definitions" / "dcm_convert_test"

print("TARGET ROOT:", TARGET_ROOT)

# ============================================================
# FOLDERS
# ============================================================

FOLDER_MAP = {
    "TABLE": "tables",
    "VIEW": "views",
    "DYNAMIC TABLE": "dynamic_tables",
    "STAGE": "stages",
    "FILE FORMAT": "file_formats",
    "STREAM": "streams",
    "TASK": "tasks"
}

def get_path(obj_type, name):
    folder = FOLDER_MAP.get(obj_type, "others")
    path = TARGET_ROOT / folder
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{name}.sql"

# ============================================================
# HELPERS
# ============================================================

def fq(name):
    return f"{TARGET_DB}.{SCHEMA}.{name}"

def replace_env(text):
    if not text:
        return text
    return re.sub(rf"\b{DATABASE}\b", TARGET_DB, text, flags=re.IGNORECASE)

# ============================================================
# OBJECT LIST
# ============================================================

objects = []
objects += [(r["name"], "TABLE") for r in session.sql(f"SHOW TABLES IN SCHEMA {DATABASE}.{SCHEMA}").collect()]
objects += [(r["name"], "VIEW") for r in session.sql(f"SHOW VIEWS IN SCHEMA {DATABASE}.{SCHEMA}").collect()]
objects += [(r["name"], "DYNAMIC TABLE") for r in session.sql(f"SHOW DYNAMIC TABLES IN SCHEMA {DATABASE}.{SCHEMA}").collect()]
objects += [(r["name"], "STAGE") for r in session.sql(f"SHOW STAGES IN SCHEMA {DATABASE}.{SCHEMA}").collect()]
objects += [(r["name"], "FILE FORMAT") for r in session.sql(f"SHOW FILE FORMATS IN SCHEMA {DATABASE}.{SCHEMA}").collect()]
objects += [(r["name"], "STREAM") for r in session.sql(f"SHOW STREAMS IN SCHEMA {DATABASE}.{SCHEMA}").collect()]
objects += [(r["name"], "TASK") for r in session.sql(f"SHOW TASKS IN SCHEMA {DATABASE}.{SCHEMA}").collect()]

print("TOTAL OBJECTS:", len(objects))

# ============================================================
# TABLE / VIEW / DYNAMIC TABLE
# ============================================================

def ddl_define(obj_type, name):
    ddl = session.sql(
        f"SELECT GET_DDL('{obj_type}', '{DATABASE}.{SCHEMA}.{name}')"
    ).collect()[0][0]

    ddl = replace_env(ddl)

    ddl = re.sub(r"CREATE\s+(OR\s+REPLACE\s+)?", "", ddl, flags=re.IGNORECASE)

    ddl = re.sub(
        r"^(.*?)\(",
        f"DEFINE {obj_type} {fq(name)} (",
        ddl,
        flags=re.IGNORECASE | re.DOTALL
    )

    return ddl

# ============================================================
# STAGE 
# ============================================================

def stage_define(name):
    rows = session.sql(f"SHOW STAGES IN SCHEMA {DATABASE}.{SCHEMA}").collect()

    for r in rows:
        if r["name"] == name:
            out = [f"DEFINE STAGE {fq(name)}"]

            if r.get("directory") or r.get("DIRECTORY"):
                out.append("DIRECTORY = ( ENABLE = TRUE )")

            if r.get("comment"):
                out.append(f"COMMENT = '{r['comment']}'")

            return "\n".join(out)

    return f"-- FAILED STAGE {fq(name)}"

# ============================================================
# FILE FORMAT 
# ============================================================

def file_format_define(name):
    try:
        ddl = session.sql(
            f"SELECT GET_DDL('FILE_FORMAT', '{DATABASE}.{SCHEMA}.{name}')"
        ).collect()[0][0]

        ddl = replace_env(ddl)

        ddl = re.sub(
            r"CREATE\s+(OR\s+REPLACE\s+)?FILE\s+FORMAT\s+[^\s]+",
            f"DEFINE FILE FORMAT {fq(name)}",
            ddl,
            flags=re.IGNORECASE
        )

        return ddl   # MUST return STRING (not list)

    except Exception as e:
        return f"-- FAILED FILE FORMAT {fq(name)}: {e}"

# ============================================================
# TASK
# ============================================================

def task_define(name):
    try:
        ddl = session.sql(
            f"SELECT GET_DDL('TASK', '{DATABASE}.{SCHEMA}.{name}')"
        ).collect()[0][0]

        ddl = replace_env(ddl)

        ddl = re.sub(
            r"CREATE\s+(OR\s+REPLACE\s+)?TASK\s+[^\s]+",
            f"DEFINE TASK {fq(name)}",
            ddl,
            flags=re.IGNORECASE
        )

        return ddl

    except Exception as e:
        return f"-- FAILED TASK {fq(name)}: {e}"

# ============================================================
# STREAM
# ============================================================

def stream_define(name):
    rows = session.sql(f"SHOW STREAMS IN SCHEMA {DATABASE}.{SCHEMA}").collect()

    for r in rows:
        if r["name"] == name:
            return f"""DEFINE STREAM {fq(name)}
AS
SELECT * FROM {r.get('TABLE_NAME','')}
"""
    return f"-- FAILED STREAM {fq(name)}"

# ============================================================
# MAIN
# ============================================================

print("\n================ OUTPUT ================\n")

for name, obj_type in objects:

    try:
        if obj_type in ["TABLE", "VIEW", "DYNAMIC TABLE"]:
            result = ddl_define(obj_type, name)

        elif obj_type == "STAGE":
            result = stage_define(name)

        elif obj_type == "FILE FORMAT":
            result = file_format_define(name)

        elif obj_type == "TASK":
            result = task_define(name)

        elif obj_type == "STREAM":
            result = stream_define(name)

        else:
            result = f"-- UNSUPPORTED {obj_type} {fq(name)}"

        file_path = get_path(obj_type, name)
        file_path.write_text(result, encoding="utf-8")

        print(f"WROTE: {file_path}")

    except Exception as e:
        print(f"FAILED {obj_type} {name}: {e}")

print("\nDONE")