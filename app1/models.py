from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    leetcode_username = models.CharField(max_length=50, blank=True, null=True)
    codechef_username = models.CharField(max_length=50, blank=True, null=True)
    codeforces_username = models.CharField(max_length=50, blank=True, null=True)
    gfg_username = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.user.username
