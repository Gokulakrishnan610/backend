import pandas as pd
# Load original uploaded CSVs
rooms_df = pd.read_csv('/Users/kirthika/Desktop/uniapp/university-app/backend/co.csv')
co_df = pd.read_csv('/Users/kirthika/Desktop/uniapp/university-app/backend/co.csv')


# --- Step 1: Clean columns: Remove spaces and newlines ---
co_df.columns = co_df.columns.str.strip().str.replace('\n', '', regex=True)

# --- Step 3: Fix CourseMaster (CO) CSV ---

# Rename fields if necessary
co_df.rename(columns={
    'Course dept id': 'course_dept_id'
}, inplace=True)

# Check if required CO fields are present
required_co_columns = [
    'course_id', 'course_name', 'course_dept_id', 'credits',
    'lecture_hours', 'practical_hours', 'tutorial_hours',
    'regulation', 'course_type'
]

missing_co = [col for col in required_co_columns if col not in co_df.columns]

if missing_co:
    raise ValueError(f"❌ Missing columns in co.csv: {missing_co}")

# Create corrected CO DataFrame
corrected_co = pd.DataFrame({
    'id': range(1, len(co_df) + 1),
    'course_id': co_df['course_id'],
    'course_name': co_df['course_name'],
    'course_dept_id': co_df['course_dept_id'],
    'credits': co_df['credits'],
    'lecture_hours': co_df['lecture_hours'],
    'practical_hours': co_df['practical_hours'],
    'tutorial_hours': co_df['tutorial_hours'],
    'regulation': co_df['regulation'],
    'course_type': co_df['course_type'],
})

# Save corrected_co.csv
corrected_co.to_csv('corrected_co.csv', index=False)
print("✅ CO (CourseMaster) CSV corrected and saved as corrected_co.csv")
