from chatbot import OnboardingChatbot

bot = OnboardingChatbot()
response = bot.chat("Why did we choose React?")
print(response.answer)