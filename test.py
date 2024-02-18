import requests

# Set the base URL of your Flask API
BASE_URL = 'http://127.0.0.1:5000'  # Update this with your Flask API URL

def test_generate_prompts():
    url = f'{BASE_URL}/generate_debate_prompts'
    data = {
        'gamemode': 'normal',
        'interested_subjects': 'politics'
    }


    response = requests.post(url, json=data)
    print(response.json())

def test_judge_debate():
    url = f'{BASE_URL}/judge_debate_content'
    data = {
        'user_id': 123,
        'debate_topic': "Should governments invest more in renewable energy?",
        'user_beginning_debate': ("Ladies and gentlemen, today we are faced with a pressing issue: the future of our planet and "
                                  "the sustainability of our energy sources. It is imperative that governments invest more in "
                                  "renewable energy initiatives. First and foremost, renewable energy sources such as solar and "
                                  "wind power are clean and sustainable, unlike fossil fuels which contribute to pollution and "
                                  "climate change. By investing in renewable energy, governments can reduce carbon emissions and "
                                  "mitigate the impacts of climate change. Moreover, renewable energy technologies are becoming "
                                  "more cost-effective and efficient, making them increasingly viable alternatives to traditional "
                                  "energy sources. Furthermore, investing in renewable energy creates jobs and stimulates "
                                  "economic growth in renewable energy industries. In conclusion, it is clear that governments "
                                  "must prioritize investment in renewable energy to secure a sustainable future for generations "
                                  "to come."),
        'gpt_response': (
            "First of all, I would like to point out that the idea of governments investing in renewable energy is not a "
            "new one. In fact, many governments around the world have already been investing in renewable energy for "
            "years. However, the question we should be asking is whether or not governments should invest more in "
            "renewable energy. And I firmly believe that the answer is no.\n\nWhile it is true that renewable energy "
            "sources are clean and sustainable, they have several drawbacks that have been overlooked in this debate. For "
            "instance, renewable energy technologies are heavily reliant on weather conditions. This means that they are "
            "not always reliable sources of energy and can be affected by factors such as cloud cover or wind speed. "
            "Therefore, investing solely in renewable energy could lead to potential energy shortages and "
            "blackouts.\n\nFurthermore, renewable energy sources require a considerable amount of land, which can be a "
            "problem in densely populated countries. Solar farms and wind turbines take up a significant amount of space "
            "and can have negative impacts on local ecosystems. This could also lead to disputes and conflicts over the "
            "use of land.\n\nOn the other hand, fossil fuels, despite their negative effects, have a much higher energy "
            "density and reliability, making them a more efficient source of energy. Additionally, countries that heavily "
            "rely on fossil fuels for their energy needs have seen significant economic growth, as these industries "
            "create jobs and stimulate the economy.\n\nIt is also important to consider the cost of investing in "
            "renewable energy. While it is true that costs have decreased in recent years, the initial investment is "
            "still high, and it could take years for countries to see a return on their investment. In contrast, "
            "fossil fuels are already well-established and can provide immediate and cost-effective solutions to meet "
            "energy demands.\n\nIn conclusion, I believe that while renewable energy is a promising alternative, "
            "it should not be the sole focus of government investments. Instead, a balance should be struck between "
            "renewable energy and traditional energy sources to ensure the reliability and affordability of energy for "
            "all citizens. Thank you."),
        'users_reply': (
            "Thank you for your insightful perspective. While I agree that renewable energy sources have limitations such "
            "as reliance on weather conditions and land usage, I still maintain that governments should prioritize "
            "investment in renewable energy. The long-term benefits of reducing carbon emissions and mitigating climate "
            "change outweigh the challenges associated with renewable energy technologies.\n\nAdditionally, advancements "
            "in technology continue to improve the efficiency and reliability of renewable energy sources, addressing "
            "concerns about energy shortages and land usage. Investing in renewable energy not only promotes "
            "environmental sustainability but also fosters innovation and economic growth in emerging "
            "industries.\n\nMoreover, the cost of renewable energy is decreasing over time, making it increasingly "
            "competitive with traditional fossil fuels. By investing now, governments can pave the way for a more "
            "sustainable and prosperous future for generations to come.\n\nIn conclusion, while acknowledging the "
            "complexities involved, I firmly believe that governments should continue to prioritize and increase "
            "investment in renewable energy initiatives to secure a cleaner and more sustainable future."),
        'gamemode': 'normal'
    }
    response = requests.post(url, json=data)
    print(response.json())

def test_generate_opposing_response():
    url = f'{BASE_URL}/generate_opposing_response'
    data = {
        'user_id': 123,
        'debate_topic': "Should governments invest more in renewable energy?",
        'user_transcript': (
            "Ladies and gentlemen, today we are faced with a pressing issue: the future of our planet and "
            "the sustainability of our energy sources. It is imperative that governments invest more in "
            "renewable energy initiatives. First and foremost, renewable energy sources such as solar and "
            "wind power are clean and sustainable, unlike fossil fuels which contribute to pollution and "
            "climate change. By investing in renewable energy, governments can reduce carbon emissions and "
            "mitigate the impacts of climate change. Moreover, renewable energy technologies are becoming "
            "more cost-effective and efficient, making them increasingly viable alternatives to traditional "
            "energy sources. Furthermore, investing in renewable energy creates jobs and stimulates "
            "economic growth in renewable energy industries. In conclusion, it is clear that governments "
            "must prioritize investment in renewable energy to secure a sustainable future for generations "
            "to come."),
    }
    response = requests.post(url, json=data)
    print(response.json())

def test_get_user():
    url = f'{BASE_URL}/get_user'
    data = {
        'user_id':123
    }
    response = requests.post(url, json=data)
    print(response.json())

if __name__ == '__main__':
    #test_generate_prompts()
    #test_generate_opposing_response()
    #test_judge_debate()
    test_get_user()
