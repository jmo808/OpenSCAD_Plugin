import os
import re

def parse_inline_bom(scad_path: str) -> tuple[list[dict], list[str]]:
    """Parses inline BOM comment annotations from a SCAD file.
    
    Returns:
        (entries, warnings)
    """
    if not os.path.exists(scad_path):
        raise FileNotFoundError(f"SCAD file not found at: '{scad_path}'")
        
    entries = []
    warnings = []
    
    with open(scad_path, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped:
                continue
            
            # Match // BOM: (case-sensitive as per spec)
            match = re.search(r'//\s*BOM:\s*(.*)', line)
            if not match:
                continue
                
            annotation_text = match.group(1).strip()
            if not annotation_text:
                warnings.append(f"Line {idx}: Empty BOM annotation")
                continue
                
            parts = [p.strip() for p in annotation_text.split(',')]
            if not parts or not parts[0]:
                warnings.append(f"Line {idx}: Malformed BOM annotation '{annotation_text}'")
                continue
                
            # Parse fields
            first_part = parts[0]
            name = None
            fields = {}
            
            if '=' in first_part:
                k, v = first_part.split('=', 1)
                k_clean = k.strip().lower()
                if k_clean in ['qty', 'category', 'supplier', 'part_number', 'part_no']:
                    fields[k_clean] = v.strip()
                else:
                    name = first_part
            else:
                name = first_part
                
            for p in parts[1:]:
                if '=' in p:
                    k, v = p.split('=', 1)
                    fields[k.strip().lower()] = v.strip()
                    
            # Validation
            if not name:
                warnings.append(f"Line {idx}: Malformed BOM annotation (missing part name): '{line.strip()}'")
                continue
                
            if 'category' not in fields or not fields['category']:
                warnings.append(f"Line {idx}: Malformed BOM annotation (missing category): '{line.strip()}'")
                continue
                
            if 'qty' not in fields:
                warnings.append(f"Line {idx}: Malformed BOM annotation (missing quantity): '{line.strip()}'")
                continue
                
            try:
                qty = int(fields['qty'])
            except ValueError:
                warnings.append(f"Line {idx}: Malformed BOM annotation (invalid quantity '{fields['qty']}'): '{line.strip()}'")
                continue
                
            entry = {
                "name": name,
                "qty": qty,
                "category": fields["category"],
                "source_line": idx
            }
            
            if "supplier" in fields:
                entry["supplier"] = fields["supplier"]
            if "part_number" in fields:
                entry["part_number"] = fields["part_number"]
            elif "part_no" in fields:
                entry["part_number"] = fields["part_no"]
                
            entries.append(entry)
            
    return entries, warnings

def parse_block_bom(scad_path: str) -> tuple[list[dict], list[str]]:
    """Parses block BOM annotations (/* BOM: ... */) from a SCAD file.
    
    Returns:
        (entries, warnings)
    """
    if not os.path.exists(scad_path):
        raise FileNotFoundError(f"SCAD file not found at: '{scad_path}'")
        
    entries = []
    warnings = []
    
    with open(scad_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    pattern = re.compile(r'/\*\s*BOM:([\s\S]*?)\*/')
    
    for match in pattern.finditer(content):
        start_pos = match.start()
        source_line = content[:start_pos].count('\n') + 1
        
        block_text = match.group(1)
        lines = block_text.split('\n')
        fields = {}
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            if line_stripped.startswith('*'):
                line_stripped = line_stripped[1:].strip()
            if not line_stripped:
                continue
                
            if ':' in line_stripped:
                k, v = line_stripped.split(':', 1)
                fields[k.strip().lower()] = v.strip()
                
        name = fields.get('name')
        qty_str = fields.get('qty')
        category = fields.get('category')
        
        if not name:
            warnings.append(f"Line {source_line}: Malformed BOM block (missing name)")
            continue
        if not category:
            warnings.append(f"Line {source_line}: Malformed BOM block (missing category)")
            continue
        if qty_str is None:
            warnings.append(f"Line {source_line}: Malformed BOM block (missing quantity)")
            continue
            
        try:
            qty = int(qty_str)
        except ValueError:
            warnings.append(f"Line {source_line}: Malformed BOM block (invalid quantity '{qty_str}')")
            continue
            
        entry = {
            "name": name,
            "qty": qty,
            "category": category,
            "source_line": source_line
        }
        
        if "supplier" in fields:
            entry["supplier"] = fields["supplier"]
        if "part_number" in fields:
            entry["part_number"] = fields["part_number"]
        elif "part_no" in fields:
            entry["part_number"] = fields["part_no"]
            
        entries.append(entry)
        
    return entries, warnings

def parse_bom_annotations(scad_path: str) -> tuple[list[dict], list[str]]:
    """Combines inline and block BOM annotation parsing from a SCAD file.
    
    Returns:
        (entries, warnings) sorted by line number.
    """
    inline_entries, inline_warnings = parse_inline_bom(scad_path)
    block_entries, block_warnings = parse_block_bom(scad_path)
    
    all_entries = inline_entries + block_entries
    all_entries.sort(key=lambda x: x["source_line"])
    
    all_warnings = inline_warnings + block_warnings
    def warn_key(w):
        m = re.search(r'Line (\d+)', w)
        return int(m.group(1)) if m else 0
    all_warnings.sort(key=warn_key)
    
    return all_entries, all_warnings

def aggregate_bom(entries: list[dict]) -> dict:
    """Aggregates identical BOM entries and groups them by category.
    
    Identical items are matched by name (case-insensitive) and category.
    Quantities are summed.
    Groups are sorted alphabetically by name.
    """
    aggregated = {}
    
    for entry in entries:
        name = entry["name"]
        category = entry["category"].lower()
        key = (name.lower(), category)
        
        if key not in aggregated:
            aggregated[key] = {
                "name": name,
                "qty": 0,
                "category": category
            }
            if "supplier" in entry:
                aggregated[key]["supplier"] = entry["supplier"]
            if "part_number" in entry:
                aggregated[key]["part_number"] = entry["part_number"]
                
        aggregated[key]["qty"] += entry["qty"]
        
    categories: dict[str, list[dict]] = {}
    total_quantity = 0
    total_unique_items = len(aggregated)
    
    for item in aggregated.values():
        cat = item["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
        total_quantity += item["qty"]
        
    for cat in categories:
        categories[cat].sort(key=lambda x: x["name"].lower())
        
    return {
        "categories": categories,
        "summary": {
            "total_unique_items": total_unique_items,
            "total_quantity": total_quantity
        }
    }

import json
import csv

def export_bom_json(aggregated: dict, output_path: str):
    """Exports aggregated BOM to JSON format."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(aggregated, f, indent=2)

def export_bom_markdown(aggregated: dict, output_path: str):
    """Exports aggregated BOM to a Markdown table."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Bill of Materials\n\n")
        for cat in sorted(aggregated["categories"].keys()):
            items = aggregated["categories"][cat]
            f.write(f"## {cat}\n\n")
            f.write("| Category | Part Name | Qty | Supplier | Part # |\n")
            f.write("| --- | --- | --- | --- | --- |\n")
            for item in items:
                sup = item.get("supplier", "")
                pnum = item.get("part_number", "")
                f.write(f"| {cat} | {item['name']} | {item['qty']} | {sup} | {pnum} |\n")
            f.write("\n")

def export_bom_csv(aggregated: dict, output_path: str):
    """Exports aggregated BOM to CSV format."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["category", "name", "qty", "supplier", "part_number"])
        for cat in sorted(aggregated["categories"].keys()):
            items = aggregated["categories"][cat]
            for item in items:
                sup = item.get("supplier", "")
                pnum = item.get("part_number", "")
                writer.writerow([cat, item["name"], item["qty"], sup, pnum])


def export_bom(aggregated: dict, output_dir: str | None = None, formats: list | None = None) -> dict[str, str]:
    """Unified exporter to write BOM in multiple formats to output_dir.
    
    Returns:
        dict mapping format -> absolute file path.
    """
    if output_dir is None:
        output_dir = os.path.expanduser("~/.openscad_bom/")
        
    os.makedirs(output_dir, exist_ok=True)
    
    if formats is None:
        formats = ["json", "md", "csv"]
        
    paths = {}
    
    if "json" in formats:
        json_path = os.path.abspath(os.path.join(output_dir, "bom.json"))
        export_bom_json(aggregated, json_path)
        paths["json"] = json_path
        
    if "md" in formats:
        md_path = os.path.abspath(os.path.join(output_dir, "bom.md"))
        export_bom_markdown(aggregated, md_path)
        paths["md"] = md_path
        
    if "csv" in formats:
        csv_path = os.path.abspath(os.path.join(output_dir, "bom.csv"))
        export_bom_csv(aggregated, csv_path)
        paths["csv"] = csv_path
        
    return paths
