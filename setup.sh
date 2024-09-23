#!/bin/bash

# Clone the repository
git clone https://github.com/carbonjo/AutoSurvey.git

# Navigate into the repository directory
cd Auto_survey2

# Create and activate a virtual environment
python3 -m venv survey
source survey/bin/activate

# Install required Python packages
pip install -r requirements.txt

echo "Environment setup complete!"

