from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import openai
import json
import database

database_instance = database.database_conn()

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

with open("config.json") as f:
    file = json.load(f)

openai.api_key = file["openai"]


def generate_debate_prompts(gamemode, interested_subjects):
    prompts = {}

    if gamemode == 'normal':
        response = openai.Completion.create(
            engine="gpt-3.5-turbo-instruct",
            prompt=f"Create a debate topic based on {interested_subjects}? Only include the prompt, do not include any arguments or additional context.",
            max_tokens=100
        )
        prompts["Topic"] = response.choices[0].text.strip().strip('"')

    elif gamemode == 'crazy':
        response = openai.Completion.create(
            engine="gpt-3.5-turbo-instruct",
            prompt="Create a random debate topic with only one side. Do not add additional context or arguments.",
            max_tokens=100
        )
        prompts["Topic"] = response.choices[0].text.strip().strip('"')

    else:
        return json.dumps(
            {"error": "Invalid gamemode. Choose either 'normal' or 'crazy'"},
            indent=4)
    print(prompts)
    return prompts


def next_level(level: int) -> int:
    return round((4 * (level ** 3)) / 5)


def is_relevent(user_beginning_debate, users_reply, debate_topic):
    # Construct the prompt
    prompt = {
        "prompt": f"Based on the debate_topic '{debate_topic}' and the user's "
                  f"arguments and replies in '{user_beginning_debate}' and '{users_reply}', "
                  f"return true or false if the user's content is relevant to "
                  f"the topic or not. ",
        "temperature": 0.7,
        "max_tokens": 50
    }

    # Generate the response from GPT model
    response = openai.Completion.create(engine="gpt-3.5-turbo-instruct",
                                        prompt=prompt["prompt"],
                                        max_tokens=prompt["max_tokens"])

    # Parse the response
    response_text = response.choices[0].text.strip().lower()
    if "true" in response_text:
        return True
    elif "false" in response_text:
        return False
    else:
        # If the response does not contain a clear indication of true or
        # false, return None
        return None
def judge_debate_content(user_id, debate_topic, user_beginning_debate,
                         gpt_response, users_reply,
                         gamemode="normal"):
    prompt = {
        "prompt": f"Debate Topic: {debate_topic}\nUser's Beginning Debate:\n{user_beginning_debate}\nGPT Response:\n{gpt_response}\nUser's Reply to GPT Response:\n{users_reply}\n\n"
                  f"Please provide feedback and scores for the following categories:\n- Argument Clarity:\n- Depth of Analysis:\n- "
                  f"Counterargument Consideration:\n- Engagement with Opposing Views:\n- Language and Tone:\n- "
                  f"Coherence and Flow:\n- Originality and Creativity:\n\nPlease provide detailed examples from the debate "
                  f"content to support your feedback.\n\nPlease provide ratings for each category on a scale of 1 to 10 in the following format:\n"
                  f"Argument Clarity: [Rating]\nDepth of Analysis: [Rating]\nCounterargument Consideration: [Rating]\n"
                  f"Engagement with Opposing Views: [Rating]\nLanguage and Tone: [Rating]\nCoherence and Flow: [Rating]\n"
                  f"Originality and Creativity: [Rating]\nAggregate Score: [Aggregate Score]\n\n"
                  f"After evaluating, please structure your feedback in a JSON format. ",
        "temperature": 0.7,
        "max_tokens": 1000,
    }

    elo = database_instance.get_user_elo(user_id)[0]
    difficulty_level = elo // 100 + 1 if elo <= 1000 else 10

    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct",
        prompt=prompt['prompt'],
        temperature=prompt['temperature'],
        max_tokens=prompt['max_tokens'],
    )
    response_json = response.choices[0].text.strip().rsplit('}', 1)[0] + '}'
    feedback_json = json.loads(response_json)
    feedback_json['feedback_text'] = response.choices[0].text.strip()
    print(feedback_json.get('Aggregate Score'))
    aggregate_score = float(feedback_json.get('Aggregate Score'))
    # Deal with the win
    if aggregate_score > difficulty_level and is_relevent(user_beginning_debate,
                                                          users_reply,
                                                          debate_topic):
        # increase the user's exp and levels if they win
        print("WINNER WINNER WINNER")
        if gamemode == "normal":
            exp = 1000
        else:
            exp = 2000
        cur_user_data = database_instance.get_user_info(user_id)
        print(cur_user_data)
        cur_exp = cur_user_data[1] + exp
        cur_level = cur_user_data[0]
        while cur_exp >= next_level(cur_level):
            cur_exp -= next_level(cur_level)
            cur_level += 1
        database_instance.add_user_info(user_id, cur_level, cur_exp)

        # add wins and losses
        cur_user_wins = database_instance.get_user_winrate(user_id)
        new_wins = cur_user_wins[0] + 1
        # caculates the new DPA and rounds it off by 2 digits
        new_dpa = round(
            (new_wins / (new_wins + cur_user_wins[1])) * 4.0, 2)
        # new wins and DPA are saved
        database_instance.add_user_winrate(user_id, new_wins,
                                           cur_user_wins[1], new_dpa)

    # deal with the loss
    else:
        print("LOSER LOSER LOSER")
        cur_user_wins = database_instance.get_user_winrate(user_id)
        new_loss = cur_user_wins[1] + 1
        # caculates the new DPA and rounds it off by 2 digits
        print(cur_user_wins[0])
        print(cur_user_wins[0] + new_loss)
        new_dpa = round(
            (cur_user_wins[0] / (cur_user_wins[0] + new_loss)) * 4.0, 2)
        print()
        print((cur_user_wins[0] / (cur_user_wins[0] + new_loss)) * 4.0)
        # new wins and DPA are saved
        database_instance.add_user_winrate(user_id, cur_user_wins[0],
                                           new_loss, new_dpa)
    # this handles the changes in user elo
    cur_elo = database_instance.get_user_elo(user_id)[0]
    elo_delta = aggregate_score - difficulty_level
    if gamemode == "crazy":
        elo_delta *= 2
    database_instance.add_user_elo(user_id, cur_elo + elo_delta)
    return feedback_json


# This is fine
def generate_opposing_response(debate_topic, user_transcript, user_id):
    elo = database_instance.get_user_elo(user_id)[0]
    difficulty_level = elo // 100 + 1 if elo <= 1000 else 10

    prompt = f"Debate topic: {debate_topic}\nOppose the following user transcript: \"{user_transcript}\"\nDifficulty Level: {difficulty_level}"

    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=1000
    )

    # Prepare the JSON response with opposing response and expected outcome
    response_json = {
        "opposing_response": response.choices[0].text.strip().strip('"')
    }

    return jsonify(response_json)


# This is fine
@app.route('/generate_debate_prompts', methods=['GET', 'POST'])
def generate_debate_prompts_route():
    data = request.get_json()
    gamemode = data.get('gamemode')
    interested_subjects = data.get('interested_subjects')

    prompts = generate_debate_prompts(gamemode, interested_subjects)
    return jsonify(prompts)


@app.route('/judge_debate_content', methods=['GET', 'POST'])
def judge_debate_content_route():
    data = request.get_json()
    user_id = data.get('user_id')
    debate_topic = data.get('debate_topic')
    user_beginning_debate = data.get('user_beginning_debate')
    gpt_response = data.get('gpt_response')
    users_reply = data.get('users_reply')
    gamemode = data.get('gamemode')
    feedback = judge_debate_content(user_id, debate_topic,
                                    user_beginning_debate, gpt_response,
                                    users_reply, gamemode)
    return jsonify(feedback)


@app.route('/generate_opposing_response', methods=['POST'])
def generate_opposing_response_route():
    data = request.get_json()
    debate_topic = data.get('debate_topic')
    user_transcript = data.get('user_transcript')
    user_id = data.get('user_id')

    opposing_response = generate_opposing_response(debate_topic,
                                                   user_transcript, user_id)
    return jsonify(opposing_response)


@app.route('/')
def index():
    response = {'check': 'success'}
    return jsonify(response)


@app.route('/generate_prompts', methods=['POST'])
def generate_prompts():
    data = request.get_json()
    gamemode = data.get('gamemode')
    interested_subjects = data.get('interested_subjects')
    return generate_debate_prompts(gamemode, interested_subjects)


@app.route('/judge_debate', methods=['GET', 'POST'])
def judge_debate():
    data = request.json
    user_id = data.get('user_id')
    debate_topic = data.get('debate_topic')
    user_beginning_debate = data.get('user_beginning_debate')
    gpt_response = data.get('gpt_response')
    users_reply = data.get('users_reply')
    gamemode = data.get('gamemode')
    return judge_debate_content(user_id, debate_topic, user_beginning_debate,
                                gpt_response, users_reply, gamemode)


@app.route('/generate_opposing_response', methods=['POST'])
def generate_response():
    data = request.json
    debate_topic = data.get('debate_topic')
    user_transcript = data.get('user_transcript')
    user_id = data.get('user_id')
    return generate_opposing_response(debate_topic, user_transcript, user_id)


# TODO: needs to check
@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.json
    user_id = data.get('user_id')
    username = data.get("username")
    interests = data.get("interests")
    database_instance.add_user_login(user_id, username)
    database_instance.delete_all_interests(user_id)
    for user_interest in interests:
        database_instance.add_user_interest(user_id, user_interest)
    database_instance.add_user_winrate(user_id, 0, 0, 0.0)
    database_instance.add_user_info(user_id, 1, 0)
    database_instance.add_user_elo(user_id, 200)


# TODO: needs to check
# needs testing
@app.route('/get_leaderboard', methods=['GET'])
def get_leaderboard():
    """
    returns back to you a leaderboard of all the top 5 students, base on elo
    the format looks something like this:
    {1:{"username": "Frank", "elo": 100, "dpa":4.0}, 2:{"username": "bob", "elo": 80, "dpa":3.2}}
    """
    response_arr = database_instance.get_top_5_elo()
    ans = {}
    for x in range(3):
        user_id = response_arr[x][0]
        user_ans = {}
        user_ans["username"] = database_instance.get_user_login(user_id)[0]
        user_ans["elo"] = database_instance.get_user_elo(user_id)[0]
        user_ans["dpa"] = database_instance.get_user_winrate(user_id)[2]
        ans[x + 1] = user_ans
    return jsonify(ans)


# TODO: needs to check
# needs testing
@app.route('/get_user', methods=['POST'])
def get_user_data():
    """
    takes in a a user_id and returns back to you it's data formated in dictionary
    with the keys: username, level, exp, win, losses, dpa, interests, elo
    """
    data = request.json
    ans = {}
    user_id = data.get('user_id')
    ans["username"] = database_instance.get_user_login(user_id)[0]
    user_info = database_instance.get_user_info(user_id)
    ans["level"] = user_info[0]
    ans["exp"] = user_info[1]
    user_winrate = database_instance.get_user_winrate(user_id)
    ans["win"] = user_winrate[0]
    ans["loss"] = user_winrate[1]
    ans["dpa"] = user_winrate[2]
    interests = []
    user_interests = database_instance.get_user_interests(user_id)
    for val in user_interests:
        interests.append(val[0])
    ans["interests"] = interests
    ans["elo"] = database_instance.get_user_elo(user_id)[0]
    return jsonify(ans)


if __name__ == "__main__":
    app.run(debug=True)
