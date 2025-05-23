# Generated by Django 5.2 on 2025-05-13 09:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('course', '0001_initial'),
        ('teacher', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeacherCourse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_count', models.IntegerField(default=0, verbose_name='Student Count')),
                ('academic_year', models.IntegerField(default=0, verbose_name='Academic Year')),
                ('semester', models.IntegerField(default=0, verbose_name='Semester')),
                ('requires_special_scheduling', models.BooleanField(default=False, verbose_name='Requires Special Scheduling')),
                ('is_assistant', models.BooleanField(default=False, verbose_name='Is Assistant Teacher')),
                ('course_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='course.course')),
                ('preferred_availability_slots', models.ManyToManyField(blank=True, related_name='courses_scheduled', to='teacher.teacheravailability', verbose_name='Preferred Availability Slots')),
                ('teacher_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='teacher.teacher')),
            ],
        ),
    ]
