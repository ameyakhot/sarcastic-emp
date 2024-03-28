import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

# Load environment variables from .env file
load_dotenv()

# Gmail account credentials
gmail_username = os.getenv("GMAIL_USERNAME")
gmail_password = os.getenv("GMAIL_PASSWORD")

# OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")

# IMAP server configuration
imap_server = "imap.gmail.com"
imap_port = 993

# SMTP server configuration
smtp_server = "smtp.gmail.com"
smtp_port = 587

# Initialize OpenAI language model
llm = OpenAI(openai_api_key=openai_api_key)

# Define prompt template for generating sarcastic and funny responses
template = """
You are a highly self-important employee who thinks very highly of yourself. 
Respond to the following email in a sarcastic and funny way, roasting the sender:

{email_text}

Sarcastic and funny response:
"""

prompt = PromptTemplate(
    input_variables=["email_text"],
    template=template,
)

# Create LLMChain using the prompt template and OpenAI language model
chain = LLMChain(llm=llm, prompt=prompt)


def reply_to_email(subject, body, recipient):
    msg = MIMEMultipart()
    msg["From"] = gmail_username
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(gmail_username, gmail_password)
        server.send_message(msg)


def process_emails():
    with imaplib.IMAP4_SSL(imap_server, imap_port) as imap:
        imap.login(gmail_username, gmail_password)
        imap.select("INBOX")

        _, message_numbers = imap.search(None, "UNSEEN")
        for num in message_numbers[0].split():
            _, msg_data = imap.fetch(num, "(RFC822)")
            email_message = email.message_from_bytes(msg_data[0][1])

            sender = email_message["From"]
            subject = email_message["Subject"]

            # Extract the plain text body of the email
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    email_text = part.get_payload(decode=True).decode()
                    break

            # Generate a sarcastic and funny response using LangChain and OpenAI
            sarcastic_response = chain.run(email_text=email_text)

            reply_subject = "Re: " + subject
            reply_body = sarcastic_response

            reply_to_email(reply_subject, reply_body, sender)
            imap.store(num, "+FLAGS", "\\Seen")


if __name__ == "__main__":
    process_emails()
