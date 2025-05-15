

import pandas as pd

# Path to your input and output CSV file
input_csv_path = '/Users/kirthika/Desktop/uniapp/university-app/backend/csv/rooms.csv'       # Replace with your actual path
output_csv_path = '/Users/kirthika/Desktop/uniapp/university-app/backend/csv/updated_rooms.csv'  # Or overwrite input_csv_path

# Load the CSV into a DataFrame
df = pd.read_csv(input_csv_path)

# Check if 'course_name' column exists
if 'maintained_by_id' not in df.columns:
    raise KeyError("The column 'course_name' does not exist in the CSV.")

# Replace " and " with " & " in the 'course_name' column
df['maintained_by_id'] = df['maintained_by_id'].str.replace(r'\band\b', '&', regex=True)

# Save the updated DataFrame to a new CSV
df.to_csv(output_csv_path, index=False)

print(f"Updated CSV saved to {output_csv_path}")
