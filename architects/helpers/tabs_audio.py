import subprocess, json

def is_playback(props):
    if not props.get("application.name"):
        return False

    mc = props.get("media.class", "").lower()
    direction = (
        props.get("stream.direction")
        or props.get("node.direction")
        or ""
    ).lower()

    # Must be audio-related
    if "audio" not in mc:
        return False

    # Prefer direction when available
    if direction == "output":
        return True

    # If direction missing, infer from class
    if "output" in mc or "sinkinput" in mc or "stream" in mc:
        return True

    return False

def extract_audio_info(node):
    info = {
        "id": node.get("id"),
        "name": None,
        "title": None,
        "rate": None,
        "channels": None,
        "format": None,
    }

    props  = node.get("info", {}).get("props", {})
    params = node.get("info", {}).get("params", {})

    info["name"]  = props.get("application.name")
    info["title"] = props.get("media.name")

    # ---- RATE (from node.rate) ----
    rate_str = props.get("node.rate")
    if rate_str and "/" in rate_str:
        try:
            num, den = map(int, rate_str.split("/"))
            info["rate"] = den // max(num, 1)
        except:
            pass

    # ---- FORMAT + CHANNELS ----
    # params may be:
    # 1) dict: { "EnumFormat": [ {...}, {...} ], "Format": [...] }
    # 2) list: [ {...}, {...} ]
    # 3) empty
    # 4) variant with "properties" array (old SPA)
    
    def enum_entries(params):
        # Case 1: params is dict
        if isinstance(params, dict):
            for key, val in params.items():
                if key in ("EnumFormat", "Format"):
                    # val may be list or dict
                    if isinstance(val, list):
                        for item in val:
                            if isinstance(item, dict):
                                yield item
                    elif isinstance(val, dict):
                        yield val
        
        # Case 2: params is list
        if isinstance(params, list):
            for p in params:
                if isinstance(p, dict) and p.get("id") in ("EnumFormat", "Format"):
                    # old style: p["properties"] contains list of dicts
                    props_list = p.get("properties")
                    if isinstance(props_list, list):
                        for item in props_list:
                            if isinstance(item, dict):
                                yield item
                    
                    # modern style: flat dict entries inside p itself
                    for k, v in p.items():
                        if isinstance(v, dict):
                            yield v
                        if isinstance(v, list):
                            for i in v:
                                if isinstance(i, dict):
                                    yield i

    # Parse formats
    for entry in enum_entries(params):
        if entry.get("mediaType") != "audio":
            continue
        if entry.get("mediaSubtype") not in ("raw", "RAW"):
            continue

        fmt = entry.get("format")
        ch  = entry.get("channels")
        rt  = entry.get("rate")

        if fmt:
            info["format"] = fmt
        if ch:
            info["channels"] = ch
        if rt:
            info["rate"] = rt

    return info

def get_display_names():
    nodes = json.loads(subprocess.check_output(["pw-dump"]))
    all_app_names = []

    for node in nodes:
        props = node.get("info", {}).get("props", {})
        if is_playback(props):
            data = extract_audio_info(node)
            all_app_names.append((data.get("name"), data.get("title")))
    return all_app_names