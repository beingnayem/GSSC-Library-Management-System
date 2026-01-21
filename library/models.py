from django.db import models
from django.contrib.auth.models import User
from datetime import datetime,timedelta
import uuid

class StudentExtra(models.Model):
    my_primary_key = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=40, unique=True)  # Set your default value here
    department_name = models.CharField(max_length=100, default="Unknown Department")  # Set your default value here
    session = models.CharField(max_length=20, default="")  # Set your default value here
    educational_year = models.PositiveIntegerField(default=2023)  # Set your default value here


    def __str__(self):
        return self.user.first_name + '[' + self.student_id + ']'
    
    @property
    def get_name(self):
        return self.user.first_name
    
    @property
    def get_user_id(self):
        return self.user.id


class Book(models.Model):
    catchoice= [
        ('education', 'Education'),
        ('entertainment', 'Entertainment'),
        ('comics', 'Comics'),
        ('biography', 'Biography'),
        ('history', 'History'),
        ('novel', 'Novel'),
        ('fantasy', 'Fantasy'),
        ('thriller', 'Thriller'),
        ('romance', 'Romance'),
        ('scifi','Sci-Fi')
    ]
    
    status_choices = [
        ('received', 'Received'),
        ('issued', 'Issued'),
        ('pending','Pending'),
        ('return_requested', 'Return_Requested')
    ]
    my_primary_key = models.BigAutoField(primary_key=True)
    name=models.CharField(max_length=30)
    isbn=models.PositiveIntegerField()
    author=models.CharField(max_length=40)
    category=models.CharField(max_length=30,choices=catchoice,default='education')
    publication_name = models.CharField(max_length=50, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    edition = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=status_choices, default='received')
    requested_by = models.ForeignKey(StudentExtra, on_delete=models.SET_NULL, null=True, blank=True)
     
    def __str__(self):
        return str(self.name)+"["+str(self.isbn)+']'


def get_expiry():
    return datetime.today() + timedelta(days=15)

class IssuedBook(models.Model):
    my_primary_key = models.BigAutoField(primary_key=True)
    #moved this in forms.py
    #enrollment=[(student.enrollment,str(student.get_name)+' ['+str(student.enrollment)+']') for student in StudentExtra.objects.all()]
    student_id=models.CharField(max_length=30)
    #isbn=[(str(book.isbn),book.name+' ['+str(book.isbn)+']') for book in Book.objects.all()]
    isbn=models.CharField(max_length=30)
    issuedate=models.DateField(auto_now=True)
    expirydate=models.DateField(default=get_expiry)
    department_name = models.CharField(max_length=100, default="Unknown Department")
    session = models.CharField(max_length=20, default="")  
    educational_year = models.PositiveIntegerField(default=2023)
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    
    def __str__(self):
        return self.student_id

