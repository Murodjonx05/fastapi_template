from fastapi import APIRouter, HTTPException, Request

from src.core.limiter import limit_minute
from src.crud.rbac import (
    InvalidAccessKeyError,
    RbacAlreadyExistsError,
    RbacNotFoundError,
    RbacValidationError,
    create_permission,
    create_plugin_permission,
    create_role,
    get_permission,
    get_plugin_permission,
    get_plugin_permissions_dict_by_access_key,
    get_role,
)
from src.database import SessionDep
from src.schemas.rbac import (
    PermissionCreateSchemaDep,
    PermissionSchema,
    PluginPermissionAccessResponseSchema,
    PluginPermissionAccessSchemaDep,
    PluginPermissionCreateResponseSchema,
    PluginPermissionCreateSchemaDep,
    PluginPermissionPublicSchema,
    PluginPermissionSchema,
    RoleCreateSchemaDep,
    RoleSchema,
)
from src.utils.logging import get_logger
from src.utils.rate_limiter import limiter

rbac_logger = get_logger("rbac_api_endpoint")
rbac_router = APIRouter()
rbac_permissions_router = APIRouter(prefix="/permissions", tags=["rbac-permissions"])
rbac_roles_router = APIRouter(prefix="/roles", tags=["rbac-roles"])
rbac_plugin_permissions_router = APIRouter(prefix="/plugin-permissions", tags=["rbac-plugin-permissions"])


def _to_http_error(exc: Exception, action: str) -> HTTPException:
    if isinstance(exc, RbacAlreadyExistsError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, RbacValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, RbacNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, InvalidAccessKeyError):
        return HTTPException(status_code=403, detail=str(exc))
    rbac_logger.exception(f"Unexpected error {action}: {exc}")
    return HTTPException(status_code=500, detail="Internal server error")


def _permission_to_schema(permission) -> PermissionSchema:
    return PermissionSchema.model_validate(
        {
            "id": permission.id,
            "name": permission.name,
            "title_key": permission.title_key,
            "description_key": permission.description_key,
            "plugin_permissions": [
                PluginPermissionSchema.model_validate(plugin_permission)
                for plugin_permission in getattr(permission, "plugin_permissions", [])
            ],
        }
    )


def _role_to_schema(role) -> RoleSchema:
    return RoleSchema.model_validate(role)


def _plugin_permission_to_schema(plugin_permission) -> PluginPermissionSchema:
    return PluginPermissionSchema(
        id=plugin_permission.id,
        permissions_id=plugin_permission.permissions_id,
        plugin_name=plugin_permission.plugin_name,
        permissions_dict=dict(plugin_permission.permissions_dict),
    )


@rbac_permissions_router.post("", response_model=PermissionSchema, status_code=201, summary="Create Permission (title/description by TranslationSmall keys)")
@limiter.limit(limit_minute(5))
async def create_permission_endpoint(
    request: Request,
    payload: PermissionCreateSchemaDep,
    session: SessionDep,
):
    try:
        return _permission_to_schema(await create_permission(payload, session))
    except Exception as exc:
        raise _to_http_error(exc, "creating permission") from exc


@rbac_permissions_router.get("", response_model=PermissionSchema, summary="Get Permission")
@limiter.limit(limit_minute(20))
async def get_permission_endpoint(
    request: Request,
    permission_id: int,
    session: SessionDep,
):
    try:
        return PermissionSchema.model_validate(await get_permission(permission_id, session))
    except Exception as exc:
        raise _to_http_error(exc, "getting permission") from exc


@rbac_roles_router.post("", response_model=RoleSchema, status_code=201, summary="Create Role (title/description by TranslationSmall keys)")
@limiter.limit(limit_minute(5))
async def create_role_endpoint(
    request: Request,
    payload: RoleCreateSchemaDep,
    session: SessionDep,
):
    try:
        return _role_to_schema(await create_role(payload, session))
    except Exception as exc:
        raise _to_http_error(exc, "creating role") from exc


@rbac_roles_router.get("", response_model=RoleSchema, summary="Get Role")
@limiter.limit(limit_minute(20))
async def get_role_endpoint(
    request: Request,
    role_id: int,
    session: SessionDep,
):
    try:
        return RoleSchema.model_validate(await get_role(role_id, session))
    except Exception as exc:
        raise _to_http_error(exc, "getting role") from exc


@rbac_plugin_permissions_router.post("", response_model=PluginPermissionCreateResponseSchema, status_code=201, summary="Create Plugin Permission Bucket (returns access key once)")
@limiter.limit(limit_minute(5))
async def create_plugin_permission_endpoint(
    request: Request,
    payload: PluginPermissionCreateSchemaDep,
    session: SessionDep,
):
    try:
        plugin_permission, access_key = await create_plugin_permission(payload, session)
        return PluginPermissionCreateResponseSchema(
            permission=PluginPermissionSchema.model_validate(plugin_permission),
            access_key=access_key,
        )
    except Exception as exc:
        raise _to_http_error(exc, "creating plugin permission") from exc


@rbac_plugin_permissions_router.get("", response_model=PluginPermissionPublicSchema, summary="Get Plugin Permission Bucket")
@limiter.limit(limit_minute(20))
async def get_plugin_permission_endpoint(
    request: Request,
    plugin_permission_id: int,
    session: SessionDep,
):
    try:
        plugin_permission = await get_plugin_permission(plugin_permission_id, session)
        return PluginPermissionPublicSchema(
            id=plugin_permission.id,
            permissions_id=plugin_permission.permissions_id,
            plugin_name=plugin_permission.plugin_name,
        )
    except Exception as exc:
        raise _to_http_error(exc, "getting plugin permission") from exc


@rbac_plugin_permissions_router.post("/resolve", response_model=PluginPermissionAccessResponseSchema, summary="Resolve plugin permission dict by access key")
@limiter.limit(limit_minute(10))
async def get_plugin_permissions_by_access_key_endpoint(
    request: Request,
    payload: PluginPermissionAccessSchemaDep,
    session: SessionDep,
):
    try:
        permissions_dict = await get_plugin_permissions_dict_by_access_key(
            plugin_permission_id=payload.plugin_permission_id,
            access_key=payload.access_key,
            session=session,
        )
        return PluginPermissionAccessResponseSchema(
            plugin_permission_id=payload.plugin_permission_id,
            permissions_dict=permissions_dict,
        )
    except Exception as exc:
        raise _to_http_error(exc, "reading plugin permissions") from exc


rbac_router.include_router(rbac_permissions_router)
rbac_router.include_router(rbac_roles_router)
rbac_router.include_router(rbac_plugin_permissions_router)
