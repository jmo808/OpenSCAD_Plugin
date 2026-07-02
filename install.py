import os
import json
import shutil
import asyncio

# Target directories for Antigravity
SCHEMA_DIRS = [
    os.path.expanduser("~/.gemini/antigravity/mcp/openscad-mcp"),
    os.path.expanduser("~/.gemini/antigravity-cli/mcp/openscad-mcp"),
    os.path.expanduser("~/.gemini/antigravity-ide/mcp/openscad-mcp"),
]
PLUGIN_DIR = os.path.expanduser("~/.gemini/config/plugins/openscad-mcp")

# Paths for other MCP clients
CLIENT_CONFIGS = {
    "Claude Code": os.path.expanduser("~/.claude.json"),
    "GitHub Copilot": os.path.expanduser("~/.config/github-copilot/mcp.json"),
    "AWS Kiro": os.path.expanduser("~/.aws/kiro/mcp.json")
}

def update_json_config(file_path: str, server_name: str, command: str, args: list[str], env: dict = None):
    """Safely updates a JSON configuration file to inject the MCP server definition."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    config = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                config = json.load(f)
        except json.JSONDecodeError:
            print(f"  Warning: {file_path} is invalid JSON. Overwriting.")
            config = {}

    # Initialize mcpServers key if missing
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Inject server definition
    server_def = {
        "command": command,
        "args": args
    }
    if env:
        server_def["env"] = env
        
    config["mcpServers"][server_name] = server_def

    with open(file_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"  Updated {file_path} with {server_name} configuration.")

def run_install():
    # Import mcp from server.py in the same directory
    from server import mcp
    
    current_dir = os.path.abspath(os.path.dirname(__file__))
    server_script = os.path.join(current_dir, "server.py")
    
    print("\n--- 1. Installing Antigravity MCP Schemas ---")
    tools = asyncio.run(mcp.list_tools())
    for schema_dir in SCHEMA_DIRS:
        print(f"Installing to {schema_dir}...")
        os.makedirs(schema_dir, exist_ok=True)
        
        for tool in tools:
            schema_file = os.path.join(schema_dir, f"{tool.name}.json")
            tool_json = {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema
            }
            with open(schema_file, "w") as f:
                json.dump(tool_json, f, indent=2)
            
        src_instructions = "instructions.md"
        if os.path.exists(src_instructions):
            shutil.copy(src_instructions, os.path.join(schema_dir, "instructions.md"))
            
    print("\n--- 2. Installing Antigravity Plugin Config ---")
    os.makedirs(PLUGIN_DIR, exist_ok=True)
    for f in ["plugin.json", "mcp_config.json"]:
        if os.path.exists(f):
            shutil.copy(f, os.path.join(PLUGIN_DIR, f))
            print(f"  Copied {f}")
            
    skills_dest_dir = os.path.join(PLUGIN_DIR, "skills", "openscad-mcp")
    os.makedirs(skills_dest_dir, exist_ok=True)
    src_skill = os.path.join("skills", "openscad-mcp", "SKILL.md")
    if os.path.exists(src_skill):
        shutil.copy(src_skill, os.path.join(skills_dest_dir, "SKILL.md"))
        print(f"  Copied SKILL.md to {skills_dest_dir}")

    print("\n--- 3. Installing to Other AI Agents ---")
    command = "uv"
    args = ["--directory", current_dir, "run", "python", server_script]
    
    for agent_name, config_path in CLIENT_CONFIGS.items():
        print(f"Configuring for {agent_name}...")
        update_json_config(config_path, "openscad-mcp", command, args)

    print("\nOpenSCAD MCP plugin installation complete for all agents!")

if __name__ == "__main__":
    run_install()
