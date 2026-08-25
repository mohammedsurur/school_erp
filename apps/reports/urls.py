# apps/reports/urls.py

from django.urls import path
from . import views

urlpatterns = [

    path('',                    views.reports_dashboard,   name='reports_dashboard'),
    path('report-card/',        views.report_card,         name='report_card'),
    path('exam-results/',       views.exam_results,        name='exam_results'),
    path('attendance/',         views.attendance_report,   name='attendance_report'),
    path('fee-collection/',     views.fee_collection,      name='fee_collection'),
    path('outstanding-fees/',   views.outstanding_fees,    name='outstanding_fees'),
    path('library/',            views.library_report,      name='library_report'),
    path('transport/',          views.transport_report,    name='transport_report'),
    path('students/',           views.student_list_report, name='student_list_report'),
    path('staff/',              views.staff_list_report,   name='staff_list_report'),
    path('history/',            views.report_history,      name='report_history'),

    # Print / Download
    path('download/<str:report_type>/', views.download_pdf,   name='download_pdf'),
    path('print/<str:report_type>/',    views.print_report,    name='print_report'),
]