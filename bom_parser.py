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
