# import csv
# import pandas as pd
# from pathlib import Path

# # Paths
# script_dir = Path(__file__).resolve().parent
# teachers_csv_path = script_dir / 'teachers.csv'  # Ensure this file exists in the same folder
# output_file = script_dir / 'departments.csv'

# # Mapping of known department name variants to their correct form
# department_corrections = {
#     "CSE": "Computer Science & Engineering",
#     "ECE": "Electronics & Communication Engineering",
#     "EEE": "Electrical & Electronics Engineering",
#     "IT": "Information Technology",
#     "MECH": "Mechanical Engineering",
#     "AI-DS": "Artificial Intelligence & Data Science",
#     "AI-ML": "Artificial Intelligence & Machine Learning",
#     "CSBS": "Computer Science & Business Systems",
#     "CS": "Computer Science & Engineering",
#     "CIVIL": "Civil Engineering",
#     "CSD": "Computer Science & Design",
#     "MATHS": "Mathematics",
#     "AERO": "Aeronautical Engineering",
#     "PHYSICS": "Physics",
#     "CHEMISTRY": "Chemistry",
#     "BIO": "Biotechnology",
#     "BIO-MED": "Biomedical Engineering",
#     "AUTO": "Automobile Engineering",
#     "MECHATRONICS": "Mechatronics Engineering",
#     "ROBOTICS AND AUTOMATION": "Robotics & Automation",
#     "ROBOTICS": "Robotics & Automation",
#     "HUMANITIES": "Humanities & Sciences",
#     "MANAGEMENT": "Management Studies",
#     "FOOD TECH": "Food Technology",
#     "CIVIL ENGG.": "Civil Engineering",
#     "BIO MEDICAL": "Biomedical Engineering",
#     "BIO TECH": "Biotechnology",
#     "CHEMICAL": "Chemical Engineering",
#     "CHEMISTRY": "Chemistry",
#     "ENGLISH": "English",
#     "HUMANITIES & SCIENCES": "Humanities & Sciences",
#     "MANAGEMENT STUDIES": "Management Studies",
#     "ROBOTICS & AUTOMATION": "Robotics & Automation",
#     "CSBS": "Computer Science & Business Systems",
#     "CSE Cyber Security": "Computer Science & Engineering (Cyber Security)",
#     "IT": "Information Technology",
#     "MBA": "Management Studies",
#     "MCT": "Mechatronics Engineering",
#     "MECHANICAL": "Mechanical Engineering",
#     "PED": "Physical Education",
#     # Add more corrections if needed
# }

# # Base departments
# base_departments = [
#     "Aeronautical Engineering",
#     "Automobile Engineering",
#     "Biomedical Engineering",
#     "Biotechnology",
#     "Chemical Engineering",
#     "Civil Engineering",
#     "Computer Science & Engineering",
#     "Electrical & Electronics Engineering",
#     "Electronics & Communication Engineering",
#     "Food Technology",
#     "Information Technology",
#     "Artificial Intelligence & Machine Learning",
#     "Artificial Intelligence & Data Science",
#     "Computer Science & Design",
#     "Computer Science & Business Systems",
#     "Computer Science & Engineering (Cyber Security)",
#     "Mechanical Engineering",
#     "Mechatronics Engineering",
#     "Robotics & Automation",
#     "Humanities & Sciences",
#     "Management Studies"
# ]

# # Extra departments to add
# extra_departments = ["Mathematics", "Physics", "Chemistry", "English"]

# # Load and normalize teacher departments
# teacher_departments = []
# try:
#     df = pd.read_csv(teachers_csv_path)
#     raw_departments = df['department_name'].dropna().unique().tolist()
#     for dept in raw_departments:
#         dept = dept.strip()
#         corrected = department_corrections.get(dept, dept)  # Normalize if mapping exists
#         teacher_departments.append(corrected)
# except Exception as e:
#     print("⚠️ Could not read teachers.csv:", e)

# # Merge all unique departments
# all_departments = set(base_departments + extra_departments + teacher_departments)

# # Contact info
# contact_info = (
#     "Rajalakshmi Engineering College, Rajalakshmi Nagar, Thandalam, "
#     "Chennai - 602 105. Phone: +91-44-67181111, 67181112. "
#     "Email: admin@rajalakshmi.edu.in"
# )

# # Write to departments.csv
# with output_file.open(mode='w', newline='', encoding='utf-8') as file:
#     writer = csv.DictWriter(file, fieldnames=['dept_name', 'date_established', 'contact_info'])
#     writer.writeheader()
#     for dept in sorted(all_departments):
#         writer.writerow({
#             'dept_name': dept,
#             'date_established': '2000',  # Replace 'YYYY' with actual data if needed
#             'contact_info': contact_info
#         })

# print(f"✅ departments.csv has been created successfully at: {output_file}")


# --------------------
# import csv
# import pandas as pd
# from pathlib import Path

# # Paths
# script_dir = Path(__file__).resolve().parent
# teachers_csv_path = script_dir / 'teachers.csv'
# updated_teachers_csv_path = script_dir / 'teachers_updated.csv'  # You can overwrite if needed

# # Department name corrections
# department_corrections = {
#     "CSE": "Computer Science & Engineering",
#     "ECE": "Electronics & Communication Engineering",
#     "EEE": "Electrical & Electronics Engineering",
#     "IT": "Information Technology",
#     "MECH": "Mechanical Engineering",
#     "AI-DS": "Artificial Intelligence & Data Science",
#     "AI-ML": "Artificial Intelligence & Machine Learning",
#     "CSBS": "Computer Science & Business Systems",
#     "CS": "Computer Science & Engineering",
#     "CIVIL": "Civil Engineering",
#     "CSD": "Computer Science & Design",
#     "MATHS": "Mathematics",
#     "AERO": "Aeronautical Engineering",
#     "PHYSICS": "Physics",
#     "CHEMISTRY": "Chemistry",
#     "BIO": "Biotechnology",
#     "BIO-MED": "Biomedical Engineering",
#     "AUTO": "Automobile Engineering",
#     "MECHATRONICS": "Mechatronics Engineering",
#     "ROBOTICS AND AUTOMATION": "Robotics & Automation",
#     "ROBOTICS": "Robotics & Automation",
#     "HUMANITIES": "Humanities & Sciences",
#     "MANAGEMENT": "Management Studies",
#     "FOOD TECH": "Food Technology",
#     "CIVIL ENGG.": "Civil Engineering",
#     "BIO MEDICAL": "Biomedical Engineering",
#     "BIO TECH": "Biotechnology",
#     "CHEMICAL": "Chemical Engineering",
#     "ENGLISH": "English",
#     "HUMANITIES & SCIENCES": "Humanities & Sciences",
#     "MANAGEMENT STUDIES": "Management Studies",
#     "ROBOTICS & AUTOMATION": "Robotics & Automation",
#     "CSE Cyber Security": "Computer Science & Engineering (Cyber Security)",
#     "MBA": "Management Studies",
#     "MCT": "Mechatronics Engineering",
#     "MECHANICAL": "Mechanical Engineering",
#     "PED": "Physical Education"
# }

# # Load CSV
# try:
#     df = pd.read_csv(teachers_csv_path)

#     if 'department_name' not in df.columns:
#         raise KeyError("The column 'department_name' is not found in teachers.csv")

#     # Replace department names
#     df['department_name'] = df['department_name'].apply(
#         lambda dept: department_corrections.get(dept.strip(), dept.strip()) if pd.notna(dept) else dept
#     )

#     # Save the updated file (overwrite or new)
#     df.to_csv(updated_teachers_csv_path, index=False)
#     print(f"✅ teachers_updated.csv has been saved at: {updated_teachers_csv_path}")

# except Exception as e:
#     print(f"⚠️ Failed to update teachers.csv: {e}")

# --------------------

# import csv
# from pathlib import Path

# # Determine the directory where the script is located
# script_dir = Path(__file__).resolve().parent
# output_file = script_dir / 'departments.csv'

# # List of departments
# departments = [
#     "Aeronautical Engineering",
#     "Automobile Engineering",
#     "Biomedical Engineering",
#     "Biotechnology",
#     "Chemical Engineering",
#     "Civil Engineering",
#     "Computer Science & Engineering",
#     "Electrical & Electronics Engineering",
#     "Electronics & Communication Engineering",
#     "Food Technology",
#     "Information Technology",
#     "Artificial Intelligence & Machine Learning",
#     "Artificial Intelligence & Data Science",
#     "Computer Science & Design",
#     "Computer Science & Business Systems",
#     "Computer Science & Engineering (Cyber Security)",
#     "Mechanical Engineering",
#     "Mechatronics Engineering",
#     "Robotics & Automation",
#     "Humanities & Sciences",
#     "Management Studies"
# ]

# # College contact information
# college_contact_info = (
#     "Rajalakshmi Engineering College, Rajalakshmi Nagar, Thandalam, "
#     "Chennai - 602 105. Phone: +91-44-67181111, 67181112. "
#     "Email: admin@rajalakshmi.edu.in"
# )

# # Create and write to the CSV file
# with output_file.open(mode='w', newline='', encoding='utf-8') as file:
#     writer = csv.DictWriter(file, fieldnames=['dept_name', 'date_established', 'contact_info'])
#     writer.writeheader()
#     for dept in departments:
#         writer.writerow({
#             'dept_name': dept,
#             'date_established': 'YYYY',  # Replace 'YYYY' with the actual year of establishment
#             'contact_info': college_contact_info
#         })

# print(f"✅ departments.csv has been created successfully at: {output_file}")

import pandas as pd
from pathlib import Path

# Paths
script_dir = Path(__file__).resolve().parent
teachers_csv_path = script_dir / 'teachers.csv'
updated_teachers_csv_path = script_dir / 'teachers_updated.csv'

# Valid choices for roles and availability
VALID_TEACHER_ROLES = {
    'Professor', 'Asst. Professor', 'HOD', 'DC', 'POP', 'Professor of Practice', 'Industry Professional'
}
VALID_AVAILABILITY_TYPES = {'regular', 'limited'}

# Department correction mapping
department_corrections = {
    "CSE": "Computer Science & Engineering",
    "ECE": "Electronics & Communication Engineering",
    "EEE": "Electrical & Electronics Engineering",
    "IT": "Information Technology",
    "MECH": "Mechanical Engineering",
    "AI-DS": "Artificial Intelligence & Data Science",
    "AI-ML": "Artificial Intelligence & Machine Learning",
    "CSBS": "Computer Science & Business Systems",
    "CS": "Computer Science & Engineering",
    "CIVIL": "Civil Engineering",
    "CSD": "Computer Science & Design",
    "MATHS": "Mathematics",
    "AERO": "Aeronautical Engineering",
    "PHYSICS": "Physics",
    "CHEMISTRY": "Chemistry",
    "BIO": "Biotechnology",
    "BIO-MED": "Biomedical Engineering",
    "AUTO": "Automobile Engineering",
    "MECHATRONICS": "Mechatronics Engineering",
    "ROBOTICS AND AUTOMATION": "Robotics & Automation",
    "ROBOTICS": "Robotics & Automation",
    "HUMANITIES": "Humanities & Sciences",
    "MANAGEMENT": "Management Studies",
    "FOOD TECH": "Food Technology",
    "CIVIL ENGG.": "Civil Engineering",
    "BIO MEDICAL": "Biomedical Engineering",
    "BIO TECH": "Biotechnology",
    "CHEMICAL": "Chemical Engineering",
    "ENGLISH": "English",
    "HUMANITIES & SCIENCES": "Humanities & Sciences",
    "MANAGEMENT STUDIES": "Management Studies",
    "ROBOTICS & AUTOMATION": "Robotics & Automation",
    "CSE Cyber Security": "Computer Science & Engineering (Cyber Security)",
    "MBA": "Management Studies",
    "MCT": "Mechatronics Engineering",
    "MECHANICAL": "Mechanical Engineering",
    "PED": "Physical Education"
}

try:
    # Load CSV
    df = pd.read_csv(teachers_csv_path)

    # Normalize department_name
    if 'department_name' in df.columns:
        df['department_name'] = df['department_name'].apply(
            lambda d: department_corrections.get(str(d).strip(), str(d).strip()) if pd.notna(d) else d
        )
    else:
        df['department_name'] = ''

    # Normalize teacher_role
    if 'teacher_role' in df.columns:
        df['teacher_role'] = df['teacher_role'].apply(
            lambda r: r if r in VALID_TEACHER_ROLES else 'Professor'
        )
    else:
        df['teacher_role'] = 'Professor'

    # Normalize availability_type
    if 'availability_type' in df.columns:
        df['availability_type'] = df['availability_type'].apply(
            lambda a: a if a in VALID_AVAILABILITY_TYPES else 'regular'
        )
    else:
        df['availability_type'] = 'regular'

    # Ensure teacher_working_hours is numeric
    if 'teacher_working_hours' in df.columns:
        df['teacher_working_hours'] = pd.to_numeric(df['teacher_working_hours'], errors='coerce').fillna(21).astype(int)
    else:
        df['teacher_working_hours'] = 21

    # Add is_industry_professional
    df['is_industry_professional'] = df['teacher_role'].apply(
        lambda r: r == 'Industry Professional'
    )

    # Save updated file
    df.to_csv(updated_teachers_csv_path, index=False)
    print(f"✅ Updated teachers file saved to: {updated_teachers_csv_path}")

except Exception as e:
    print(f"⚠️ Error updating teachers.csv: {e}")
