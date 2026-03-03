def serialize_modules(modules):
    """
    Serializes a list of Module objects into a dictionary format suitable for API responses.
    
    Includes nested submodules.
    """
    data = []

    for m in modules:
        data.append({
            "code": m.code,
            "name": m.name,
            "icon": m.icon,
            "submodules": [
                {
                    "code": sm.submodule.code,
                    "name": sm.submodule.name,
                    "icon": sm.submodule.icon,
                }
                for sm in m.submodules.select_related('submodule').all()
            ],
        })

    return data


def serialize_tenant_modules(tenant_modules, permissions):
    """
    Serializes modules enabled for a specific tenant, annotated with user permissions.
    
    Args:
        tenant_modules: QuerySet of TenantModule objects.
        permissions: QuerySet of Permission objects available to the user.
        
    Returns:
        list: List of module dictionaries with 'permissions' (e.g., 'module_access') 
              and nested submodules.
    """
    modules = {}
    sub_index = {}

    # Build permission index
    perm_index = set(
        permissions.values_list(
            "module__code",
            "submodule__code",
            "code",
        )
    )

    for tm in tenant_modules:
        m = tm.module
        sm = tm.submodule

        # init module
        if m.code not in modules:
            modules[m.code] = {
                "code": m.code,
                "name": m.name,
                "icon": m.icon,
                "permissions": set(),
                "submodules": []
            }

        # module-level permission
        if (m.code, None) in perm_index:
            modules[m.code]["permissions"].add("module_access")

        # submodule
        if sm:
            key = (m.code, sm.code)
            if key not in sub_index:
                sm_obj = {
                    "code": sm.code,
                    "name": sm.name,
                    "permissions": set(),
                }
                modules[m.code]["submodules"].append(sm_obj)
                sub_index[key] = sm_obj

            if (m.code, sm.code) in perm_index:
                sub_index[key]["permissions"].add("submodule_access")

    return list(modules.values())
