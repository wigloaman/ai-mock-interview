from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserProfileForm
from interview import models


def index(request):
    context = {
    }
    return render(request, 'interview/index.html', context)


@login_required
def view_profile(request):
    userprofile, _ = models.UserProfile.objects.get_or_create(user=request.user)
    context = {"user": request.user,
               "userprofile": userprofile
               }
    return render(request, 'interview/view_profile.html', context)


@login_required
def update_profile(request):
    userprofile, _ = models.UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=userprofile)
        if form.is_valid():
            form.save()
            return redirect("interview:view_profile")
    else:
        form = UserProfileForm(instance=userprofile)
    return render(request, 'interview/edit_profile.html', {'form': form})
