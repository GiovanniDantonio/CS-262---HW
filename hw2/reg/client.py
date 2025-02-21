import grpc
import chat_pb2
import chat_pb2_grpc
import tkinter as tk
from tkinter import ttk, messagebox

class ChatClient:
    def __init__(self):
        self.channel = grpc.insecure_channel("localhost:50051")
        self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)
        self.username = None

    def login(self, username, password):
        response = self.stub.Login(chat_pb2.UserCredentials(username=username, password=password))
        if response.success:
            self.username = username
            print(f"Logged in! {response.unread_count} unread messages.")
        else:
            print("Login failed:", response.message)

    def send_message(self, recipient, content):
        if not self.username:
            print("You must log in first.")
            return
        response = self.stub.SendMessage(chat_pb2.Message(sender=self.username, recipient=recipient, content=content))
        print(response.message)

    def get_messages(self):
        if not self.username:
            print("You must log in first.")
            return
        response = self.stub.GetMessages(chat_pb2.MessageRequest(username=self.username, count=10))
        for msg in response.messages:
            print(f"{msg.timestamp} - {msg.sender}: {msg.content}")

if __name__ == "__main__":
    client = ChatClient()
    client.login("user1", "password123")
    client.send_message("user2", "Hello!")
    client.get_messages()
