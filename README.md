# FoodDeliveryApp
Group 23's Repository for COSC310 (University of British Columbia - Okanagan)
Team Members:
- Ye Thway Aung (57617417) 
- Owen Wood (64265275)
- Su Myat Thwe (95306684)
- Sultan Aldeiro (35187749)

## How to Run
### Option 1: From Virtual Environment
1. Make sure your terminal is in the *backend* directory 
2. Create your virtual environment (name it whatever you want) IN THE BACKEND DIRECTORY
    * example terminal prompt (last argument is venv name): *python -m venv venv*
3. Activate the virtual environment
    * for the previous example (venv=venv name): *venv/scripts/activate*
4. From the backend directory, run the following commands:
    * *pip install -r requirements.txt*
    * *fastapi dev app/main.py*
5. To close the program, press *ctrl + c* from the terminal

### Option 2: Using Docker (from terminal)
1. Open the Docker Desktop app
2. Make sure your terminal is in the root directory *FoodDeliveryApp/*
3. Run the following command:
    * *docker compose up --build*
4. To close the program, press *ctrl + c* from the terminal

## For Developers
### Run Tests & Generate Coverage Reports
Run the following prompts in your terminal (from the backend directory):
*(remove existing coverage reports from git if needed: git rm -r testing/coverage-reports-html)*

pytest testing --cov --cov-report=term --cov-report=markdown:testing/coverage-reports/coverage_report_md --cov-report=html:testing/coverage-reports/html-reports

*Note: if you would like to commit these reports to GitHub, you will need to delete the .gitignore file in the coverage-reports/html folder.*
