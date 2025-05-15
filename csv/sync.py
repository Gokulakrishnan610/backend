import csv

old_file = '/Users/kirthika/Desktop/uniapp/university-app/backend/data/teachers.csv'
new_file = '/Users/kirthika/Desktop/uniapp/university-app/backend/csv/updated_data/teachers.csv'
output_file = '/Users/kirthika/Desktop/uniapp/university-app/backend/csv/updated_data/updated_teachers_synced.csv'

# Step 1: Load old roles by email
old_roles = {}
with open(old_file, newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        email = row['email'].strip()
        role = row['role'].strip()
        old_roles[email] = role

# Step 2: Read and update new file
with open(new_file, newline='', encoding='utf-8-sig') as f_in, open(output_file, 'w', newline='', encoding='utf-8') as f_out:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        email = row['email'].strip()
        if email in old_roles:
            row['teacher_role'] = old_roles[email]
        writer.writerow(row)

print(f"✅ teacher_role values updated and saved to {output_file}")


