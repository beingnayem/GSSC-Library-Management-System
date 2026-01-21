from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from . import forms,models
from django.urls import reverse
from .models import StudentExtra, Book, IssuedBook
from django.http import HttpResponseRedirect
from django.contrib.auth.models import Group
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required,user_passes_test
from datetime import datetime,timedelta,date
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout


def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'library/index.html')


#for showing signup/login button for student
def studentclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'library/studentclick.html')


#for showing signup/login button for teacher
def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'library/adminclick.html')


def adminsignup_view(request):
    form=forms.AdminSigupForm()
    if request.method=='POST':
        form=forms.AdminSigupForm(request.POST)
        if form.is_valid():
            user=form.save()
            user.set_password(user.password)
            user.save()


            my_admin_group = Group.objects.get_or_create(name='ADMIN')
            my_admin_group[0].user_set.add(user)

            return HttpResponseRedirect('adminlogin')
    return render(request,'library/adminsignup.html',{'form':form})


def studentsignup_view(request):
    form1 = forms.StudentUserForm()
    form2 = forms.StudentExtraForm()
    mydict = {'form1': form1, 'form2': form2}
    
    if request.method == 'POST':
        form1 = forms.StudentUserForm(request.POST)
        form2 = forms.StudentExtraForm(request.POST)
        
        if form1.is_valid() and form2.is_valid():
            student_id = form2.cleaned_data['student_id']
            
            # Check if a student with the provided student_id already exists
            if StudentExtra.objects.filter(student_id=student_id).exists():
                messages.error(request, 'A student already exists with this student ID. Please try again with a different student ID.')
                return render(request, 'library/studentsignup.html', context=mydict)
            
            user = form1.save()
            user.set_password(user.password)
            user.save()
            
            f2 = form2.save(commit=False)
            f2.user = user
            user2 = f2.save()
            
            my_student_group = Group.objects.get_or_create(name='STUDENT')
            my_student_group[0].user_set.add(user)

            return HttpResponseRedirect('studentlogin')
    
    return render(request, 'library/studentsignup.html', context=mydict)


def is_admin(user):
    return user.groups.filter(name='ADMIN').exists()


def afterlogin_view(request):
    if is_admin(request.user):
        return render(request,'library/adminafterlogin.html')
    else:
        return render(request,'library/studentafterlogin.html')

def admin_signin(request):
   pass


def student_signin(request):
    pass



@login_required
def signout(request):
    logout(request)
    return redirect('home')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def addbook_view(request):
    #now it is empty book form for sending to html
    form=forms.BookForm()
    if request.method=='POST':
        #now this form have data from html
        form=forms.BookForm(request.POST)
        if form.is_valid():
            
            user=form.save()
            return render(request,'library/bookadded.html')
    return render(request,'library/addbook.html',{'form':form})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def viewbook_view(request):
    books=models.Book.objects.all()
    return render(request,'library/viewbook.html',{'books':books})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def issuebook_view(request):
    form = forms.IssuedBookForm()
    
    if request.method == 'POST':
        form = forms.IssuedBookForm(request.POST)
        
        if form.is_valid():
            student_id = request.POST.get('student_id2')
            isbn = request.POST.get('isbn2')
            
            # Create IssuedBook instance and set its attributes
            issued_by_user = request.user  # Get the actual User instance
            obj = models.IssuedBook(
                student_id=student_id,
                isbn=isbn,
                issued_by=issued_by_user # Set the admin who issued the book
            )
            obj.save()
            
            # Update the book's status to 'Issued'
            book = models.Book.objects.get(isbn=isbn)
            book.status = 'issued'
            book.save()
            
            return render(request, 'library/bookissued.html')
    
    return render(request, 'library/issuebook.html', {'form': form})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def viewissuedbook_view(request):
    issuedbooks = models.IssuedBook.objects.all()
    li = []
    
    for ib in issuedbooks:
        issdate = str(ib.issuedate.day) + '-' + str(ib.issuedate.month) + '-' + str(ib.issuedate.year)
        expdate = str(ib.expirydate.day) + '-' + str(ib.expirydate.month) + '-' + str(ib.expirydate.year)
        
        # Fine calculation
        days = (date.today() - ib.issuedate)
        d = days.days
        fine = 0
        if d > 15:
            day = d - 15
            fine = day * 10
        
        books = list(models.Book.objects.filter(isbn=ib.isbn))
        students = list(models.StudentExtra.objects.filter(student_id=ib.student_id))
        
        for student, book in zip(students, books):
            t = (student.get_name, student.student_id, student.session, student.department_name, book.name, book.isbn, book.author, issdate, expdate, fine, book.status, ib.issued_by)
            li.append(t)
    
    return render(request, 'library/viewissuedbook.html', {'li': li})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def viewstudent_view(request):
    students=models.StudentExtra.objects.all()
    return render(request,'library/viewstudent.html',{'students':students})


@login_required(login_url='studentlogin')
def viewissuedbookbystudent(request):
    students = models.StudentExtra.objects.filter(user_id=request.user.id)

    if students:
        student = students[0]
        issued_books = models.IssuedBook.objects.filter(student_id=student.student_id)

        issued_books_info = []
        for issued_book in issued_books:
            book = models.Book.objects.get(isbn=issued_book.isbn)
            if book.status == 'issued':
                issued_by = issued_book.issued_by

                issued_date = issued_book.issuedate.strftime('%d-%m-%Y')
                expiry_date = issued_book.expirydate.strftime('%d-%m-%Y')

                days_overdue = (date.today() - issued_book.issuedate).days
                fine = max(0, (days_overdue - 15) * 10)

                issued_books_info.append({
                    'student_name': student.user.username,
                    'student_id': student.student_id,
                    'book_name': book.name,
                    'isbn': book.isbn,
                    'author': book.author,
                    'issued_date': issued_date,
                    'expiry_date': expiry_date,
                    'fine': fine,
                    'issued_by': issued_by,
                    'status': book.status,
                })

        return render(
            request,
            'library/viewissuedbookbystudent.html',
            {'issued_books_info': issued_books_info}
        )
    else:
        return HttpResponse("Student not found.")




def aboutus_view(request):
    return render(request,'library/aboutus.html')


def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message, EMAIL_HOST_USER, ['wapka1503@gmail.com'], fail_silently = False)
            return render(request, 'library/contactussuccess.html')
    return render(request, 'library/contactus.html', {'form':sub})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_bookByAdmin(request):
    if request.method == 'GET':
        pk = request.GET['pk']
        
    book = get_object_or_404(Book, pk=pk)

    if book:
        book.delete()
    
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def edit_book(request, pk):
    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        book.name = request.POST['name']
        book.isbn = request.POST['isbn']
        book.author = request.POST['author']
        book.category = request.POST['category']
        book.publication_name = request.POST['publication_name']
        book.publication_date = request.POST['publication_date']
        book.edition = request.POST['edition']
        book.save()

        Books=models.Book.objects.all()
        return render(request,'library/viewbook.html',{'books':Books})

    context = {'book': book}
    return render(request, 'library/editBook.html', context)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_studentByAdmin(request):
    if request.method == 'GET':
        pk = request.GET.get('pk')  # Using get() method to avoid KeyError
        
        if pk is not None:
            student = get_object_or_404(StudentExtra, pk=pk)
            student.delete()
    
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def edit_student(request, pk):
    student = get_object_or_404(StudentExtra, pk=pk)  # Use StudentExtra instead of Book

    if request.method == 'POST':
        student.user.first_name = request.POST['f_name']  # Correct the field name
        student.user.last_name = request.POST['l_name'] 
        student.student_id = request.POST['student_id']
        student.department_name = request.POST['department_name']
        student.session = request.POST['session']
        student.educational_year = request.POST['educational_year']
        student.user.save()  # Save the user instance
        student.save()  # Save the StudentExtra instance

        students = StudentExtra.objects.all()  # Use lowercase 'students' instead of 'StudentExtra'
        return render(request, 'library/viewstudent.html', {'students': students})

    context = {'student': student}
    return render(request, 'library/editStudent.html', context)


@login_required(login_url='studentlogin')
def viewbook_viewbyStudent(request):
    books=models.Book.objects.filter(status='received')
    return render(request,'library/viewAllbookByStudent.html',{'books':books})


@login_required(login_url='studentlogin')
def request_borrow_book(request):
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        try:
            book = Book.objects.get(pk=book_id, status='received')
            student = get_object_or_404(StudentExtra, user=request.user)  # Get the StudentExtra instance for the logged-in user
            # print(student.student_id)
            # print(student.department_name)

            # Create a pending book request
            book.status = 'pending'
            book.requested_by = student
            book.save()

            return render(request, 'library/book_request_success.html')  # Redirect to a success page
        except Book.DoesNotExist:
            pass  # Handle error if book not found or not in 'received' status

    return render(request, 'library/book_request_failure.html')  # Redirect to a failure page


@login_required(login_url='adminlogin')
def pending_book_requests(request):
    user = request.user

    # Check if the user belongs to the "ADMIN" group
    if user.groups.filter(name='ADMIN').exists():
        pending_books = Book.objects.filter(status='pending')
        print(pending_books)
        return render(request, 'library/view_pending_books.html', {'pending_books': pending_books})
    else:
        return render(request, 'library/access_denied.html')  # Redirect to access denied page for non-admin users



@login_required(login_url='adminlogin')
def approve_issue_book(request):
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        student_id = request.POST.get('student_id')  # Get the student_id from the form
        isbn = request.POST.get('isbn')  # Get the ISBN from the form

        try:
            book = Book.objects.get(pk=book_id, status='pending')
            print(book)
            
            # Create an IssuedBook instance
            issued_book = IssuedBook.objects.create(
                student_id=student_id,
                isbn=isbn,
                issued_by=request.user  # Assuming the currently logged-in admin approves the book
            )

            # Update the book status to 'issued'
            book.status = 'issued'
            book.save()

            return redirect(request.META.get('HTTP_REFERER'))  # Redirect back to the pending requests page
        except Book.DoesNotExist:
            pass  # Handle error if book not found or not in 'pending' status

    return render(request, 'library/approval_failure.html')  # Redirect to an approval failure page


@login_required(login_url='adminlogin')
def decline_issue_book(request):
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        try:
            book = Book.objects.get(pk=book_id, status='pending')

            # Check if there's an associated IssuedBook instance
            issued_book = IssuedBook.objects.filter(student_id=book.requested_by.student_id, isbn=book.isbn).first()
            if issued_book:
                issued_book.delete()  # Delete the IssuedBook instance

            # Update the book status to 'received'
            book.status = 'received'
            book.requested_by = None  # Reset the requested_by field
            book.save()

            return redirect('view_pendingbooks')  # Redirect back to the pending requests page
        except Book.DoesNotExist:
            pass  # Handle error if book not found or not in 'pending' status

    return render(request, 'library/decline_failure.html')  # Redirect to a decline failure page


@login_required(login_url='studentlogin')
@login_required(login_url='studentlogin')
def request_return_book(request):
    if request.method == 'POST':
        isbn = request.POST.get('isbn')
        print(isbn)
        try:
            book = Book.objects.get(isbn=isbn, status='issued')
            # Update the IssuedBook status to 'return_requested'
            book.status = 'return_requested'
            book.save()
            return render(request, 'library/return_request_success.html')
        except Book.DoesNotExist:
            return render(request, 'library/return_request_failure.html')  # Handle case when book doesn't exist or isn't issued

    return render(request, 'library/return_request_failure.html')  # Redirect to a failure page


@login_required(login_url='adminlogin')
def view_return_request(request):
    user = request.user

    # Check if the user belongs to the "ADMIN" group
    if user.groups.filter(name='ADMIN').exists():
        return_requested_book = Book.objects.filter(status='return_requested')
        print(return_requested_book)
        return render(request, 'library/view_return_requested_book.html', {'return_requested_book': return_requested_book})
    else:
        return render(request, 'library/access_denied.html')  # Redirect to access denied page for non-admin users
    
    
@login_required(login_url='adminlogin')
def approve_return_book(request):
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        try:
            book = Book.objects.get(pk=book_id, status='return_requested')

            # Check if there's an associated IssuedBook instance
            issued_book = IssuedBook.objects.filter(student_id=book.requested_by.student_id, isbn=book.isbn).first()
            if issued_book:
                issued_book.delete()  # Delete the IssuedBook instance

            # Update the book status to 'received'
            book.status = 'received'
            book.requested_by = None  # Reset the requested_by field
            book.save()

            return redirect('view_return_request')  # Redirect back to the pending requests page
        except Book.DoesNotExist:
            pass  # Handle error if book not found or not in 'pending' status

    return render(request, 'library/request_approve_failure.html')  # Redirect to a decline failure page


@login_required(login_url='studentlogin')
def search_book_student(request):
    if 'keywords' in request.GET:
        keywords = request.GET['keywords']
        # Perform the filtering or searching logic based on the keywords
        # For example, you can search for books whose name or author contains the keywords
        # Modify the following line to match your filtering criteria
        books = Book.objects.filter(name__icontains=keywords)

        context = {'books': books, 'keywords': keywords}
        return render(request, 'library/search_book_student.html', context)
    else:
        return render(request, 'library/book_not_found.html')