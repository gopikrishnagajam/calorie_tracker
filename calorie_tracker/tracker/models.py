from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Food(models.Model):
    name = models.CharField(max_length=100)
    calories = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} - {self.calories} kcal"


class Consume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} ate {self.food.name} on {self.date}"


class CalorieGoal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.PositiveIntegerField()
    weight = models.FloatField(help_text="In kilograms")
    goal = models.PositiveIntegerField(help_text="Calories per day")

    def __str__(self):
        return f"{self.user.username}'s goal: {self.goal} kcal"
