from sqlmodel import Session, select

from .database import engine
from .models import Permission, Role, RolePermission


PERMISSIONS = {
    "employee:view": "View employees",
    "employee:create": "Create employees",
    "employee:update": "Update employees",
    "employee:suspend": "Suspend employees",

    "order:view": "View orders",
    "order:create": "Create orders",
    "order:update": "Update orders",
    "order:void": "Void orders",

    "payment:view": "View payments",
    "payment:create": "Create payments",
    "payment:refund": "Refund payments",

    "inventory:view": "View inventory",
    "inventory:adjust": "Adjust inventory",

    "kitchen:view": "View kitchen orders",
    "kitchen:update": "Update kitchen orders",

    "reports:view": "View reports",
}


ROLE_PERMISSIONS = {
    "MANAGER": list(PERMISSIONS.keys()),

    "ADMIN": [
        "employee:view",
        "employee:create",
        "employee:update",

        "order:view",
        "order:create",
        "order:update",
        "order:void",

        "payment:view",

        "inventory:view",
        "inventory:adjust",

        "reports:view",
    ],

    "CASHIER": [
        "order:view",
        "order:create",

        "payment:view",
        "payment:create",
    ],

    "WAITER": [
        "order:view",
        "order:create",
    ],

    "CHEF": [
        "kitchen:view",
        "kitchen:update",
    ],
}


def seed_rbac():
    with Session(engine) as session:

        # 1. Create permissions
        permissions = {}

        for code, description in PERMISSIONS.items():
            permission = session.exec(
                select(Permission).where(Permission.code == code)
            ).first()

            if not permission:
                permission = Permission(
                    code=code,
                    description=description,
                )
                session.add(permission)
                session.flush()

            permissions[code] = permission

        # 2. Create global roles
        roles = {}

        for role_name in ROLE_PERMISSIONS:
            role = session.exec(
                select(Role).where(Role.name == role_name)
            ).first()

            if not role:
                role = Role(name=role_name)
                session.add(role)
                session.flush()

            roles[role_name] = role

        # 3. Assign permissions to roles
        for role_name, permission_codes in ROLE_PERMISSIONS.items():

            role = roles[role_name]

            for permission_code in permission_codes:
                permission = permissions[permission_code]

                existing = session.exec(
                    select(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == permission.id,
                    )
                ).first()

                if not existing:
                    session.add(
                        RolePermission(
                            role_id=role.id,
                            permission_id=permission.id,
                        )
                    )

        session.commit()


if __name__ == "__main__":
    seed_rbac()