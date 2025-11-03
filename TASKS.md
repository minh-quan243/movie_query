1. Create a `requirements.txt` file in the project root.
2. Create shell script for macOS and Windows that will take care of setting up the virtual environment and installing dependencies and start the web app inside `start_server/`. It will:
    - Create and activate a virtual environment.
    - Install dependencies from `requirements.txt`.
    - Download the spaCy model.
    - Navigate to the `frontend/` directory.
    - Install Node.js dependencies.
    - Build the frontend.
    - Start the Flask backend server.
    
    Note that for dependencies installation, it should check if the virtual environment is already set up or dependencies already installed to avoid redundant installations, this also apply for Node.js dependencies. Because to start the web app, user will run this script multiple times.