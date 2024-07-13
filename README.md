1. Install [Anaconda](https://docs.anaconda.com/anaconda/install/)
   - Follow the instructions on the Anaconda website to install Anaconda on your system.
2. Create Anaconda enviornment and activate it
   - Open a terminal or command prompt and run the following commands:
        ```console
        conda create -n tc-energy python=3.11
        conda activate tc-energy
        ```
3. Install Requirements:
   - Ensure you are in your project's directory, then run:
        ```console
        pip install -r requirements.txt
        ```
4. Get [Google Maps API key](https://developers.google.com/maps/documentation)
   - Follow the instructions on the Google Developers website to obtain your API key.
5. Set Google Maps API key as environment variable
    - Local:
        - Linux / MacOS:
            ```console
            echo "export GOOGLE_API_KEY='yourkey'" >> ~/.zshrc
            source ~/.zshrc
            echo $GOOGLE_API_KEY
            ```
        - Windows:
            ```console
            setx GOOGLE_API_KEY "yourkey"
            echo %GOOGLE_API_KEY%
            ```
    - Online Deployment:
        - Open `app-temp.yaml`
        - Modify the following line:
            ```yaml
            GOOGLE_API_KEY: 'your_google_api_key'
            ```
        - Rename the file to `app.yaml`