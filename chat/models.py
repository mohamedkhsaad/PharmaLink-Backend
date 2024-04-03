from django.db import models
from User.models import User
from Doctor.models import Doctor

class Chat(models.Model):
    sender_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages',null=True, blank=True)
    sender_doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='sent_messages',null=True, blank=True)
    receiver_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    receiver_doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        sender = self.sender_user if self.sender_user else self.sender_doctor
        receiver = self.receiver_user if self.receiver_user else self.receiver_doctor
        receiver_name = receiver.username if receiver else '[No Receiver]'
        return f'{sender} -> {receiver_name}: {self.message}'
