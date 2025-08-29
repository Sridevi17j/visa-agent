VISA_TYPES = {
    "tourist": ["single_entry", "multiple_entry"],
    "business": ["single_entry", "multiple_entry"], 
    "transit": ["single_entry"],
    "student": ["single_entry"],
    "work": ["single_entry", "multiple_entry"]
}

# Combined visa types for user selection
COMBINED_VISA_TYPES = []
for visa_category, entry_types in VISA_TYPES.items():
    for entry_type in entry_types:
        COMBINED_VISA_TYPES.append(f"{visa_category}_{entry_type}")
