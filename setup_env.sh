#!/bin/bash

# Load Miniconda
module load miniconda3/24.1.2-py310

# Create Conda environment
conda env create -f environment.yml

# Activate the environment
conda activate 7030_capstone_project

# Install optional pip packages
pip install -r requirements.txt

# Register Python kernel
python -m ipykernel install --user --name 7030_capstone_project --display-name "Python (7030_capstone_project)"

# Register R kernel
Rscript -e 'IRkernel::installspec(name="ir_7030_capstone_project", displayname="R (7030_capstone_project)")'

# Start JupyterLab (port 2000)
# Streamlit dashboard must use a DIFFERENT port (recommended: 2001):
#   streamlit run app.py --server.port 2001 --server.address 0.0.0.0
jupyter lab --no-browser --port=2000
