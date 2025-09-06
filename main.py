from openai import OpenAI #pip install openai
from dotenv import load_dotenv #pip install python-dotenv
from pypdf import PdfReader #pip install pypdf
import gradio as gr #pip install gradio


load_dotenv(override=True)
openai = OpenAI()

reader = PdfReader("/docs/Profile.pdf")
print(reader)


