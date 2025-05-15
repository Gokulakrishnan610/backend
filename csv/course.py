# import pandas as pd

# # Path to your Excel file
# excel_file = '/Users/kirthika/Desktop/uniapp/university-app/backend/csv/Master Course list.xlsx'

# # Load the Excel file
# df = pd.read_excel(excel_file, sheet_name=0)

# # Valid path to save CSV
# csv_file = '/Users/kirthika/Desktop/uniapp/university-app/backend/csv/output.csv'

# # Save as CSV
# df.to_csv(csv_file, index=False)

# print(f"Excel converted to CSV and saved at: {csv_file}")



# import pandas as pd

# # Path to your input and output CSV file
# input_csv_path = '/Users/kirthika/Desktop/uniapp/university-app/backend/csv/output.csv'       # Replace with your actual path
# output_csv_path = '/Users/kirthika/Desktop/uniapp/university-app/backend/csv/updated_courses.csv'  # Or overwrite input_csv_path

# # Load the CSV into a DataFrame
# df = pd.read_csv(input_csv_path)

# # Check if 'course_name' column exists
# if 'course_dept_id' not in df.columns:
#     raise KeyError("The column 'course_name' does not exist in the CSV.")

# # Replace " and " with " & " in the 'course_name' column
# df['course_dept_id'] = df['course_dept_id'].str.replace(r'\band\b', '&', regex=True)

# # Save the updated DataFrame to a new CSV
# df.to_csv(output_csv_path, index=False)

# print(f"Updated CSV saved to {output_csv_path}")
