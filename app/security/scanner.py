"""Security scanner for Docker containers, host, and network."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("security")

# Capabilities considered dangerous
DANGEROUS_CAPS = {
    "SYS_ADMIN", "NET_ADMIN", "ALL", "SYS_PTRACE", "SYS_RAWIO",
    "DAC_OVERRIDE", "NET_RAW", "SYS_MODULE", "SYS_CHROOT", "SETFCAP",
}

# Sensitive host paths (source path -> is root-level critical)
SENSITIVE_PATHS = {"/": True, "/etc": True, "/root": True, "/proc": False, "/sys": False}

# Patterns suggesting secrets in environment variable names
SECRET_PATTERNS = {"PASSWORD", "SECRET", "KEY", "TOKEN", "API_KEY", "APIKEY", "PRIVATE", "CREDENTIAL"}

MAX_EXPOSED_PORTS = 10


def _w(severity: str, category: str, target: str, check_id: str,
       title: str, description: str, recommendation: str) -> dict[str, str]:
    return {
        "severity": severity, "category": category, "target": target,
        "check_id": check_id, "title": title,
        "description": description, "recommendation": recommendation,
    }


# ── Container checks ──────────────────────────────────────────

def _check_privileged(name: str, info: dict) -> list[dict]:
    if info.get("HostConfig", {}).get("Privileged"):
        return [_w("critical", "container", name, "privileged_mode",
                    "Privileged mode enabled",
                    f"Container '{name}' runs with --privileged, granting full host access.",
                    "Remove --privileged and use specific --cap-add flags instead.")]
    return []


def _check_root_user(name: str, info: dict) -> list[dict]:
    user = info.get("Config", {}).get("User", "")
    if not user or user in ("0", "root"):
        return [_w("warning", "container", name, "running_as_root",
                    "Running as root",
                    f"Container '{name}' runs as root (User: '{user or 'unset'}').",
                    "Set a non-root USER in Dockerfile or use --user flag.")]
    return []


def _check_capabilities(name: str, info: dict) -> list[dict]:
    cap_add = set(info.get("HostConfig", {}).get("CapAdd") or [])
    dangerous = cap_add & DANGEROUS_CAPS
    if dangerous:
        sev = "critical" if ("ALL" in dangerous or "SYS_ADMIN" in dangerous) else "warning"
        caps = ", ".join(sorted(dangerous))
        return [_w(sev, "container", name, "dangerous_capabilities",
                    f"Dangerous capabilities: {caps}",
                    f"Container '{name}' has capabilities: {caps}.",
                    "Use --cap-drop ALL and add only required capabilities.")]
    return []


def _check_docker_socket(name: str, info: dict) -> list[dict]:
    for m in info.get("Mounts") or []:
        if "docker.sock" in m.get("Source", ""):
            rw = m.get("RW", True)
            if rw:
                return [_w("critical", "container", name, "docker_socket_writable",
                           "Docker socket mounted read-write",
                           f"Container '{name}' has docker.sock with write access — full Docker API control.",
                           "Mount docker.sock read-only (:ro) or remove it.")]
            return [_w("warning", "container", name, "docker_socket_mounted",
                       "Docker socket mounted (read-only)",
                       f"Container '{name}' has docker.sock mounted read-only.",
                       "Consider if Docker socket access is truly needed.")]
    return []


def _check_sensitive_mounts(name: str, info: dict) -> list[dict]:
    warnings: list[dict] = []
    for m in info.get("Mounts") or []:
        src = m.get("Source", "")
        if "docker.sock" in src:
            continue
        for sensitive, is_root_critical in SENSITIVE_PATHS.items():
            if src == sensitive or (sensitive != "/" and src.startswith(sensitive + "/")):
                rw = m.get("RW", True)
                sev = "critical" if (rw and is_root_critical) else "warning"
                dest = m.get("Destination", "")
                warnings.append(_w(sev, "container", name,
                                   f"sensitive_mount",
                                   f"Sensitive host path: {src}",
                                   f"Container '{name}' mounts '{src}' -> '{dest}' ({'rw' if rw else 'ro'}).",
                                   "Mount as read-only (:ro) or remove if not needed."))
                break
    return warnings


def _check_readonly_rootfs(name: str, info: dict) -> list[dict]:
    if not info.get("HostConfig", {}).get("ReadonlyRootfs"):
        return [_w("info", "container", name, "no_readonly_rootfs",
                    "Root filesystem is writable",
                    f"Container '{name}' does not use --read-only.",
                    "Use --read-only with tmpfs for writable directories.")]
    return []


def _check_security_profiles(name: str, info: dict) -> list[dict]:
    warnings: list[dict] = []
    for opt in info.get("HostConfig", {}).get("SecurityOpt") or []:
        if "apparmor=unconfined" in opt:
            warnings.append(_w("warning", "container", name, "apparmor_disabled",
                                "AppArmor profile disabled",
                                f"Container '{name}' has AppArmor set to unconfined.",
                                "Use default AppArmor profile or a custom one."))
        if "seccomp=unconfined" in opt or "seccomp:unconfined" in opt:
            warnings.append(_w("warning", "container", name, "seccomp_disabled",
                                "Seccomp profile disabled",
                                f"Container '{name}' has Seccomp set to unconfined.",
                                "Use default Seccomp profile for syscall filtering."))
    return warnings


def _check_env_secrets(name: str, info: dict) -> list[dict]:
    env_list = info.get("Config", {}).get("Env") or []
    found: list[str] = []
    for env_str in env_list:
        key = env_str.split("=", 1)[0].upper()
        if any(p in key for p in SECRET_PATTERNS):
            found.append(env_str.split("=", 1)[0])
    if found:
        display = found[:5]
        extra = f" (+{len(found) - 5} more)" if len(found) > 5 else ""
        return [_w("warning", "container", name, "env_secrets",
                    f"Potential secrets in environment ({len(found)} vars)",
                    f"Container '{name}' has env vars matching secret patterns: {', '.join(display)}{extra}. Values are NOT shown.",
                    "Use Docker secrets or config files instead of environment variables.")]
    return []


def _check_resource_limits(name: str, info: dict) -> list[dict]:
    hc = info.get("HostConfig", {})
    warnings: list[dict] = []
    if not hc.get("Memory", 0):
        warnings.append(_w("info", "container", name, "no_memory_limit",
                           "No memory limit",
                           f"Container '{name}' has no memory limit, risking host OOM.",
                           "Set --memory limit (e.g., --memory=512m)."))
    if not (hc.get("NanoCpus", 0) or hc.get("CpuQuota", 0)):
        warnings.append(_w("info", "container", name, "no_cpu_limit",
                           "No CPU limit",
                           f"Container '{name}' has no CPU limit.",
                           "Set --cpus limit (e.g., --cpus=1.0)."))
    return warnings


# ── Network checks ─────────────────────────────────────────────

def _check_host_network(name: str, info: dict) -> list[dict]:
    if info.get("HostConfig", {}).get("NetworkMode") == "host":
        return [_w("warning", "network", name, "host_network_mode",
                    "Host network mode",
                    f"Container '{name}' uses --net=host, sharing the host network namespace.",
                    "Use bridge network with explicit port mapping.")]
    return []


def _check_exposed_ports(name: str, info: dict) -> list[dict]:
    bindings = info.get("HostConfig", {}).get("PortBindings") or {}
    count = len(bindings)
    if count > MAX_EXPOSED_PORTS:
        return [_w("info", "network", name, "many_exposed_ports",
                    f"{count} ports exposed",
                    f"Container '{name}' exposes {count} ports (>{MAX_EXPOSED_PORTS}).",
                    "Expose only necessary ports; use Docker networks for inter-service communication.")]
    return []


def _check_ssh_exposed(name: str, info: dict) -> list[dict]:
    """Check if container exposes SSH port (22) to the host."""
    bindings = info.get("HostConfig", {}).get("PortBindings") or {}
    for port_proto, hosts in bindings.items():
        if port_proto.startswith("22/") and hosts:
            host_port = hosts[0].get("HostPort", "22") if hosts else "22"
            return [_w("warning", "network", name, "ssh_port_exposed",
                       f"SSH port exposed (host:{host_port})",
                       f"Container '{name}' exposes SSH port 22 to host port {host_port}.",
                       "Avoid exposing SSH from containers. Use 'docker exec' for access instead.")]
    return []


# ── Host / daemon checks ──────────────────────────────────────

def _check_daemon_security(system_info: dict) -> list[dict]:
    warnings: list[dict] = []
    opts = set()
    for opt in system_info.get("SecurityOptions") or []:
        for part in opt.split(","):
            if part.startswith("name="):
                opts.add(part.split("=", 1)[1])

    if "apparmor" not in opts and "selinux" not in opts:
        warnings.append(_w("warning", "host", "docker-daemon", "no_mac_security",
                           "No AppArmor/SELinux on Docker daemon",
                           "Docker daemon has neither AppArmor nor SELinux enabled.",
                           "Enable AppArmor or SELinux for mandatory access control."))
    if "seccomp" not in opts:
        warnings.append(_w("warning", "host", "docker-daemon", "no_seccomp_default",
                           "No default Seccomp profile",
                           "Docker daemon does not have a default Seccomp profile.",
                           "Enable default Seccomp profile to restrict syscalls."))
    return warnings


def _check_kernel_aslr() -> list[dict]:
    path = "/host_proc/sys/kernel/randomize_va_space"
    try:
        with open(path) as f:
            val = f.read().strip()
        if val != "2":
            return [_w("warning", "host", "kernel", "aslr_not_full",
                       f"ASLR not fully enabled (value={val})",
                       "kernel.randomize_va_space is not set to 2 (full randomization).",
                       "Set kernel.randomize_va_space=2 for full ASLR protection.")]
        return []
    except OSError:
        return [_w("unavailable", "host", "kernel", "kernel_aslr",
                   "Kernel ASLR check unavailable",
                   "Cannot read /proc/sys/kernel/randomize_va_space.",
                   "Add '/proc:/host_proc:ro' volume mount in docker-compose.yml to enable this check.")]


def _check_ip_forward() -> list[dict]:
    path = "/host_proc/sys/net/ipv4/ip_forward"
    try:
        with open(path) as f:
            val = f.read().strip()
        if val == "1":
            return [_w("info", "host", "kernel", "ip_forward_enabled",
                       "IP forwarding enabled",
                       "net.ipv4.ip_forward=1 (required by Docker, increases attack surface).",
                       "This is expected for Docker networking. Verify no unintended routing.")]
        return []
    except OSError:
        return [_w("unavailable", "host", "kernel", "kernel_ip_forward",
                   "IP forwarding check unavailable",
                   "Cannot read /proc/sys/net/ipv4/ip_forward.",
                   "Add '/proc:/host_proc:ro' volume mount in docker-compose.yml to enable this check.")]


def _check_kernel_security_module() -> list[dict]:
    path = "/host_sys/kernel/security/lsm"
    try:
        with open(path) as f:
            val = f.read().strip()
        if not val:
            return [_w("warning", "host", "kernel", "no_lsm",
                       "No Linux Security Module loaded",
                       "No LSM active on the host kernel.",
                       "Enable AppArmor, SELinux, or another LSM for mandatory access control.")]
        return [_w("info", "host", "kernel", "lsm_active",
                   f"LSM active: {val}",
                   f"Kernel security modules: {val}.",
                   "No action needed.")]
    except OSError:
        return [_w("unavailable", "host", "kernel", "kernel_lsm",
                   "Kernel security module check unavailable",
                   "Cannot read /sys/kernel/security/lsm.",
                   "Add '/sys:/host_sys:ro' volume mount in docker-compose.yml to enable this check.")]


# ── Main scan entry point ─────────────────────────────────────

async def scan(docker: Any) -> list[dict]:
    """Run full security scan. Returns list of warning dicts."""
    warnings: list[dict] = []

    try:
        containers = await docker.containers.list(all=True)
        for c in containers:
            try:
                info = await c.show()
            except Exception:
                continue
            name = info.get("Name", "").lstrip("/")

            # Container checks
            warnings.extend(_check_privileged(name, info))
            warnings.extend(_check_root_user(name, info))
            warnings.extend(_check_capabilities(name, info))
            warnings.extend(_check_docker_socket(name, info))
            warnings.extend(_check_sensitive_mounts(name, info))
            warnings.extend(_check_readonly_rootfs(name, info))
            warnings.extend(_check_security_profiles(name, info))
            warnings.extend(_check_env_secrets(name, info))
            warnings.extend(_check_resource_limits(name, info))

            # Network checks
            warnings.extend(_check_host_network(name, info))
            warnings.extend(_check_exposed_ports(name, info))
            warnings.extend(_check_ssh_exposed(name, info))
    except Exception as e:
        logger.warning("Container security scan failed: %s", e)

    # Daemon checks
    try:
        system_info = await docker._query_json("info")
        warnings.extend(_check_daemon_security(system_info))
    except Exception as e:
        logger.warning("Daemon security check failed: %s", e)

    # Host/kernel checks (filesystem-based, may be unavailable)
    warnings.extend(_check_kernel_aslr())
    warnings.extend(_check_ip_forward())
    warnings.extend(_check_kernel_security_module())

    return warnings
