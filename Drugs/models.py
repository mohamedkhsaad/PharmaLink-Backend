
# Import necessary modules
from django.db import models

# Django model to represent drug-drug interactions
class DDIInteraction(models.Model):
    """
    Django model to represent drug-drug interactions.

    - Inherits from the Django's `models.Model` class.
    - Represents a table in the database to store drug-drug interaction data.
    """

    # Primary key field for the model
    id = models.BigAutoField(primary_key=True)

    # Fields to store identifiers for the drugs involved in the interaction
    drug1_id = models.CharField(max_length=50)
    drug2_id = models.CharField(max_length=50)

    # Fields to store names of the drugs involved in the interaction
    drug1_name = models.CharField(max_length=255)
    drug2_name = models.CharField(max_length=255)

    # Field to store the type of interaction
    interaction_type = models.CharField(max_length=1000)

    def __str__(self):
        """
        Returns a string representation of the model instance.

        Returns:
            - str: A string representation of the DDIInteraction instance.
        """
        return f"{self.drug1_name} - {self.drug2_name}: {self.interaction_type}"
