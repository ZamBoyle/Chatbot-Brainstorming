# Chatbot Brainstorming

A Flask application that allows multiple chatbots to brainstorm and provide the best response to a user's question.

## Features
- Send a question to multiple chatbots.
- Collect responses from each chatbot.
- Evaluate responses and generate clarification questions.
- Select the best response based on evaluations from other chatbots.

## Requirements
- Python 3.6+
- Flask
- aiohttp

## Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/Chatbot-Brainstorming.git
    ```

2. Navigate to the project directory:
    ```bash
    cd Chatbot-Brainstorming
    ```

3. Install the required dependencies:
    ```bash
    pip install Flask aiohttp
    ```

4. Create a `config.py` file with your API keys and chatbot URLs:
    ```python
    # config.py
    CHATBOT_APIS = {
        "gpt-4": "https://api.openai.com/v1/engines/davinci-codex/completions",
        "dialogflow": "https://dialogflow.googleapis.com/v2/projects/project-id/agent/sessions/session-id:detectIntent"
    }

    API_KEYS = {
        "gpt-4": "YOUR_OPENAI_API_KEY",
        "dialogflow": "YOUR_DIALOGFLOW_API_KEY"
    }
    ```

5. Add `config.py` to your `.gitignore` file:
    ```bash
    echo "config.py" >> .gitignore
    ```

## Usage

1. Run the Flask application:
    ```bash
    python app.py
    ```

2. Open your web browser and go to `http://127.0.0.1:5000/`.

3. Enter a question in the form and submit it to receive the best response from the chatbots.

## Contributing

Feel free to submit issues or pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License.

