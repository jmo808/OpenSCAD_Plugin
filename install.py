import os
import json
import shutil
import asyncio

# Target directories for MCP tools schemas and instructions
SCHEMA_DIRS = [
    os.path.expanduser("~/.gemini/antigravity/mcp/openscad-mcp"),
    os.path.expanduser("~/.gemini/antigravity-cli/mcp/openscad-mcp"),
    os.path.expanduser("~/.gemini/antigravity-ide/mcp/openscad-mcp"),
]

# Target directory for the Antigravity Plugin configuration
PLUGIN_DIR = os.path.expanduser("~/.gemini/config/plugins/openscad-mcp")

def run_install():
    # Import mcp from server.py in the same directory
    from server import mcp
    
    # Export tool schemas
    tools = asyncio.run(mcp.list_tools())
    
    # 1. Install tool schemas and instructions to the harness schema directories
    for schema_dir in SCHEMA_DIRS:
        print(f"Installing OpenSCAD MCP schemas to {schema_dir}...")
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
            print(f"  Exported schema for {tool.name} to {schema_file}")
            
        # Copy instructions.md
        src_instructions = "instructions.md"
        if os.path.exists(src_instructions):
            dest_instructions = os.path.join(schema_dir, "instructions.md")
            shutil.copy(src_instructions, dest_instructions)
            print(f"  Copied instructions.md to {dest_instructions}")
        else:
            print("  Warning: instructions.md not found in current directory.")
            
    # 2. Install plugin configurations (plugin.json, mcp_config.json, skills)
    print(f"Installing Antigravity Plugin to {PLUGIN_DIR}...")
    os.makedirs(PLUGIN_DIR, exist_ok=True)
    
    # Copy plugin.json
    if os.path.exists("plugin.json"):
        shutil.copy("plugin.json", os.path.join(PLUGIN_DIR, "plugin.json"))
        print("  Copied plugin.json")
        
    # Copy mcp_config.json
    if os.path.exists("mcp_config.json"):
        shutil.copy("mcp_config.json", os.path.join(PLUGIN_DIR, "mcp_config.json"))
        print("  Copied mcp_config.json")
        
    # Copy skills/openscad-mcp/SKILL.md
    skills_dest_dir = os.path.join(PLUGIN_DIR, "skills", "openscad-mcp")
    os.makedirs(skills_dest_dir, exist_ok=True)
    
    src_skill = os.path.join("skills", "openscad-mcp", "SKILL.md")
    if os.path.exists(src_skill):
        shutil.copy(src_skill, os.path.join(skills_dest_dir, "SKILL.md"))
        print(f"  Copied SKILL.md to {skills_dest_dir}")
    else:
        print("  Warning: SKILL.md not found in workspace.")
        
    print("\nOpenSCAD MCP plugin installation complete!")

if __name__ == "__main__":
    run_install()
