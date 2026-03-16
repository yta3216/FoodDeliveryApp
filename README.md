# FoodDeliveryApp
Group 23's Repository for COSC310 (University of British Columbia - Okanagan)
Team Members:
- Ye Thway Aung (57617417) 
- Owen Wood (64265275)
- Su Myat Thwe (95306684)
- Sultan Aldeiro (35187749)

# How to Run:
1. Make sure your terminal is in the backend directory 
2. Create your virtual environment (name it whatever you want) IN THE BACKEND DIRECTORY
3. Activate the virtual environment
4. From the backend repository
4. pip install "pip install -r requirements.txt"
5. To run: fastapi dev app/main.py

# For Developers

## Test & Generate Coverage Reports
Run the following prompt in your terminal (from the FoodDeliveryApp directory):

pytest fullstack-project/backend/testing --cov --cov-report=term --cov-report=html:fullstack-project/backend/testing/coverage-reports-html

*Note: if you would like to commit these reports to GitHub, you will need to delete the .gitignore file in the coverage report folder.*