1. Install [Anaconda](https://docs.anaconda.com/anaconda/install/)
2. Create Anaconda enviornment and activate it
    - ```console
        conda create -n tc-energy python=3.9
        conda activate tc-energy
        ```
3. Install Requirements
    - ```console
        pip install -r requirements.txt
        ```
4. Get [Google Maps API key](https://developers.google.com/maps/documentation)
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
        - Open `app.yaml`
        - Modify the following line:
        ```yaml
        GOOGLE_API_KEY: 'your_google_api_key'
        ```