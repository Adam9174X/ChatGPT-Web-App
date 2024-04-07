from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import json
import openai

app = Flask(__name__, template_folder='APP', static_folder='Data')
app.secret_key = 'Adam9174X'  # Set a secret key for session security

openai.api_key = 'Put Your Own OpenAI API Key here...'

# Load User database from JSON file
with open('/home/Adam9174X/mysite/database.json', 'r') as file:
    database = json.load(file)

# Initialize user chat history in session
def init_user_history():
    if 'history' not in session:
        session['history'] = []


@app.route('/')
def index():
    return  render_template('home.html')

# Error handling
@app.errorhandler(Exception)
def handle_error(error):
    return render_template('error.html'), 500

@app.route('/chat' , methods=['GET', 'POST'])
def chat():
    if 'user' in session:  # Check if user is signed in
        models = openai.Model.list()
        model_names = [model['id'] for model in models['data']]
        init_user_history()  # Initialize user chat history in session
        return render_template('ChatGPT.html', models=model_names)
    else:
        return redirect(url_for('sign_in'))

@app.route('/Sign_Up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        User_Name = request.form['User_Name'].strip()  # Remove leading/trailing spaces
        Password = request.form['Password'].strip()  # Remove leading/trailing spaces

        # Check if the User_Name already exists
        if User_Name in database:
            return '<div class="alert alert-danger alert-dismissible fade show" role="alert"><center>User Name is already Taken!</center><button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>' + render_template('Sign Up.html')

        # Add the New User to the database
        database[User_Name] = Password

        # Save the updated database to the JSON file
        with open('/home/Adam9174X/mysite/database.json', 'w') as file:
            json.dump(database, file)

        return redirect(url_for('chat'))

    return render_template('Sign Up.html')


@app.route('/Sign_In', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'POST':
        User_Name = request.form['User_Name'].strip()  # Remove leading/trailing spaces
        Password = request.form['Password'].strip()  # Remove leading/trailing spaces

        # Check if the User Name and Password match a User in the database
        if User_Name in database and database[User_Name] == Password:
            session['user'] = User_Name  # Store user in session
            init_user_history()  # Initialize user chat history in session
            return redirect(url_for('chat'))

        elif User_Name not in database:
            return '<div class="alert alert-danger alert-dismissible fade show" role="alert"><center>User Name is Incorrect!</center><button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>' + render_template("Sign In.html")

        elif User_Name in database and database[User_Name] != Password:
            return '<div class="alert alert-danger alert-dismissible fade show" role="alert"><center>Password is Incorrect!</center><button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>' + render_template("Sign In.html")

    return render_template('Sign In.html')

@app.route('/Chat', methods=['POST'])
def Chat():
    user_input = request.form['user_input']
    selected_model = request.form['model']  # Added to get the selected model from the dropdown
    JavaScript = """
<script>
  function typeLastMessage() {
    const lastMessage = document.querySelector('.assistant-message:last-of-type h');
    const textToType = lastMessage.textContent.trim();
    lastMessage.textContent = ''; // Remove the text from the element

    let currentIndex = 0;

    function typeCharacter() {
      lastMessage.textContent += textToType[currentIndex];
      currentIndex += 1;

      if (currentIndex < textToType.length) {
        setTimeout(typeCharacter, 1);
      } else {
        setTimeout(() => {
          lastMessage.style.borderRightWidth = '0'; // Remove the cursor by setting border-right-width to 0
          window.scrollTo(0, document.documentElement.scrollHeight || document.body.scrollHeight); // Scroll to the bottom of the page
          document.getElementById('send-button').disabled = false; // Enable the send button
          document.getElementById('user-input').disabled = false; // Enable the user input

        }, 1000);
      }

      window.scrollTo(0, document.documentElement.scrollHeight || document.body.scrollHeight); // Scroll down with each character typed
    }

    typeCharacter();
    document.getElementById('send-button').disabled = true; // Disable the send button
    document.getElementById('user-input').disabled = true; // Disable the user input
  }

  typeLastMessage();
</script>
"""

    # Check if the user input contains image-related keywords
    if any(keyword in user_input.lower().replace(" ", "") for keyword in ["image", "photo" , "picture"]):
        # Generate the image using OpenAI's API
        image = openai.Image.create(
            prompt=user_input,
            size="512x512",
        )

        image_url = image['data'][0]['url']

        # Return URL of the generated image
        return jsonify({
            'response': f"<p><h>Sure, here is the Photo with the Description you Provided : </h></p>"
                       + JavaScript
                       + f"<img src='" + image_url + "'  width='300' height='300'>"
                       + f"<br><br><br>"
                       + f"<a href='" + image_url + "'  download='Photo.png'>"
                       + f"<button class='btn btn-primary' id='download'>Download</button>"
                       + f"</a><br>"
        })

    if selected_model is not None and selected_model.startswith("gpt"):
        history = session['history']
        s = list(sum(history, ()))
        s.append(user_input)
        inp = ' '.join(s)

        # Call OpenAI API for chat completion
        completion = openai.ChatCompletion.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": inp},
                {"role": "user", "content": user_input}
            ]
        )

        response = completion.choices[0].message.content

        history.append((user_input, response))
        session['history'] = history  # Update user chat history in session

        return jsonify({'response': f'<h>{response}</h>' + JavaScript})

    else:
        history = session['history']
        s = list(sum(history, ()))
        s.append(user_input)
        inp = ' '.join(s)

        # Call OpenAI API for model completion using the selected model
        completion = openai.Completion.create(
            engine=selected_model,  # Use the selected model
            prompt=inp,
            max_tokens=2048,
            temperature=1
        )

        response = completion.choices[0].text.strip()

        history.append((user_input, response))
        session['history'] = history  # Update user chat history in session

        return jsonify({'response': f'<h>{response}</h>' + JavaScript})

@app.route('/new-chat', methods=['POST'])
def new_chat():
    session['history'] = []
    return jsonify({'success': True})

@app.route('/Sign_Out')
def sign_out():
    session.pop('user', None)  # Remove user from session
    session.pop('history', None)  # Remove user chat history from session
    return redirect(url_for('sign_in'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9174, debug=False)
