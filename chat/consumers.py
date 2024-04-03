
from channels.generic.websocket import WebsocketConsumer
import json
from django.core.exceptions import ObjectDoesNotExist
from chat.models import Chat
from User.models import User
from Doctor.models import Doctor

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_text = data.get('message')
            sender_user_id = data.get('sender_user_id')
            sender_doctor_id = data.get('sender_doctor_id')
            receiver_user_id = data.get('receiver_user_id')
            receiver_doctor_id = data.get('receiver_doctor_id')

            # Validate sender's role and ID
            sender = None
            if sender_user_id:
                try:
                    sender = User.objects.get(id=sender_user_id)
                except ObjectDoesNotExist:
                    raise ValueError("Sender user does not exist.")
            elif sender_doctor_id:
                try:
                    sender = Doctor.objects.get(id=sender_doctor_id)
                except ObjectDoesNotExist:
                    raise ValueError("Sender doctor does not exist.")
            else:
                raise ValueError("Sender ID not provided.")

            # Validate receiver's role and ID
            receiver = None
            if receiver_user_id:
                try:
                    receiver = User.objects.get(id=receiver_user_id)
                except ObjectDoesNotExist:
                    raise ValueError("Receiver user does not exist.")
            elif receiver_doctor_id:
                try:
                    receiver = Doctor.objects.get(id=receiver_doctor_id)
                except ObjectDoesNotExist:
                    raise ValueError("Receiver doctor does not exist.")
            else:
                raise ValueError("Receiver ID not provided.")

            if all([message_text, sender, receiver]):
                # Create and save the chat message
                chat_message = Chat.objects.create(
                    sender_user=sender if isinstance(sender, User) else None,
                    sender_doctor=sender if isinstance(sender, Doctor) else None,
                    receiver_user=receiver if isinstance(receiver, User) else None,
                    receiver_doctor=receiver if isinstance(receiver, Doctor) else None,
                    message=message_text
                )

                # Send acknowledgment back to the sender
                self.send(text_data=json.dumps({
                    'message': f"Message saved: {chat_message}"
                }))
            else:
                print("Missing required fields in the received JSON data.")
        except json.JSONDecodeError as e:
            print(f"Invalid JSON format: {e}")
        except ValueError as e:
            print(f"Error: {e}")
