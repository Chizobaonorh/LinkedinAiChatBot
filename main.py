from openai import OpenAI #pip install openai
from dotenv import load_dotenv #pip install python-dotenv
from pypdf import PdfReader #pip install pypdf
import gradio as gr #pip install gradio
from pydantic import BaseModel
import os

load_dotenv(override=True)
openai = OpenAI()

reader = PdfReader("./docs/Profile.pdf")
linkedin = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        linkedin += text

with open("./docs/summary.txt", "r", encoding="utf-8") as f:
    summary = f.read()

name = "Chizoba Ononlememen"

system_prompt = f""" You are acting as {name} and answering questions about your work profile, particularly questions related
to {name}'s work experience, skills, projects, and education. Your major responsibility will be
to represent {name} in a way that is both accurate and professional. 
You are given a summary of {name}'s work profile and also linkedin profile. Use this to answer 
questions. Be professional and engaging, as if talking to a potential employer or client who came across your page. 
If you don't know the answer, say No.
"""

system_prompt += f"\n\nSummary: {summary}\n\n## LinkedIn Profile: {linkedin}"
system_prompt += f"With this context, please chat with the user, always staying in character as {name}."

def chat(message, history):
    messages = [{"role": "system", "content": system_prompt}]+ history +[{"role": "user", "content": message}]

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages)
    
    return response.choices[0].message.content

gr.ChatInterface(chat, type="messages").launch()


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str
    
evaluator_system_prompt = f"You are an evaluator that decides whether a response to a question is acceptable. \
    You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality. \
        The Agent is playing the role of {name} and is representing {name} on their website. \
            The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. \
                The Agent has been provided with context on {name} in the form of their summary and Linkedin details. Here's the information "

evaluator_system_prompt += f"\n\n## Summary:\n{summary}\n\n ##LinkedIn Profile: \n{linkedin}\n\n"
evaluator_system_prompt += f"With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback."

def evaluator_user_prompt(reply, message, history):
    user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
    user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
    user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
    user_prompt += f"Please evaluate the response, replying with whether it is acceptable and your feedback."

    return user_prompt

gemini = OpenAI(
    api_key = os.getenv("GOOGLE_API_KEY"),
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

)

def evaluate(reply, message, history) -> Evaluation:
    messages = [{"role": "system", "content": evaluator_system_prompt}] + [{"role": "user", "content": evaluator_user_prompt(reply, message, history)}]
    response = gemini.beta.chat.completions.parse(model="gemini-2.0-flash", messages=messages, response_format=Evaluation)
    return response.choices[0].message.parsed

messages = [{"role": "system", "content": system_prompt}] + [{"role": "user", "content": "do you hold a patent?"}]
response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
reply = response.choices[0].message.content

evaluate(reply, "do you hold a patent?", messages[:1])

def rerun(reply, message, history, feedback):
    updated_system_prompt = system_prompt + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
    updated_system_prompt += f"##Your attempted answer:\n{reply}\n\n"
    updated_system_prompt += f"Reason for rejection:\n{feedback}\n\n"
    messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return response.choices[0].message.content

def chat(message, history):
    if "patent" in message:
        system = system_prompt + "\n\nEverything in your reply needs to be in pig latin - \
            it is mandatory that you respond entirely in pig latin"
    else:
        system = system_prompt
    messages = [{"role": "system", "content": system}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
    reply = response.choices[0].message.content

    evaluation = evaluate(reply, message, history)

    if evaluation.is_acceptable:
        print("Passed evaluation - returning reply")
    else:
        print("Failed evaluation - retrying")
        print(evaluation.feedback)
        reply = rerun(reply, message, history, evaluation.feedback)
    return reply

gr.ChatInterface(chat, type="messages").launch()




