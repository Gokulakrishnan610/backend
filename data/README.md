# University App Database Seeding

This directory contains data files and seeding utilities for the University App.

## Data Files

The following CSV files are used to seed the database with real data:

- `app_users.csv`: User accounts for students and teachers
- `departments.csv`: Academic departments
- `teachers.csv`: Teacher profiles
- `courses.csv`: Course information
- `rooms.csv`: Room information

## Seeding Commands

### Import CSV Data

To import data from the CSV files:

```bash
python manage.py import_data
```

This will import departments, users, teachers, courses, and rooms from the CSV files.

### Seed Fake Data

To seed the database with fake data for all models:

```bash
python manage.py seed_data
```

This command:
1. First runs the `import_data` command to import real data from CSV files
2. Creates additional users if needed
3. Creates student profiles for users
4. Creates course master entries
5. Creates time slots for scheduling
6. Creates teacher-course assignments
7. Creates student-course enrollments

To clear existing generated data before seeding:

```bash
python manage.py seed_data --clear
```

This will only clear data for models that are generated with fake data, not the data imported from CSV files.

## Data Model Dependencies

The seeding follows this order to respect dependencies:

1. Authentication (Users)
2. Departments
3. Teachers/Students (depends on Users and Departments)
4. Courses (depends on Departments)
5. Course Master (depends on Departments)
6. Rooms (depends on Departments)
7. Slots (independent)
8. Teacher-Course assignments (depends on Teachers and Courses)
9. Student-Course enrollments (depends on Students and Courses) 