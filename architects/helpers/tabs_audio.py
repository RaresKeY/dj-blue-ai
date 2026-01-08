import subprocess, json, re, time

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

def get_audio_graph():
    """
    Parses PipeWire dump to build a graph of Apps, Sinks, and Sources.
    Returns (apps, sinks, sources)
    """
    try:
        data = json.loads(subprocess.check_output(["pw-dump"], text=True))
    except (subprocess.CalledProcessError, FileNotFoundError):
        return [], {}, {}
    
    apps = []
    sinks = {}
    sources = {} # Physical sources or monitors

    # 1. First pass: Collect all Sinks and Sources
    for node in data:
        props = node.get("info", {}).get("props", {})
        node_id = node.get("id")
        media_class = props.get("media.class", "")
        
        if media_class == "Audio/Sink":
            name = props.get("node.name")
            desc = props.get("node.description", name)
            # The monitor source for a sink is typically "sink_name.monitor"
            sinks[node_id] = {
                "name": name,
                "desc": desc,
                "monitor": f"{name}.monitor"
            }
            # Add implicit monitor to sources list too, if we want "all sources"
            sources[f"{name}.monitor"] = {
                "name": f"{name}.monitor",
                "desc": f"Monitor of {desc}",
                "is_monitor": True
            }
            
        elif media_class == "Audio/Source":
             name = props.get("node.name")
             sources[name] = {
                 "name": name,
                 "desc": props.get("node.description", name),
                 "is_monitor": False
             }

    # 2. Second pass: Collect Apps and link to Sinks
    for node in data:
        props = node.get("info", {}).get("props", {})
        node_id = node.get("id")
        
        if is_playback(props): 
            target = props.get("node.target") # string ID or int
            info = extract_audio_info(node)
            
            apps.append({
                "id": node_id,
                "name": info.get("name") or "Unknown App",
                "title": info.get("title") or "Unknown Stream",
                "target_id": int(target) if target else None
            })
            
    return apps, sinks, sources

def get_display_names():
    """Returns list of (App Name, Window Title) for UI."""
    apps, _, _ = get_audio_graph()
    # Filter out empty names
    return [(a["name"], a["title"]) for a in apps if a["name"]]

def resolve_app_to_monitor(app_name_fragment):
    """
    Finds a monitor source for an app matching the name fragment.
    Returns source_name or None.
    """
    apps, sinks, _ = get_audio_graph()
    
    # Simple substring match
    target_app = None
    for app in apps:
        if app_name_fragment.lower() in (app.get("name") or "").lower():
            target_app = app
            break
            
    if not target_app:
        return None
        
    target_sink_id = target_app.get("target_id")
    if target_sink_id and target_sink_id in sinks:
        return sinks[target_sink_id]["monitor"]
        
    # Fallback to default sink's monitor if no explicit target
    try:
        default_sink = subprocess.check_output(["pactl", "get-default-sink"], text=True).strip()
        return f"{default_sink}.monitor"
    except:
        pass
        
    return None

def get_all_recordable_sources(blacklist=None):
    """
    Returns a list of all recordable source names (monitors + mics),
    filtering out any that contain strings from the blacklist.
    """
    if blacklist is None:
        blacklist = []
        
    _, _, sources = get_audio_graph()
    valid_sources = []
    
    for name, info in sources.items():
        # Check blacklist
        is_blocked = False
        for block in blacklist:
            if block.lower() in name.lower() or block.lower() in info["desc"].lower():
                is_blocked = True
                break
        
        if not is_blocked:
            valid_sources.append(name)
            
    return valid_sources


class AppIsolationManager:
    """
    Helper to isolate applications by moving them to a temporary Null Sink
    so they can be recorded independently of the system mix.
    """
    
    @staticmethod
    def get_sink_inputs():
        """Parses 'pactl list sink-inputs' to return list of dicts."""
        output = subprocess.check_output(["pactl", "list", "sink-inputs"], text=True)
        inputs = []
        current = {}
        
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("Sink Input #"):
                if current:
                    inputs.append(current)
                current = {"id": line.split("#")[1], "properties": {}}
            elif "=" in line and current:
                # Property line
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"')
                current["properties"][key] = val
            elif ":" in line and current and "Properties:" not in line:
                # Attribute line (Volume, etc)
                key, val = line.split(":", 1)
                current[key.strip()] = val.strip()
                
        if current:
            inputs.append(current)
            
        return inputs

    @staticmethod
    def _isolate_streams(target_ids, session_name="Gemini Capture"):
        """
        Internal: Moves specified stream IDs to a new Null Sink + Loopback.
        """
        if not target_ids:
            raise ValueError("No streams to isolate.")

        # Determine original sinks to handle EasyEffects/Loopback targeting
        all_inputs = AppIsolationManager.get_sink_inputs()
        original_sink_map = {}
        for inp in all_inputs:
            if inp["id"] in target_ids:
                original_sink_map[inp["id"]] = inp.get("Sink")

        # Unique ID for this isolation session
        session_id = int(time.time())
        sink_name = f"Gemini_ISO_{session_id}"
        
        # 1. Load Null Sink
        print(f"[Isolation] Creating Null Sink: {sink_name}")
        mod_null = subprocess.check_output([
            "pactl", "load-module", "module-null-sink", 
            f"sink_name={sink_name}", 
            f"sink_properties=device.description=\"{session_name}\""
        ], text=True).strip()
        
        # 2. Determine Loopback Target
        # Check if *any* of the target streams were on EasyEffects
        try:
            sinks_output = subprocess.check_output(["pactl", "list", "short", "sinks"], text=True)
            sink_idx_to_name = {}
            for line in sinks_output.splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    sink_idx_to_name[parts[0]] = parts[1]
        except:
            sink_idx_to_name = {}

        loopback_target = None
        
        # Heuristic: if any stream was on EasyEffects, preserve that chain.
        # Otherwise, default to system default.
        for sid in target_ids:
            s_idx = original_sink_map.get(sid)
            if s_idx and s_idx in sink_idx_to_name:
                s_name = sink_idx_to_name[s_idx]
                if "easyeffects" in s_name.lower():
                    print(f"[Isolation] Detected EasyEffects on stream {sid}. Preserving chain.")
                    loopback_target = s_name
                    break
        
        if not loopback_target:
            loopback_target = subprocess.check_output(["pactl", "get-default-sink"], text=True).strip()
        
        print(f"[Isolation] Creating Loopback to: {loopback_target}")
        mod_loop = subprocess.check_output([
            "pactl", "load-module", "module-loopback",
            f"source={sink_name}.monitor",
            f"sink={loopback_target}"
        ], text=True).strip()
        
        # 3. Move Streams
        for sid in target_ids:
            print(f"[Isolation] Moving stream {sid} to {sink_name}")
            subprocess.run(["pactl", "move-sink-input", sid, sink_name], check=False)
            
        def cleanup():
            print(f"[Isolation] Cleaning up {sink_name}...")
            subprocess.run(["pactl", "unload-module", mod_loop], check=False)
            subprocess.run(["pactl", "unload-module", mod_null], check=False)
            
        return f"{sink_name}.monitor", cleanup

    @staticmethod
    def isolate_app(app_name_fragment):
        """Isolates a single app by name fragment."""
        return AppIsolationManager.isolate_apps([app_name_fragment])

    @staticmethod
    def isolate_apps(app_name_fragments):
        """Isolates multiple apps (by name fragments) into a single mixed capture."""
        all_inputs = AppIsolationManager.get_sink_inputs()
        target_ids = []
        
        # Normalize fragments to lower case
        fragments = [f.lower() for f in app_name_fragments]
        
        for inp in all_inputs:
            props = inp.get("properties", {})
            name = props.get("application.name", "")
            if not name:
                name = props.get("media.name", "")
            
            name_lower = name.lower()
            if any(frag in name_lower for frag in fragments):
                target_ids.append(inp["id"])
                
        if not target_ids:
            raise ValueError(f"No active streams found for apps: {app_name_fragments}")
            
        desc = f"Gemini Capture ({', '.join(app_name_fragments)})"
        return AppIsolationManager._isolate_streams(target_ids, desc)

    @staticmethod
    def isolate_all_except(excluded_fragments):
        """
        Isolates ALL active application streams EXCEPT those matching the excluded fragments.
        Useful for 'Record System Audio but exclude DJ App'.
        """
        all_inputs = AppIsolationManager.get_sink_inputs()
        target_ids = []
        
        exclusions = [f.lower() for f in excluded_fragments]
        
        for inp in all_inputs:
            props = inp.get("properties", {})
            name = props.get("application.name", "")
            if not name:
                name = props.get("media.name", "")
            
            name_lower = name.lower()
            
            # If name matches any exclusion, SKIP it.
            if any(ex in name_lower for ex in exclusions):
                print(f"[Isolation] Excluding stream: {name}")
                continue
                
            # Otherwise, include it
            target_ids.append(inp["id"])
            
        if not target_ids:
            raise ValueError("No streams left to isolate after exclusions.")
            
        desc = f"Gemini Capture (All except {', '.join(excluded_fragments)})"
        return AppIsolationManager._isolate_streams(target_ids, desc)