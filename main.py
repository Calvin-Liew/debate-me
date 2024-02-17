from flask import Flask, request, jsonify
import openai
import json
import database


database_instance = database.database_conn()

app = Flask(__name__)

with open("config.json") as f:
    file = json.load(f)



#openai.api_key = file["openai"]
openai.api_key = env("openai")

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
        return json.dumps({"error": "Invalid gamemode. Choose either 'normal' or 'crazy'"}, indent=4)
    print(prompts)
    return prompts


def next_level(level: int) -> int:
    return round((4 * (level ** 3)) / 5)

def increaseElo(user_id, actual_outcome, gamemode="normal"):
    cur_user_elo = database_instance.get_user_elo(user_id)[0]
    expected_outcome = cur_user_elo // 100 + 1 if cur_user_elo <= 1000 else 10
    if gamemode == "normal":
        added_elo = cur_user_elo + actual_outcome - expected_outcome
    else:
        added_elo = cur_user_elo + 2 * (actual_outcome - expected_outcome)
    database_instance.add_user_elo(user_id, added_elo)


def judge_debate_content(user_id, debate_topic, user_beginning_debate, gpt_response, users_reply, difficulty,
                         gamemode="normal"):

    prompt = {
        "prompt": f"Debate Topic: {debate_topic}\nUser's Beginning Debate:\n{user_beginning_debate}\nGPT Response:\n{gpt_response}\nUser's Reply to GPT Response:\n{users_reply}\n\n"
                  f"Please provide feedback and scores for the following categories:\n- Argument Clarity:\n- Depth of Analysis:\n- "
                  f"Counterargument Consideration:\n- Engagement with Opposing Views:\n- Language and Tone:\n- "
                  f"Coherence and Flow:\n- Originality and Creativity:\n\nPlease provide detailed examples from the debate "
                  f"content to support your feedback.\n\nPlease provide ratings for each category on a scale of 1 to 10 in the following format:\n"
                  f"Argument Clarity: [Rating]\nDepth of Analysis: [Rating]\nCounterargument Consideration: [Rating]\n"
                  f"Engagement with Opposing Views: [Rating]\nLanguage and Tone: [Rating]\nCoherence and Flow: [Rating]\n"
                  f"Originality and Creativity: [Rating]\nAggregate Score: [Aggregate Score]\nExp gained: {exp}\n\n"
                  f"After evaluating, please structure your feedback in a JSON format.The gamemode is {gamemode}, if its crazy, please mark harsher for user debate mistakes and give higher points for users positive debate attributes\n",
        "temperature": 0.7,
        "max_tokens": 1000,
    }

    try:
        response = openai.Completion.create(
            engine="gpt-3.5-turbo-instruct",
            prompt=prompt['prompt'],
            temperature=prompt['temperature'],
            max_tokens=prompt['max_tokens'],
        )

        response_json = response.choices[0].text.strip().rsplit('}', 1)[0] + '}'

        feedback_json = json.loads(response_json)

        feedback_json['feedback_text'] = response.choices[0].text.strip()

        aggregate_score = feedback_json.get('Aggregate Score', None)

        # Deal with the win
        if(aggregate_score > difficulty):
            # increase the user's exp and levels if they win
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
            cur_user_wins[0] += 1
            # caculates the new DPA and rounds it off by 2 digits
            cur_user_wins[2] = round((cur_user_wins[0]/cur_user_wins[0]+cur_user_wins[1]) * 4.0,2)

        # deal with the loss
        else:
            cur_user_wins = database_instance.get_user_winrate(user_id)
            cur_user_wins[1] += 1
            # caculates the new DPA and rounds it off by 2 digits
            cur_user_wins[2] = round((cur_user_wins[0]/cur_user_wins[0]+cur_user_wins[1]) * 4.0,2)

        # new wins and DPA are saved
        database_instance.add_user_winrate(user_id,cur_user_wins[0],cur_user_wins[1],cur_user_wins[2])
        # this handles the changes in user elo
        cur_elo = database_instance.get_user_elo(user_id)[0]
        elo_delta = aggregate_score - difficulty
        if gamemode == "crazy":
            elo_delta *= 2
        database_instance.add_user_elo(user_id, cur_elo + elo_delta)
        return feedback_json

    except Exception as e:
        print(f"Error analyzing debate content: {e}")
        return None


def generate_opposing_response(debate_topic, user_transcript, elo):
    difficulty_level = elo // 100 + 1 if elo <= 1000 else 10

    prompt = f"Debate topic: {debate_topic}\nOppose the following user transcript: \"{user_transcript}\"\nDifficulty Level: {difficulty_level}"

    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=1000
    )

    # Prepare the JSON response with opposing response and expected outcome
    response_json = {
        "opposing_response": response.choices[0].text.strip()
    }

    return json.dumps(response_json, indent=4)




@app.route('/generate_debate_prompts', methods=['POST'])
def generate_debate_prompts_route():
    data = request.get_json()
    gamemode = data.get('gamemode')
    interested_subjects = data.get('interested_subjects')

    prompts = generate_debate_prompts(gamemode, interested_subjects)
    return jsonify(prompts)


@app.route('/judge_debate_content', methods=['POST'])
def judge_debate_content_route():
    data = request.get_json()
    debate_topic = data.get('debate_topic')
    user_beginning_debate = data.get('user_beginning_debate')
    gpt_response = data.get('gpt_response')
    users_reply = data.get('users_reply')
    gamemode = data.get('gamemode', 'normal')
    user_id = 123
    feedback = judge_debate_content(user_id, debate_topic, user_beginning_debate, gpt_response, users_reply, gamemode)
    return jsonify(feedback)


@app.route('/generate_opposing_response', methods=['POST'])
def generate_opposing_response_route():
    data = request.get_json()
    debate_topic = data.get('debate_topic')
    user_transcript = data.get('user_transcript')
    elo = data.get('elo')

    opposing_response = generate_opposing_response(debate_topic, user_transcript, elo)
    return jsonify(opposing_response)

@app.route('/')
def index():
    return 'hello world'

@app.route('/generate_prompts', methods=['POST'])
def generate_prompts():
    data = request.json
    gamemode = data.get('gamemode')
    interested_subjects = data.get('interested_subjects')
    return generate_debate_prompts(gamemode, interested_subjects)


@app.route('/judge_debate', methods=['POST'])
def judge_debate():
    data = request.json
    user_id = data.get('user_id')
    debate_topic = data.get('debate_topic')
    user_beginning_debate = data.get('user_beginning_debate')
    gpt_response = data.get('gpt_response')
    users_reply = data.get('users_reply')
    gamemode = data.get('gamemode')
    return jsonify(judge_debate_content(user_id, debate_topic, user_beginning_debate, gpt_response, users_reply, gamemode))


@app.route('/generate_opposing_response', methods=['POST'])
def generate_response():
    data = request.json
    debate_topic = data.get('debate_topic')
    user_transcript = data.get('user_transcript')
    elo = data.get('elo')
    return generate_opposing_response(debate_topic, user_transcript, elo)

@app.route('/add_user_elo', methods=['POST'])
def add_elo():
    data = request.json
    user_id = data.get('user_id')
    actual_outcome = data.get('actual_outcome')
    gamemode = data.get('gamemode')
    increaseElo(user_id, actual_outcome, gamemode)
    return "elo added"

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.json
    user_id = data.get('user_id')
    username = data.get("username")
    interests = data.get("interests")
    database_instance.add_user_login(user_id,username)
    for user_interest in interests:
        database_instance.add_user_interest(user_id, user_interest)
    database_instance.add_user_winrate(user_id,0,0,0.0)
    database_instance.add_user_info(user_id,1,0)
    database_instance.add_user_elo(user_id,200)
    return "user created"

@app.route('/get_leaderboard', methods=['GET'])
def get_leaderboard():
     response_arr = database_instance.get_top_5_elo()
     #
     ans = []
     for val in response_arr:
         ans.append(val[0])

def get_user_data():
    data = request.json
    #username, level, exp, win, losses, dpa, interests, elo
    user_id = data.get('user_id')
    user_info = database_instance.get_user_info(user_id)
    level = user_info[0]
    exp = user_info[1]
    user_winrate = database_instance.get_user_winrate(user_id)
    win = user_winrate[0]
    loss = user_winrate[1]
    dpa = user_winrate[2]
    interests = []
    user_interests = database_instance.get_user_interests(user_id)
    for val in user_interests:
        interests.append(val[0])
    user_name = database_instance.get_user_login(user_id)[0]
    elo = database_instance.get_user_elo(user_id)



if __name__ == "__main__":
    app.run(debug=True)
