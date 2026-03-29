import json
from typing import Annotated

from fastapi import Body, Depends
from pydantic import Field, StringConstraints, field_validator

from src.schemas.base import BaseSchema

PermissionName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
PluginName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
PermissionKey = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
PermissionsDict = dict[PermissionKey, bool]


class PluginPermissionSchema(BaseSchema):
    id: int
    permissions_id: int
    plugin_name: PluginName
    permissions_dict: PermissionsDict = Field(default_factory=dict)


class PluginPermissionPublicSchema(BaseSchema):
    id: int
    permissions_id: int
    plugin_name: PluginName


class PermissionSchema(BaseSchema):
    id: int
    name: PermissionName
    title_key: str = Field(description="TranslationSmall.key for permission title")
    description_key: str = Field(description="TranslationSmall.key for permission description")
    plugin_permissions: list[PluginPermissionSchema] = Field(default_factory=list)


class RoleSchema(BaseSchema):
    id: int
    name: PermissionName
    title_key: str = Field(description="TranslationSmall.key for role title")
    description_key: str = Field(description="TranslationSmall.key for role description")
    permissions_id: int


class RoleCreateSchema(BaseSchema):
    name: PermissionName
    title_key: str = Field(
        description="TranslationSmall.key for role title",
        examples=["rbac.role.admin.title"],
    )
    description_key: str = Field(
        description="TranslationSmall.key for role description",
        examples=["rbac.role.admin.description"],
    )
    permissions_id: int


class PermissionCreateSchema(BaseSchema):
    name: PermissionName
    title_key: str = Field(
        description="TranslationSmall.key for permission title",
        examples=["rbac.permission.posts.title"],
    )
    description_key: str = Field(
        description="TranslationSmall.key for permission description",
        examples=["rbac.permission.posts.description"],
    )


class PluginPermissionCreateSchema(BaseSchema):
    permissions_id: int
    plugin_name: PluginName
    permissions_dict: PermissionsDict = Field(default_factory=dict)


class PluginPermissionCreateResponseSchema(BaseSchema):
    permission: PluginPermissionSchema
    access_key: str


class PluginPermissionAccessSchema(BaseSchema):
    plugin_permission_id: int
    access_key: str


class PluginPermissionAccessResponseSchema(BaseSchema):
    plugin_permission_id: int
    permissions_dict: PermissionsDict


class RbacBulkCreateSchema(BaseSchema):
    permissions: list[PermissionCreateSchema] = Field(default_factory=list)
    roles: list[RoleCreateSchema] = Field(default_factory=list)
    plugin_permissions: list[PluginPermissionCreateSchema] = Field(default_factory=list)


class RbacBulkCreateResponseSchema(BaseSchema):
    permissions: list[PermissionSchema] = Field(default_factory=list)
    roles: list[RoleSchema] = Field(default_factory=list)
    plugin_permissions: list[PluginPermissionSchema] = Field(default_factory=list)
    plugin_access_keys: dict[int, str] = Field(
        default_factory=dict,
        description="Returned only for newly created plugin permissions: {plugin_permission_id: access_key}",
    )


class RbacQuickPermissionInputSchema(BaseSchema):
    permission_name: PermissionName = Field(examples=["perm.posts"])
    permission_title_key: str = Field(examples=["rbac.permission.posts.title"])
    permission_description_key: str = Field(examples=["rbac.permission.posts.description"])


class RbacQuickRoleInputSchema(BaseSchema):
    role_name: PermissionName = Field(examples=["role.admin"])
    role_title_key: str = Field(examples=["rbac.role.admin.title"])
    role_description_key: str = Field(examples=["rbac.role.admin.description"])


class RbacQuickPluginInputSchema(BaseSchema):
    plugin_name: PluginName = Field(examples=["plugin.blog"])
    plugin_permissions_dict_json: str = Field(
        default="{}",
        description='JSON object with bool values, e.g. {"posts.read": true, "posts.write": false}',
    )

    @field_validator("plugin_permissions_dict_json")
    @classmethod
    def validate_plugin_permissions_dict_json(cls, value: str) -> str:
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(str(exc)) from exc
        if not isinstance(parsed, dict):
            raise ValueError("JSON value must be an object")
        if not all(isinstance(key, str) for key in parsed):
            raise ValueError("JSON object keys must be strings")
        if not all(isinstance(item, bool) for item in parsed.values()):
            raise ValueError("JSON object values must be booleans")
        return value


class RbacQuickCreateSchema(BaseSchema):
    permission: RbacQuickPermissionInputSchema
    role: RbacQuickRoleInputSchema
    plugin: RbacQuickPluginInputSchema


def _permission_create_dep(
    payload: Annotated[PermissionCreateSchema, Body(...)],
) -> PermissionCreateSchema:
    return payload


def _role_create_dep(
    payload: Annotated[RoleCreateSchema, Body(...)],
) -> RoleCreateSchema:
    return payload


def _plugin_permission_create_dep(
    payload: Annotated[PluginPermissionCreateSchema, Body(...)],
) -> PluginPermissionCreateSchema:
    return payload


def _plugin_permission_access_dep(
    payload: Annotated[PluginPermissionAccessSchema, Body(...)],
) -> PluginPermissionAccessSchema:
    return payload


def _rbac_bulk_create_dep(
    payload: Annotated[RbacBulkCreateSchema, Body(...)],
) -> RbacBulkCreateSchema:
    return payload


def _rbac_quick_create_dep(
    payload: Annotated[RbacQuickCreateSchema, Body(...)],
) -> RbacQuickCreateSchema:
    return payload


RoleCreateSchemaDep = Annotated[RoleCreateSchema, Depends(_role_create_dep)]
PermissionCreateSchemaDep = Annotated[
    PermissionCreateSchema,
    Depends(_permission_create_dep),
]
PluginPermissionCreateSchemaDep = Annotated[
    PluginPermissionCreateSchema,
    Depends(_plugin_permission_create_dep),
]
PluginPermissionAccessSchemaDep = Annotated[
    PluginPermissionAccessSchema,
    Depends(_plugin_permission_access_dep),
]
RbacBulkCreateSchemaDep = Annotated[
    RbacBulkCreateSchema,
    Depends(_rbac_bulk_create_dep),
]
RbacQuickCreateSchemaDep = Annotated[
    RbacQuickCreateSchema,
    Depends(_rbac_quick_create_dep),
]
