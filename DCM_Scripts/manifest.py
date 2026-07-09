import yaml
from pathlib import Path


# ============================================================
# Disable YAML anchors/aliases
# ============================================================

class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


# ============================================================
# CONFIGURATION
# ============================================================

MANIFEST_VERSION = 2
PROJECT_TYPE = "DCM_PROJECT"
DEFAULT_TARGET = "DCM_DEV"

ACCOUNT_IDENTIFIER = "KIPI-KIPI_PRIMARY"

WAREHOUSE = "DISHA_RANI_WH"
WH_SIZE = "XSMALL"

DCM_SCHEMA = "UTILITIES"
BASE_DATABASE = "CICD_AUTOMATION"

ENVIRONMENTS = [
    "DEV",
    "QA",
    "PROD",
]

SCHEMAS = [
    "HOSPITALS",
    "PATIENTS",
    "UTILITIES",
]

# First role is used as project_owner
ROLES = {
    "DEV": [
        "GITHUB_CICD_DEMO_ROLE",
        # "DEVELOPER_ROLE",
    ],
    "QA": [
        "GITHUB_CICD_DEMO_ROLE",
        # "QA_TESTER_ROLE",
    ],
    "PROD": [
        "GITHUB_CICD_DEMO_ROLE",
        # "PROD_DEPLOY_ROLE",
    ],
}

DEFAULT_ROLES = [
    "GITHUB_CICD_DEMO_ROLE",
]


# ============================================================
# PATH RESOLUTION
# ============================================================

from pathlib import Path

def get_manifest_path():
    # Use __file__ when available, otherwise fall back to cwd()
    try:
        start = Path(__file__).resolve().parent
    except NameError:
        start = Path.cwd()

    for directory in [start] + list(start.parents):
        manifest = directory / "dcm_automation" / "manifest.yml"
        if manifest.exists():
            return manifest

    raise RuntimeError(
        "Could not locate dcm_automation/manifest.yml. "
        "Run the script from within the project or specify the project root."
    )


# ============================================================
# BUILD MANIFEST
# ============================================================

def build_manifest():
    targets = {}
    configurations = {}

    for env in ENVIRONMENTS:
        database = f"{BASE_DATABASE}_{env}"
        project_name = f"{database}.{DCM_SCHEMA}.DCM_AUTOMATION"
        target_name = f"DCM_{env}"

        env_roles = ROLES.get(env, DEFAULT_ROLES)
        project_owner = env_roles[0]

        targets[target_name] = {
            "account_identifier": ACCOUNT_IDENTIFIER,
            "project_name": project_name,
            "project_owner": project_owner,
            "templating_config": env,
        }

        configurations[env] = {
            "env_suffix": f"_{env}",
            "database": database,
            "schemas": SCHEMAS,
            "dcm_schema": DCM_SCHEMA,
            "project_name": project_name,
            "project_owner": project_owner,
            "roles": env_roles,
        }

    return {
        "manifest_version": MANIFEST_VERSION,
        "type": PROJECT_TYPE,
        "default_target": DEFAULT_TARGET,
        "targets": targets,
        "templating": {
            "defaults": {
                "project_owner_role": DEFAULT_ROLES[0],
                "warehouse": WAREHOUSE,
                "wh_size": WH_SIZE,
                "dcm_schema": DCM_SCHEMA,
            },
            "configurations": configurations,
        },
    }


# ============================================================
# WRITE MANIFEST
# ============================================================

def write_manifest(manifest, manifest_path):
    with manifest_path.open("w") as file:
        yaml.dump(
            manifest,
            file,
            Dumper=NoAliasDumper,
            default_flow_style=False,
            sort_keys=False,
        )


# ============================================================
# MAIN
# ============================================================

def main():
    manifest_path = get_manifest_path()

    manifest = build_manifest()

    write_manifest(manifest, manifest_path)

    print("=" * 60)
    print("Manifest generated successfully.")
    print(f"Location: {manifest_path}")
    print("=" * 60)

    print(
        yaml.dump(
            manifest,
            Dumper=NoAliasDumper,
            default_flow_style=False,
            sort_keys=False,
        )
    )


if __name__ == "__main__":
    main()