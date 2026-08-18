from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .models import Product

def product_list(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'store/product_list.html', {'products': products})
