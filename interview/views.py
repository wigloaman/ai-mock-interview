from django.shortcuts import render


def index(request):
    context = {
    }
    return render(request, 'interview/index.html', context)
