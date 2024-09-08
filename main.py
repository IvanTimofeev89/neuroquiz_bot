# import discord
# import os
# from dotenv import load_dotenv
# from discord.ext import commands
#
#
# load_dotenv()
#
# intents = discord.Intents.default()
# intents.message_content = True
#
# client = discord.Client(intents=intents)
# bot = commands.Bot(command_prefix='/', intents=intents)
#
#
# @bot.command()
# async def start(ctx):
#     await ctx.send('Введите тему викторины:')
#
#
# bot.run(os.getenv('TOKEN'))
import random

import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
import random

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  # Включаем реакции
intents.members = True  # Включаем участников

bot = commands.Bot(command_prefix='/', intents=intents)


questions = [{
    "question": "text_question_1",
    "answer_1": "text_answer_1",
    "answer_2": "text_answer_2",
    "answer_3": "text_answer_3",
    "answer_4": "text_answer_4",
    "correct_answer": "correct_answer_1",
    },
    {
    "question": "text_question_2",
    "answer_1": "text_answer_1",
    "answer_2": "text_answer_2",
    "answer_3": "text_answer_3",
    "answer_4": "text_answer_4",
    "correct_answer": "correct_answer_2",
    },
    {
    "question": "text_question_3",
    "answer_1": "text_answer_1",
    "answer_2": "text_answer_2",
    "answer_3": "text_answer_3",
    "answer_4": "text_answer_4",
    "correct_answer": "correct_answer_3",
    },
    {
    "question": "text_question_4",
    "answer_1": "text_answer_1",
    "answer_2": "text_answer_2",
    "answer_3": "text_answer_3",
    "answer_4": "text_answer_4",
    "correct_answer": "correct_answer_4"},]

# Словарь для хранения активных викторин по каналам
active_quizzes = {}

def get_question(questions):
    return random.choice(questions)


class QuizView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.current_question = None
        self.message = None
        self.quiz_topic = None
        self.votes = {"1️⃣": [], "2️⃣": [], "3️⃣": [], "4️⃣": []}
        self.voted_users = {}  # Словарь для отслеживания уже голосовавших пользователей

    # Кнопка "Следующий вопрос"
    @discord.ui.button(label="Следующий вопрос", style=discord.ButtonStyle.primary)
    async def next_question(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_question = get_question(questions)
        content = (
            f"Вопрос: {self.current_question['question']}\n"
            f"1️⃣ {self.current_question['answer_1']}\n"
            f"2️⃣ {self.current_question['answer_2']}\n"
            f"3️⃣ {self.current_question['answer_3']}\n"
            f"4️⃣ {self.current_question['answer_4']}\n"
        )

        # Отправляем сообщение с вопросом и сохраняем объект сообщения
        await interaction.response.send_message(content, view=self)
        self.message = await interaction.original_response()  # Получаем отправленное сообщение

        # Очищаем предыдущие голоса при каждом новом вопросе
        self.votes = {"1️⃣": [], "2️⃣": [], "3️⃣": [], "4️⃣": []}
        self.voted_users.clear()  # Очищаем данные по голосам пользователей

        # Добавляем реакции-эмодзи для голосования
        await self.message.add_reaction("1️⃣")
        await self.message.add_reaction("2️⃣")
        await self.message.add_reaction("3️⃣")
        await self.message.add_reaction("4️⃣")

    # Кнопка "Правильный ответ"
    @discord.ui.button(label="Правильный ответ", style=discord.ButtonStyle.primary)
    async def correct_answer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_question:
            await interaction.response.send_message(
                f"Правильный ответ: {self.current_question['correct_answer']}"
                f"\nГолоса: {self.votes}")
        else:
            await interaction.response.send_message(
                "Сначала выберите вопрос с помощью 'Следующий вопрос'")

    # Кнопка "Закончить викторину"
    @discord.ui.button(label="Закончить викторину", style=discord.ButtonStyle.danger)
    async def end_quiz(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Викторина закончена!")
        # Удаление кнопок после завершения викторины
        self.clear_items()
        await interaction.message.edit(view=self)

        # Удаление викторины из активных
        active_quizzes.pop(interaction.channel.id, None)


# Обработчик событий на добавление реакций для подсчета голосов
@bot.event
async def on_reaction_add(reaction, user):
    # Проверяем, что реакция добавлена к текущему вопросу и что это не бот добавил реакцию
    if not user.bot and reaction.message.id in [view.message.id for view in active_quizzes.values()]:
        # Ищем активную викторину для данного канала
        quiz_view = active_quizzes.get(reaction.message.channel.id)
        if quiz_view:
            # Проверяем, если пользователь уже голосовал
            if user.id in quiz_view.voted_users:
                # Если реакция другая, удаляем новую реакцию
                if quiz_view.voted_users[user.id] != reaction.emoji:
                    await reaction.remove(user)
            else:
                # Увеличиваем счетчик голосов для данного эмодзи
                if reaction.emoji in quiz_view.votes:
                    quiz_view.votes[reaction.emoji].append(user.id)
                    quiz_view.voted_users[user.id] = reaction.emoji  # Сохраняем голос пользователя
                    print(f'Добавление реакции: {quiz_view.votes}')
                    print(f'Добавление реакции: {quiz_view.voted_users}')

# Обработчик событий на удаление реакций
@bot.event
async def on_reaction_remove(reaction, user):
    print('Удаление реакции')
    # Проверяем, есть ли активная викторина для текущего канала
    quiz_view = active_quizzes.get(reaction.message.channel.id)

    # Убедимся, что викторина существует и пользователь голосовал
    if quiz_view and user.id in quiz_view.voted_users:
        # Удаляем голос пользователя из списка голосов
        if quiz_view.voted_users[user.id] == reaction.emoji:
            # Удаляем пользователя из списка проголосовавших за конкретную реакцию
            quiz_view.votes[reaction.emoji].remove(user.id)  # Удаляем по значению
            # Удаляем запись о голосе пользователя
            del quiz_view.voted_users[user.id]
            print(f'Удаление реакции: {quiz_view.votes}')
            print(f'Удаление реакции: {quiz_view.voted_users}')

    #     # Проверка: не стало ли количество голосов для реакции отрицательным
    #     if quiz_view.votes[reaction.emoji] < 0:
    #         quiz_view.votes[reaction.emoji] = 0  # Обработка возможных ошибок
    #     print(f"Обновленные голоса: {quiz_view.votes}")
    # else:
    #     print(f"Ошибка: не удалось найти викторину или голос пользователя для {reaction.emoji}")


# Команда для запуска викторины
@bot.command()
async def start(ctx):
    prompt_message = await ctx.send('Введите тему викторины:')

    # Функция для проверки ответа
    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    try:
        # Ожидаем ответа пользователя
        response_message = await bot.wait_for('message', timeout=60.0, check=check)
        # Получаем введенную тему
        topic = response_message.content

        # Создаем и сохраняем объект викторины
        view = QuizView()
        view.quiz_topic = topic
        active_quizzes[ctx.channel.id] = view

        await ctx.send(f'Тема викторины: {topic}')
        await ctx.send('Нажмите кнопку ниже, чтобы начать викторину:', view=view)

    except TimeoutError:
            await ctx.send('Время ожидания истекло. Попробуйте снова.')

    # Запуск викторины
    # view = QuizView()
    # active_quizzes[ctx.channel.id] = view
    # await ctx.send('Введите тему викторины:', view=view)


bot.run(os.getenv('TOKEN'))
