from typing import Any
from datetime import datetime, timedelta
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect
from django.http import HttpResponse
from inventory.models import MenuItem, Ingredient, RecipeRequirement, Purchase, Profile
from .forms import PurchaseForm, IngredientForm, MenuItemForm, RecipeRequirementForm, ProfileForm, SignUpForm 
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
from django.views import View


# Create your views here.
 #login our customer
class HomeView(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            "name": request.user,
            "ingredients": Ingredient.objects.all(),
            "menu": MenuItem.objects.all(),
            "purchase": Purchase.objects.all(),
            "reciperequirement": RecipeRequirement.objects.all(),
        }
        return render(request, 'inventory/home.html', context)


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
            user = form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Account created for {username}. You are now logged in.')
                return redirect(reverse('home'))  # Assuming you have a named URL pattern
            else:
                messages.error(request, 'An error occurred during registration. Please try again.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignUpForm()
    return render(request, 'inventory/register.html', {'form': form})



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


# this view shows the purchases made 
class PurchaseList(LoginRequiredMixin,ListView):
    model = Purchase
    template_name = 'inventory/purchase-list.html'
    context_object_name = 'purchases'



  # decreasing ingredient.quantity because ingredients were used for the purchased menu_item, have to finish the automatic subtractions in the inventory ingredients

def form_valid(self, form):
    item = form.save(commit=False)
    menu_item = MenuItem.objects.get(id=item.menu_item.id)
    recipe_requirements = RecipeRequirement.objects.filter(menu_item=menu_item)
    errors_list = []

    try:
        with transaction.atomic():
            for requirement in recipe_requirements:
                if requirement.ingredient.quantity < requirement.quantity:
                    errors_list.append(requirement.ingredient.name)
                    
            if errors_list:
                error_string = ", ".join(errors_list)
                raise ValueError(f"Not enough ingredients in the inventory! ({error_string})")

            # Update ingredient quantities
            for requirement in recipe_requirements:
                requirement.ingredient.quantity = F('quantity') - requirement.quantity
                requirement.ingredient.save()

            item.save()

    except ValueError as e:
        messages.error(self.request, str(e))
        return self.render_to_response(self.get_context_data(form=form))

    messages.success(self.request, "Purchase successful")
    return super(PurchaseCreate, self).form_valid(form)
    




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


class Register(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "inventory/register.html"




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
        


class IngredientDetail(LoginRequiredMixin, DetailView):
    # This view displays details of a single Ingredient object
    
    # Specify the model this view is associated with
    model = Ingredient
    
    # Specify the template to be used for rendering this view
    template_name = "inventory/ingredient_details.html"
    
    def get_context_data(self, **kwargs):
        # Override the get_context_data method to customize the context
        # sent to the template
        
        # Call the parent class's get_context_data to get the default context
        context = super().get_context_data(**kwargs)
        
        # Add the list of related RecipeRequirement objects to the context
        # self.object refers to the current Ingredient instance
        # reciperequirement_set is a reverse relation to all RecipeRequirement
        # objects that reference this Ingredient
        context['recipe_requirements_list'] = self.object.reciperequirement_set.all()
        
        # Return the updated context
        return context

    # Note: In the template, you can now access:
    # - {{ object }} or {{ ingredient }} to get the Ingredient instance
    # - {{ recipe_requirements_list }} to get all related RecipeRequirement objects


class MenuItemDetail(DetailView):
    model = MenuItem
    template_name = "inventory/menuitem_detail.html"

    def get_context_data(self, **kwargs):
        context = super(MenuItemDetail, self).get_context_data(**kwargs)
        menuitem = self.object
        recipe_requirements = RecipeRequirement.objects.filter(menu_item=menuitem).distinct()
        context['recipe_requirements_list'] = recipe_requirements
        return context


