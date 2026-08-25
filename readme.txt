STEP 1 — Install Python 3.11
STEP 2 — Install PostgreSQL on Windows
postgress password = Aman@1234
db name = school_erp
STEP 3 — Install Git (if not installed)
STEP 4 — Open Command Prompt (CMD) or PowerShell
STEP 5 — Create Project Folder
:: Create project folder
mkdir school_erp
cd school_erp

STEP 6 — Create Virtual Environment
:: Create virtual environment
python -m venv venv

 STEP 7 — Install WeasyPrint Dependencies (Windows Extra Step)
:: Activate it (Windows CMD)
venv\Scripts\activate
Download GTK3 runtime from:
https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
:: Activate it (PowerShell)
venv\Scripts\Activate.ps1

STEP 8 — Create requirements.txt
STEP 9 — Install All Packages --pip install -r requirements.txt

STEP 10 — Create Django Project
:: Still inside school_erp folder with venv active
django-admin startproject config .

:: Verify — you should see:
dir
:: config\   manage.py   requirements.txt   venv\

STEP 11 — Create Apps Folder & All Apps

STEP 12 — Fix Each App's apps.py
STEP 13 — Create Settings Package
STEP 14 — Create .env File
STEP 15 — Write Settings Files
STEP 16 — Update manage.py
STEP 17 — Create templates Folder Structure
STEP 18 — Create .gitignore
STEP 19 — Run Migrations & Start Server
:: If PowerShell gives error, run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
:: Then try again:
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
after setup all files and folder
:: Check for problems first
python manage.py check

:: Make migrations
python manage.py makemigrations

:: Run migrations
python manage.py migrate

:: Create admin superuser
python manage.py createsuperuser
:: Enter: Username, Email, Password

:: Collect static files
python manage.py collectstatic --noinput

:: Start server
python manage.py runserver