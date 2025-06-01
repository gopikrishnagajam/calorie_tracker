from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Food, Consume, CalorieGoal
from django.utils.timezone import now
from datetime import date
from django.db.models import Sum

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
    consumed_items = Consume.objects.filter(user=request.user, date=today)
    total_calories = consumed_items.aggregate(total=Sum('food__calories'))['total'] or 0

    # Food entry from user
    if request.method == "POST":
        food_name = request.POST['food_name'].strip().lower()
        try:
            food = Food.objects.get(name__iexact=food_name)
        except Food.DoesNotExist:
            return render(request, 'tracker/dashboard.html', {
                'error': 'Food not found. Try adding it manually.',
                'consumed_items': consumed_items,
                'total_calories': total_calories,
                'goal': get_user_goal(request.user),
                'goal_reached': total_calories >= get_user_goal(request.user)
            })
        Consume.objects.create(user=request.user, food=food, date=today)
        return redirect('dashboard')

    goal = get_user_goal(request.user)
    goal_reached = total_calories >= goal if goal else False

    return render(request, 'tracker/dashboard.html', {
        'consumed_items': consumed_items,
        'total_calories': total_calories,
        'goal': goal,
        'goal_reached': goal_reached
    })


# ✅ Set goal based on age and weight
@login_required
def set_goal(request):
    if request.method == "POST":
        age = int(request.POST['age'])
        weight = float(request.POST['weight'])

        # Simple formula (can be adjusted)
        goal = int(10 * weight + 6.25 * age + 300)

        CalorieGoal.objects.update_or_create(user=request.user, defaults={
            'age': age,
            'weight': weight,
            'goal': goal
        })
        return redirect('dashboard')

    return render(request, 'tracker/set_goal.html')


# ✅ Add food manually
@login_required
def add_food(request):
    if request.method == "POST":
        name = request.POST['name'].strip().lower()
        calories = int(request.POST['calories'])

        Food.objects.create(name=name, calories=calories)
        return redirect('dashboard')

    return render(request, 'tracker/add_food.html')


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
