def serialize_modules(modules):
    data = []

    for m in modules:
        data.append({
            "code": m.code,
            "name": m.name,
            "icon": m.icon,
            "submodules": [
                {
                    "code": sm.code,
                    "name": sm.name,
                    "icon": sm.icon,
                }
                for sm in m.submodules.all()
            ],
        })

    return data


def serialize_tenant_modules(tenant_modules, permissions):
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
