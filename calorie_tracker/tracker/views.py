import os
import requests
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("CALORIE_NINJAS_API_KEY")


from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Food, Consume, CalorieGoal
from django.utils.timezone import now
from datetime import date
from django.db.models import Sum
from django.urls import reverse

# Registration
def register(request):
    form = UserCreationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('dashboard')
    return render(request, 'tracker/register.html', {'form': form})

# Login
def login_view(request):
    form = AuthenticationForm(data=request.POST or None)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('dashboard')
    return render(request, 'tracker/login.html', {'form': form})

# Logout
def logout_view(request):
    logout(request)
    return redirect('login')


# ✅ Main Dashboard
@login_required
def dashboard(request):
    today = date.today()

    # 1. Ensure goal is set
    try:
        goal_obj = CalorieGoal.objects.get(user=request.user)
    except CalorieGoal.DoesNotExist:
        return redirect('set_goal')
    
    goal = goal_obj.goal  # safe to use now

    # 2. Get today's items + total
    consumed_items = Consume.objects.filter(user=request.user, date=today)
    total_calories = consumed_items.aggregate(total=Sum('food__calories'))['total'] or 0

    # 3. Calculate goal status
    goal_reached = total_calories >= goal

    # 4. Prepare chart data
    chart_data = consumed_items.values('food__name').annotate(total=Sum('food__calories'))
    food_names = [item['food__name'].title() for item in chart_data]
    calorie_values = [item['total'] for item in chart_data]

    if goal_reached and not request.session.get('goal_viewed'):
        request.session['goal_viewed'] = True
        return redirect('goal_reached')


    # 5. Handle food entry
    if request.method == "POST":
        food_name = request.POST['food_name'].strip().lower()

        url = f"https://api.calorieninjas.com/v1/nutrition?query={food_name}"
        response = requests.get(url, headers={'X-Api-Key': API_KEY})

        food = None
        if response.status_code == 200:
            items = response.json().get('items')
            if items:
                calories = int(items[0]['calories'])
                food, _ = Food.objects.get_or_create(
                    name=food_name, defaults={'calories': calories, 'user': None}
                )

        # Fallback to local DB
        if not food:
            food = Food.objects.filter(name__iexact=food_name, user__in=[None, request.user]).first()

        if not food:
            return redirect(f"{reverse('add_food')}?prefill={food_name}&log_after=true")

        # Save consumption
        Consume.objects.create(user=request.user, food=food, date=today)
        return redirect('dashboard')

    if goal_reached:
        return redirect('goal_reached')

    # 6. Final render (GET)
    return render(request, 'tracker/dashboard.html', {
        'consumed_items': consumed_items,
        'total_calories': total_calories,
        'goal': goal,
        'goal_reached': goal_reached,
        'food_names': food_names,
        'calorie_values': calorie_values,
    })




# ✅ Set goal based on age and weight
@login_required
def set_goal(request):
    if request.method == "POST":
        age = int(request.POST['age'])
        weight = float(request.POST['weight'])
        height = float(request.POST['height'])
        gender = request.POST['gender']

        if gender == 'M':
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        goal = int(bmr + 300)  # Add estimated activity factor

        CalorieGoal.objects.update_or_create(user=request.user, defaults={
            'age': age,
            'weight': weight,
            'height': height,
            'gender': gender,
            'goal': goal
        })

        return redirect('dashboard')

    return render(request, 'tracker/set_goal.html')



# ✅ Add food manually
@login_required
def add_food(request):
    prefill_name = request.GET.get('prefill', '')
    log_after = request.GET.get('log_after') == 'true'

    if request.method == "POST":
        name = request.POST['name'].strip().lower()
        calories = int(request.POST['calories'])

        food = Food.objects.create(name=name, calories=calories, user=request.user)

        if log_after:
            today = date.today()
            Consume.objects.create(user=request.user, food=food, date=today)

        return redirect('dashboard')

    return render(request, 'tracker/add_food.html', {'prefill_name': prefill_name})




# ✅ Goal reached message
@login_required
def goal_reached(request):
    return render(request, 'tracker/goal_reached.html')


# ✅ Daily history view
@login_required
def history(request):
    all_days = (
        Consume.objects.filter(user=request.user)
        .values('date')
        .annotate(total=Sum('food__calories'))
        .order_by('-date')
    )

    return render(request, 'tracker/history.html', {'history': all_days})


# ✅ Helper function
def get_user_goal(user):
    try:
        return CalorieGoal.objects.get(user=user).goal
    except CalorieGoal.DoesNotExist:
        return 0

@login_required
def reset_today(request):
    request.session.pop('goal_viewed', None)
    if request.method == 'POST':
        today = date.today()
        Consume.objects.filter(user=request.user, date=today).delete()
    return redirect('dashboard')

@login_required
def reset_all_history(request):
    if request.method == 'POST':
        Consume.objects.filter(user=request.user).delete()
    return redirect('dashboard')
