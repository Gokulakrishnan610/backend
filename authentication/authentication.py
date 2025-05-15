from django.conf import settings
from rest_framework import authentication, exceptions, permissions
from .models import User
import jwt

class IsAuthenticated(authentication.BaseAuthentication):
    def authenticate(self, request):
        try:
            token = request.COOKIES.get('token')
            if not token:
                raise exceptions.AuthenticationFailed('Authentication Failed')
            try:
                payload = jwt.decode(token, settings.JWT_KEY, 'HS256')
            except:
                raise exceptions.AuthenticationFailed('Authentication Failed')
            email = payload['id']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise exceptions.AuthenticationFailed('Authentication Failed')

            return (user, None)
        except:
            raise exceptions.AuthenticationFailed('Authentication Failed')
            
    def has_permission(self, request, view):
        """
        Required method when using as a permission class.
        Return True if the user is authenticated.
        """
        return bool(request.user and request.user.is_authenticated)

class CustomIsAuthenticated(permissions.BasePermission):
    """
    Dedicated permission class to check if the user is authenticated.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

class JWTCookieAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get('token')
        
        if not token:
            return None 
        try:
            payload = jwt.decode(token, settings.JWT_KEY, algorithms=['HS256'])
            email = payload['id']
            user = User.objects.get(email=email)
            return (user, None)
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')

class CheckAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        try:
            token = request.COOKIES.get('token')
            if not token:
                return (None, None)
            try:
                payload = jwt.decode(token, settings.JWT_KEY, 'HS256')
            except jwt.ExpiredSignatureError:
                return (None, None)
            email=payload['id']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return (None, None)
            return (user, None)
        except:
            return (None, None)