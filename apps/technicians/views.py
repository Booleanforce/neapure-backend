from django.shortcuts import render


def technicians_dashboard(request):
    return render(request, "technicians/dashboard.html")
# Create your views here.
