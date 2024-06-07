from flask import Flask, render_template, request
import aiohttp
import asyncio
import re
import config  # Importer les configurations

app = Flask(__name__)

# Utiliser les configurations importées
CHATBOT_APIS = config.CHATBOT_APIS
API_KEYS = config.API_KEYS

async def send_to_chatbot(session, chatbot, url, question):
    """
    Envoie une question à un chatbot spécifique et retourne la réponse.

    :param session: Session aiohttp pour les requêtes HTTP asynchrones
    :param chatbot: Nom du chatbot
    :param url: URL de l'API du chatbot
    :param question: Question à envoyer au chatbot
    :return: Réponse du chatbot
    """
    headers = {
        "Authorization": f"Bearer {API_KEYS[chatbot]}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": question,
        "max_tokens": 150
    }
    try:
        async with session.post(url, headers=headers, json=payload) as response:
            response.raise_for_status()
            return await response.json()
    except aiohttp.ClientError as e:
        print(f"Error with {chatbot}: {e}")
        return {"choices": [{"text": "Error processing request."}]}

async def get_responses_from_chatbots(question):
    """
    Envoie la question à tous les chatbots et collecte leurs réponses.

    :param question: Question à envoyer aux chatbots
    :return: Dictionnaire des réponses des chatbots
    """
    async with aiohttp.ClientSession() as session:
        tasks = [send_to_chatbot(session, chatbot, url, question) for chatbot, url in CHATBOT_APIS.items()]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        return {chatbot: response for chatbot, response in zip(CHATBOT_APIS.keys(), responses)}

async def evaluate_response(session, evaluator_bot, response_to_evaluate):
    """
    Demande à un chatbot d'évaluer une réponse fournie par un autre chatbot.

    :param session: Session aiohttp pour les requêtes HTTP asynchrones
    :param evaluator_bot: Nom du chatbot évaluateur
    :param response_to_evaluate: Réponse à évaluer
    :return: Score d'évaluation de la réponse
    """
    headers = {
        "Authorization": f"Bearer {API_KEYS[evaluator_bot]}",
        "Content-Type": "application/json"
    }
    evaluation_prompt = f"Please evaluate the following response on a scale of 1 to 5 for quality and relevance: {response_to_evaluate['choices'][0]['text']}"
    payload = {
        "prompt": evaluation_prompt,
        "max_tokens": 50
    }
    try:
        async with session.post(CHATBOT_APIS[evaluator_bot], headers=headers, json=payload) as response:
            response.raise_for_status()
            evaluation_response = await response.json()
            score_text = evaluation_response['choices'][0]['text'].strip()
            score = int(re.search(r'\b[1-5]\b', score_text).group())
            return score
    except (aiohttp.ClientError, ValueError, AttributeError) as e:
        print(f"Error with {evaluator_bot} evaluating response: {e}")
        return 3  # Default score if parsing fails

async def evaluate_responses(session, responses):
    """
    Collecte les évaluations de toutes les réponses par les autres chatbots.

    :param session: Session aiohttp pour les requêtes HTTP asynchrones
    :param responses: Dictionnaire des réponses des chatbots
    :return: Dictionnaire des scores d'évaluation des réponses
    """
    scores = {chatbot: {} for chatbot in responses.keys()}
    for bot1, response1 in responses.items():
        if isinstance(response1, Exception):
            continue
        for bot2, response2 in responses.items():
            if bot1 != bot2 and not isinstance(response2, Exception):
                scores[bot1][bot2] = await evaluate_response(session, bot1, response2)
    return scores

def generate_clarification_question(response):
    """
    Génère une question de clarification basée sur la réponse d'un chatbot.

    :param response: Réponse du chatbot
    :return: Question de clarification générée
    """
    response_text = response['choices'][0]['text']
    questions = re.findall(r"([^.!?]*\?)", response_text)
    
    if questions:
        clarification_question = f"Can you clarify the following: {questions[0]}"
    else:
        clarification_question = f"Can you provide more details about: {response_text[:100]}"
    
    return clarification_question

async def interact_between_bots(initial_question):
    """
    Coordonne l'interaction entre les chatbots, en collectant les réponses initiales, les évaluations, et les questions de clarification, puis en sélectionnant la meilleure réponse finale.

    :param initial_question: Question initiale posée par l'utilisateur
    :return: Meilleure réponse finale sélectionnée
    """
    async with aiohttp.ClientSession() as session:
        responses = await get_responses_from_chatbots(initial_question)
        scores = await evaluate_responses(session, responses)

        clarifications = {}
        for bot, score_dict in scores.items():
            bot_to_ask = min(score_dict, key=score_dict.get)
            clarification_question = generate_clarification_question(responses[bot_to_ask])
            clarifications[bot] = await send_to_chatbot(session, bot, CHATBOT_APIS[bot], clarification_question)

        final_scores = await evaluate_responses(session, clarifications)
        best_response = select_best_response(clarifications, final_scores)
        return best_response

def select_best_response(clarifications, scores):
    """
    Sélectionne la réponse ayant le meilleur score moyen.

    :param clarifications: Dictionnaire des réponses clarifiées
    :param scores: Dictionnaire des scores d'évaluation des réponses clarifiées
    :return: Meilleure réponse sélectionnée
    """
    avg_scores = {bot: sum(score.values()) / len(score) for bot, score in scores.items()}
    best_bot = max(avg_scores, key=avg_scores.get)
    return clarifications[best_bot]

@app.route('/', methods=['GET', 'POST'])
async def home():
    """
    Page d'accueil avec formulaire pour poser une question. Affiche la meilleure réponse après traitement par les chatbots.

    :return: Rendu de la page HTML avec la meilleure réponse
    """
    best_response = None
    if request.method == 'POST':
        question = request.form.get('question')
        best_response = await interact_between_bots(question)
    return render_template('index.html', best_response=best_response)

if __name__ == '__main__':
    app.run(debug=True)

