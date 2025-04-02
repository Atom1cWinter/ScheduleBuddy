from django.shortcuts import render


# Create your views here.

def home(request):
    return render(request, 'base/home.html')

def calendarSync(request):
    return render(request, 'base/calendarSync.html')
def courseLoad(request):
    return render(request, 'base/courseLoad.html')
def roadMap(request):
    return render(request, 'base/roadMap.html')
def waitListClearance(request):
    return render(request, 'base/waitListClearance.html')
def openSeat(request):
    return render(request, 'base/openSeat.html')
def sectionRec(request):
    return render(request, 'base/sectionRec.html')