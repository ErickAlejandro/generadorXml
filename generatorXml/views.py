from django.shortcuts import render

# Create your views here.
def view_generator(request):
    context = {
        "message": "funciona"
    }
    return render(request, "view_generator.html", context)