#!/usr/bin/env python3
import os
import sys
import re

server_host = os.environ.get("CUSTOM_SERVER_HOST", "rustdesk.palma.cloudns.cc").strip()
server_key = os.environ.get("CUSTOM_SERVER_KEY", "fUKE4r0Y0R6UPOAmi+i+uIrrLsdcEaYCbk6RWSZQoZQ=").strip()
unattended = os.environ.get("CUSTOM_UNATTENDED_MODE", "false").strip().lower() == "true"

print("==================================================")
print("  RustDesk Custom Server Configurator (Oracle Cloud)")
print(f"  Server Host:     {server_host}")
print(f"  Public Key:      {server_key}")
print(f"  Unattended Mode: {unattended}")
print("==================================================")

config_path = "libs/hbb_common/src/config.rs"

if not os.path.exists(config_path):
    print(f"Error: {config_path} not found! Current directory: {os.getcwd()}")
    sys.exit(1)

with open(config_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Hardcode RENDEZVOUS_SERVERS
content, count_servers = re.subn(
    r'pub const RENDEZVOUS_SERVERS:\s*&\[&str\]\s*=\s*&\[.*?\];',
    f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{server_host}"];',
    content
)
print(f"Patched RENDEZVOUS_SERVERS: {count_servers} match(es)")

# 2. Hardcode RS_PUB_KEY
content, count_key = re.subn(
    r'pub const RS_PUB_KEY:\s*&str\s*=\s*".*?";',
    f'pub const RS_PUB_KEY: &str = "{server_key}";',
    content
)
print(f"Patched RS_PUB_KEY: {count_key} match(es)")

# 3. Lock get_rendezvous_server() so it strictly returns our server
old_get_server = "pub fn get_rendezvous_server() -> String {"
new_get_server = f"""pub fn get_rendezvous_server() -> String {{
        return format!("{server_host}:{{RENDEZVOUS_PORT}}");"""

if old_get_server in content:
    content = content.replace(old_get_server, new_get_server)
    print("Locked get_rendezvous_server() to custom server")
else:
    print("Warning: get_rendezvous_server() signature not matched directly")

# 4. Lock get_rendezvous_servers()
old_get_servers = "pub fn get_rendezvous_servers() -> Vec<String> {"
new_get_servers = f"""pub fn get_rendezvous_servers() -> Vec<String> {{
        return vec!["{server_host}".to_owned()];"""

if old_get_servers in content:
    content = content.replace(old_get_servers, new_get_servers)
    print("Locked get_rendezvous_servers() to custom server")
else:
    print("Warning: get_rendezvous_servers() signature not matched directly")

# 5. Unattended mode support (accept sessions with password, no manual prompt)
if unattended:
    print("Injecting unattended access defaults (approve-mode: password)...")
    content = content.replace(
        'pub static ref DEFAULT_SETTINGS: RwLock<HashMap<String, String>> = Default::default();',
        '''pub static ref DEFAULT_SETTINGS: RwLock<HashMap<String, String>> = RwLock::new(HashMap::from([
        ("approve-mode".to_string(), "password".to_string()),
        ("verification-method".to_string(), "use-permanent-password".to_string()),
    ]));'''
    )

with open(config_path, "w", encoding="utf-8") as f:
    f.write(content)

print("SUCCESS: libs/hbb_common/src/config.rs customized and locked!")
