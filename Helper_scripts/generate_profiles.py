
import yaml
import os


def load_manifest(manifest_path):
    with open(manifest_path, 'r') as f:
        return yaml.safe_load(f)


def build_profiles(manifest, profile_name="dcm_dbt_cicd", default_target="DCM_DEV"):
    templating = manifest.get("templating", {})
    defaults = templating.get("defaults", {})
    configurations = templating.get("configurations", {})
    targets = manifest.get("targets", {})

    outputs = {}
    for target_name, target_config in targets.items():
        config_key = target_config.get("templating_config")
        env_config = configurations.get(config_key, {})

        output = {
            "type": "snowflake",
            "account": target_config.get("account_identifier"),
            "user": os.environ.get("SNOWFLAKE_USER", defaults.get("user", "DISHA_RANI")),
            "role": target_config.get("project_owner", defaults.get("project_owner_role")),
            "database": env_config.get("database"),
            "warehouse": env_config.get("warehouse", defaults.get("warehouse")),
            "schema": "PATIENTS_SILVER",
            "threads": 4,
            "client_session_keep_alive": False,
        }
        outputs[target_name] = output

    profiles = {
        profile_name: {
            "target": default_target,
            "outputs": outputs,
        }
    }
    return profiles


def main():
    workspace_root = os.path.abspath(os.path.join(os.getcwd(), ".."))
    manifest_path = os.path.join(workspace_root, "dcm_automation", "manifest.yml")
    output_path = os.path.join(workspace_root, "dcm_automation", "sources", "dbt", "dcm_dbt_cicd", "profiles.yml")

    manifest = load_manifest(manifest_path)
    default_target = manifest.get("default_target", "DCM_DEV")
    profiles = build_profiles(manifest, default_target=default_target)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(profiles, f, default_flow_style=False, sort_keys=False)

    print(f"Generated profiles.yml at: {output_path}")
    print(yaml.dump(profiles, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
