from django.db import models


class Country(models.Model):
    numeric_code = models.CharField(
        max_length=3, unique=True, help_text="ISO 3166-1 numeric code for the country"
    )  # ISO 3166-1 numeric code
    code = models.CharField(max_length=2, unique=True)  # ISO Alpha-2 code
    name = models.CharField(max_length=255)  # Country name

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.code}, {self.numeric_code})"


# class Child(models.Model):
#     name = models.CharField(max_length=100)
#     age = models.PositiveIntegerField()
#     country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="children")
#     profile_description = models.TextField(blank=True)
#     date_of_birth = models.DateField()
#     image_path = models.CharField(max_length=50)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     deleted_at = models.DateTimeField(null=True, blank=True)

#     def __str__(self):
#         return f"{self.name} ({self.age}), {self.country.name}, {self.date_of_birth}"
