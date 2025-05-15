import csv

input_file = '/Users/kirthika/Desktop/uniapp/university-app/backend/csv/REC.csv'
output_file = '/Users/kirthika/Desktop/uniapp/university-app/backend/csv/converted_students.csv'
default_password = 'changeme@123'

with open(input_file, newline='', encoding='utf-8-sig') as infile, open(output_file, 'w', newline='', encoding='utf-8') as outfile:
    reader = csv.DictReader(infile)
    fieldnames = ['name', 'email', 'password', 'user_type']
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        first_name = row['student_id__first_name'].strip()
        last_name = row['student_id__last_name'].strip()
        name = f"{first_name} {last_name}".strip()
        email = row['student_id__email'].strip()

        writer.writerow({
            'name': name,
            'email': email,
            'password': default_password,
            'user_type': 'student'
        })

print(f"✅ Converted {input_file} to {output_file}")
