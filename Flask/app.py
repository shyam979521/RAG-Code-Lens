from app import create_app

app = create_app()

if __name__ == '__main__':
    # We disable reloader because saving the ZIP upload into the project folder 
    # triggers a server restart, which kills the upload process.
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
