from django.db import models

# Create your models here.


from django.db import models

class DDIInteraction(models.Model):
    id = models.BigAutoField(primary_key=True)
    drug1_id = models.CharField(max_length=50)
    drug2_id = models.CharField(max_length=50)
    drug1_name = models.CharField(max_length=255)
    drug2_name = models.CharField(max_length=255)
    interaction_type = models.CharField(max_length=1000)
