
{% macro create_dcm_project(env_config, project_owner_role) %}

-- ======================================================
-- RBAC 
-- ======================================================

{% for env_suffix, cfg in env_config.items() %}

-- ======================================================
-- ENV: {{ env_suffix }}
-- ======================================================

{% set db = cfg.database %}
{% set schemas = cfg.schemas %}
{% set roles = cfg.roles %}

{% for role_type, role_name in roles.items() %}

-- ------------------------------------------------------
-- ROLE: {{ role_type }} ({{ role_name }})
-- ------------------------------------------------------

{% for schema in schemas %}

{% set full_schema = db ~ "." ~ schema %}

-- Base Access
GRANT USAGE ON DATABASE {{ db }} TO ROLE {{ role_name }};
GRANT USAGE ON SCHEMA {{ full_schema }} TO ROLE {{ role_name }};

-- Create Privileges
{% if ROLE_POLICY[role_type].create %}
GRANT CREATE TABLE, CREATE VIEW, CREATE STAGE, CREATE STREAM, CREATE FILE FORMAT, CREATE TASK
ON SCHEMA {{ full_schema }}
TO ROLE {{ role_name }};
{% endif %}

-- Read Access
{% if ROLE_POLICY[role_type].read %}
GRANT SELECT ON ALL TABLES IN SCHEMA {{ full_schema }} TO ROLE {{ role_name }};
GRANT SELECT ON FUTURE TABLES IN SCHEMA {{ full_schema }} TO ROLE {{ role_name }};
{% endif %}

-- Ownership
{% if ROLE_POLICY[role_type].ownership %}
GRANT OWNERSHIP ON ALL TABLES IN SCHEMA {{ full_schema }}
TO ROLE {{ role_name }}
COPY CURRENT GRANTS;

{% for obj in FUTURE_GRANT_OBJECT_TYPES %}
GRANT OWNERSHIP ON FUTURE {{ obj }}
IN SCHEMA {{ full_schema }}
TO ROLE {{ role_name }};
{% endfor %}
{% endif %}

{% endfor %}

{% endfor %}

-- Role hierarchy
{% set role_list = roles.values() | list %}

{% for i in range(role_list | length - 1) %}
GRANT ROLE {{ role_list[i] }} TO ROLE {{ role_list[i+1] }};
{% endfor %}

GRANT ROLE {{ role_list[-1] }} TO ROLE {{ project_owner_role }};

{% endfor %}

{% endmacro %}
