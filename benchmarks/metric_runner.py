import json
import argparse
import sys
from pathlib import Path

def load_json(file_path):
    """Safely load a JSON file and handle common errors."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in file - {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        sys.exit(1)

def main():
    # 6. Accept command-line arguments
    parser = argparse.ArgumentParser(description="Calculate Schema Field Extraction and Type Inference Accuracy.")
    parser.add_argument("--analyzer", required=True, help="Path to the system-generated analyzer schema JSON.")
    parser.add_argument("--groundtruth", required=True, help="Path to the ground truth schema JSON.")
    parser.add_argument("--output", required=True, help="Path to save the output results JSON.")
    
    args = parser.parse_args()
    
    # 1. Load both JSON schema files
    analyzer_schema = load_json(args.analyzer)
    groundtruth_schema = load_json(args.groundtruth)
    
    # 2. Compare the "properties" section
    analyzer_props = analyzer_schema.get("properties", {})
    groundtruth_props = groundtruth_schema.get("properties", {})
    
    fields_total = len(groundtruth_props)
    
    if fields_total == 0:
        print("Error: Ground truth schema has no fields in the 'properties' section. Cannot divide by zero.")
        sys.exit(1)
        
    analyzer_keys = set(analyzer_props.keys())
    groundtruth_keys = set(groundtruth_props.keys())
    
    # Calculate Field Extraction Accuracy (A_f)
    fields_correct = len(analyzer_keys.intersection(groundtruth_keys))
    a_f = fields_correct / fields_total
    
    misclassifications = []
    
    # Identify missing and extra fields
    missing_fields = groundtruth_keys - analyzer_keys
    extra_fields = analyzer_keys - groundtruth_keys
    
    for mf in missing_fields:
        misclassifications.append(f"{mf}:missing_field")
        
    for ef in extra_fields:
        misclassifications.append(f"{ef}:extra_field")
        
    # Calculate Type Inference Accuracy (A_t)
    types_correct = 0
    
    for field, gt_data in groundtruth_props.items():
        if field in analyzer_props:
            gt_type = gt_data.get("type", "unknown")
            an_type = analyzer_props[field].get("type", "unknown")
            
            if gt_type == an_type:
                types_correct += 1
            else:
                misclassifications.append(f"{field}:type_mismatch (Expected {gt_type}, Got {an_type})")
                
    a_t = types_correct / fields_total
    
    # 3. Print counts and percentages
    print(f"Fields extracted correctly: {fields_correct}/{fields_total} → A_f = {a_f*100:.1f}%")
    print(f"Types inferred correctly: {types_correct}/{fields_total} → A_t = {a_t*100:.1f}%")
    
    # 4. List misclassifications explicitly
    print("\nMisclassifications:")
    if misclassifications:
        for m in misclassifications:
            print(f"   - {m}")
    else:
        print("   - None (Perfect Match!)")
        
    # 5. Save results to output JSON
    dataset_name = Path(args.analyzer).stem.replace("_schema", "") + ".csv"
    
    results = {
        "dataset": dataset_name,
        "fields_correct": fields_correct,
        "fields_total": fields_total,
        "A_f": round(a_f, 3),
        "types_correct": types_correct,
        "types_total": fields_total,
        "A_t": round(a_t, 3),
        "misclassifications": misclassifications
    }
    
    output_path = Path(args.output)
    
    # Create parent directories if they don't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4)
        print(f"\n[+] Results successfully saved to {output_path}")
    except Exception as e:
        print(f"Error saving output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()