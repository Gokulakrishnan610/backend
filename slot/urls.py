from django.urls import path
from . import views

urlpatterns = [
    path('', views.SlotListView.as_view(), name="slots-list"),
    path('teacher-slot-preference/', views.TeacherSlotPreferenceView.as_view(), name="teacher-slot-preference"),
    path('teacher-slots/', views.TeacherSlotListView.as_view(), name="teacher-slots-list"),
    path('department-summary/', views.DepartmentSlotSummaryView.as_view(), name="department-slot-summary"),
    path('initialize-default-slots/', views.InitializeDefaultSlotsView.as_view(), name="initialize-default-slots"),
    path('batch-assignments/', views.BatchTeacherSlotAssignmentView.as_view(), name="batch-teacher-slot-assignments"),
]
