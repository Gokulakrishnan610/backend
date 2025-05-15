from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from utlis.import_csv import import_from_csv

from course.resources import CourseResource
from courseMaster.resources import CourseMasterResource

class ImportDataView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, resource_name):
        RESOURCE_MAPPING = {
            'course': CourseResource,
            'course-master': CourseMasterResource
        }

        if resource_name not in RESOURCE_MAPPING:
            return Response(
                {"error": f"Resource '{resource_name}' not found"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if 'file' not in request.FILES:
            return Response(
                {"error": "No file uploaded"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            dry_run = request.data.get('dry_run', 'false').lower() == 'true'
            
            result, errors = import_from_csv(
                RESOURCE_MAPPING[resource_name],
                request.FILES['file'],
                dry_run=dry_run
            )
            
            response_data = {
                "success": not result.has_errors(),
                "rows_processed": result.total_rows,
                "rows_imported": result.totals.get('new', 0) + result.totals.get('update', 0),
                "dry_run": dry_run,
                "errors": errors
            }
            
            status_code = status.HTTP_200_OK if not errors else status.HTTP_206_PARTIAL_CONTENT
            
            return Response(response_data, status=status_code)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )