from typing import Any
from datetime import datetime, timedelta
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect
from django.http import HttpResponse
from inventory.models import MenuItem, Ingredient, RecipeRequirement, Purchase, Profile
from .forms import PurchaseForm, IngredientForm, MenuItemForm, RecipeRequirementForm, ProfileForm, SignUpForm # Assuming you have a form for purchase details
from django.views.generic import TemplateView, ListView, DetailView
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, OuterRef, Subquery
from django.views.generic.edit import DeleteView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView



# Create your views here.
 #login our customer
class HomeView(LoginRequiredMixin, TemplateView):
   template_name = 'inventory/home.html'

   def get_context_data(self):
       context = super().get_context_data()
       context["ingredients"] = Ingredient.objects.all()
       context["menu"] = MenuItem.objects.all()
       context["purchase"] = Purchase.objects.all()
       context["reciperequirement"] = RecipeRequirement.objects.all()
       return context
   


#
# If the request method is POST, validates the form data and creates a new user.
# The form contains username, email, and password fields. 
# After successful validation, the user is logged in automatically.
#
# If the request method is GET, displays a blank registration form.
def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            #we create the user object
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1') #Hash password
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('inventory/.html')
    else:
         form = SignUpForm()
    return render(request, 'games/register.html', {'form': form}) 



# Login view

class LoginView(LoginView):
    template_name = 'inventory/log_in.html'
    success_url = reverse_lazy("home")
    extra_context = {'login': 'active'}

    def get_success_url(self):
        return self.success_url

    def form_invalid(self, form):
        return HttpResponse("Invalid credentials")
    

def logout_request(request):
    logout(request)
    return redirect("home")
    




# all Listviews below   
    
# this is a view that will show a list of ingredient
class IngredientsList(LoginRequiredMixin,ListView):
    model = Ingredient
    template_name = 'inventory/ingredients-list.html'
    context_object_name = 'ingredients'

    def get_queryset(self):
        return Ingredient.objects.all()


# this view will show the menu items
class MenuItemView(LoginRequiredMixin,ListView):
    model = MenuItem
    template_name = 'inventory/menu.html'
    context_object_name = 'menu'


    def get_queryset(self):
        return MenuItem.objects.all()

    

# this view shows the purchses made 
class PurchaseList(LoginRequiredMixin,ListView):
    model = Purchase
    template_name = 'inventory/purchase-list.html'
    context_object_name = 'purchases'




# all createview below

class MenuItemCreate(CreateView):
    model = MenuItem
    form_class = MenuItemForm
    template_name = 'inventory/menu_create.html'


class PurchaseCreate(CreateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = 'inventory/purchase_create.html'
    success_url = reverse_lazy('purchase-list')


class IngredientCreate(CreateView):
    model = Ingredient
    form_class = IngredientForm
    template_name = 'inventory/ingredient_create.html'
    success_url = reverse_lazy('ingredientslist')


class RecipeRequirementCreate(LoginRequiredMixin,CreateView):
    model = RecipeRequirement
    form_class = RecipeRequirementForm
    template_name = 'inventory/reciperequirement_create.html'
    success_url = reverse_lazy("menuitem")


class ProfileCreate(LoginRequiredMixin,CreateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'inventory/profile.html'




#All Updateview
    
class IngredientUpdate(UpdateView):
  model = Ingredient
  template_name = "inventory/ingredient_update_form.html"
  form_class = IngredientForm
  success_url = reverse_lazy('ingredientslist')



#All Deleteview
class IngredientDelete(DeleteView):
    model = Ingredient
    template_name = 'inventory/ingredient_delete_form.html'
    success_url = reverse_lazy('ingredientslist')



class MenuItemDelete(DeleteView):
    model = MenuItem
    template_name = 'inventory/menuitem_delete_form.html'
    success_url = reverse_lazy ('menuitem')




  # decreasing ingredient.quantity because ingredients were used for the purchased menu_item, have to finish the automatic subtractions in the inventory ingredients
    
def form_valid(self, form):
    item = form.save(commit=False) #we have changed to True from False
    menu_item = MenuItem.objects.get(id = item.menu_item.id)
    recipe_requirements = RecipeRequirement.objects.filter(menu_item = menu_item)
    errors_list = []
    print(menu_item)

    for i in recipe_requirements:
      if (i.ingredient.quantity - i.quantity) >= 0:
        print(i)
      else:
        errors_list.append(i.ingredient.name)
    if (errors_list.__len__() == 0):
      i.ingredient.quantity -= i.quantity
      i.ingredient.save()
      item.save()
      messages.success(self.request, "successful") #i removed the # to see what happens
      return super(PurchaseCreate, self).form_valid(form)
    else:
      error_string = ", ".join(errors_list)
      messages.error(self.request, f"not enough ingredients in the inventory! ({error_string})")
      return self.render_to_response(self.get_context_data(form=form))
    




# function for profit and revenue calculation
@login_required
def profit_revenue(request):
    context = {}
    context["menu"] = MenuItem.objects.all()
    context["purchase"] = Purchase.objects.all()

    # Calculate total revenue
    total_revenue = Purchase.objects.aggregate(
        total_revenue=Sum('menu_item__price')
    )['total_revenue'] or 0  # Ensure None is handled

    # Subquery to calculate the total ingredient cost for each menu item
    ingredient_cost_subquery = RecipeRequirement.objects.filter(
        menu_item=OuterRef('menu_item_id')
    ).annotate(
        total_cost=Sum(F('quantity') * F('ingredient__price_per_unit'))
    ).values('total_cost')

    # Annotate purchases with ingredient costs
    purchases_with_costs = Purchase.objects.annotate(
        ingredient_cost=Subquery(ingredient_cost_subquery)
    )

    # Calculate total profit
    total_profit = purchases_with_costs.aggregate(
        total_profit=Sum(F('menu_item__price') - F('ingredient_cost'))
    )['total_profit'] or 0  # Ensure None is handled

    context["total_revenue"] = total_revenue
    context["total_profit"] = total_profit
    context["purchase"] = purchases_with_costs


    return render(request, "inventory/profit_revenue.html", context)
        


class IngredientDetail(LoginRequiredMixin,DetailView):
    model = Ingredient
    template_name = "inventory/ingredient_details.html"
    
    def get_context_data(self, **kwargs):
        context = super(IngredientDetail,self).get_context_data(**kwargs)
        context['object'] = self.object
        ingredient = Ingredient.objects.get(id=context['object'].pk)
        recipe_requirements_list = []
        for item in context['object'].reciperequirement_set.all():
            recipe_requirements_list.append(item)
        context = {
           'ingredient':ingredient,
           'recipe_requirements_list': recipe_requirements_list
        }
        return context


class MenuItemDetail(DetailView):
    model = MenuItem
    template_name = "inventory/menuitem_detail.html"

    def get_context_data(self, **kwargs):
        context = super(MenuItemDetail, self).get_context_data(**kwargs)
        menuitem = self.object
        recipe_requirements = RecipeRequirement.objects.filter(menu_item=menuitem).distinct()
        context['recipe_requirements_list'] = recipe_requirements
        return context


