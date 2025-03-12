from django.http import HttpResponse
from django.shortcuts import render
from django.views import View


# Create your views here.
class HelloWorldView(View):
    """
    A simple HelloWorld view class that returns a greeting message
    """
    def get(self, request, *args, **kwargs):
        return HttpResponse("Hello, World!")
