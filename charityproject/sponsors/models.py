from django.db import models


class Country(models.Model):
    # ISO 3166-1 numeric code
    numeric_code = models.CharField(
        max_length=3, unique=True, help_text="ISO 3166-1 numeric code for the country"
    )
    # ISO Alpha-2 code
    code = models.CharField(
        max_length=2, unique=True, help_text="ISO Alpha-2 code for the country"
    )
    # Country name
    name = models.CharField(max_length=255, unique=True, verbose_name="Country Name")

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class Gender(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Child(models.Model):
    name = models.CharField(max_length=255)
    age = models.PositiveIntegerField()
    gender = models.ForeignKey(
        Gender, on_delete=models.PROTECT, related_name="children"
    )
    country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name="children"
    )
    profile_description = models.TextField(blank=True)
    date_of_birth = models.DateField()
    image = models.ImageField(upload_to="children/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["country"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.age}), {self.country.name}, {self.date_of_birth}"
