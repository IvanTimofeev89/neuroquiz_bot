import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv
from g4f.client import Client

load_dotenv()

ANSWER_TO_EMOJI = {
    "answer_1": "1️⃣",
    "answer_2": "2️⃣",
    "answer_3": "3️⃣",
    "answer_4": "4️⃣",
}

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  # Включаем реакции
intents.members = True  # Включаем участников


bot = commands.Bot(command_prefix="/", intents=intents)


client = Client()

# Словарь для хранения активных викторин по каналам
active_quizzes = {}

# Id сообщения для учета голосов участников по викторинам
msg_reaction_dict = {}

# def get_question(client, topic):
#     request_text = (
#         f"Придумай вопрос для викторины на тему: {topic}, а также четыре варианта ответов. "
#         + 'Ответ дай вида {"question": "вопрос", '
#         '"answer_1": "ответ 1", '
#         '"answer_2": "ответ 2", '
#         '"answer_3": "ответ 3", '
#         '"answer_4": "ответ 4", '
#         '"correct_answer": тут ключ правильного ответа}'
#     )
#     print("Отправили запрос")
#     response = client.chat.completions.create(
#         model="gpt-4-turbo",
#         messages=[{"role": "user", "content": request_text}],
#     )
#     print(response.choices[0].message.content)
#     json_obj = json.loads(response.choices[0].message.content)
#     return json_obj

questions = [
    {
        "question": "text_question_1",
        "answer_1": "text_answer_1",
        "answer_2": "text_answer_2",
        "answer_3": "text_answer_3",
        "answer_4": "text_answer_4",
        "correct_answer": "1️⃣",
    },
    {
        "question": "text_question_2",
        "answer_1": "text_answer_1",
        "answer_2": "text_answer_2",
        "answer_3": "text_answer_3",
        "answer_4": "text_answer_4",
        "correct_answer": "1️⃣",
    },
    {
        "question": "text_question_3",
        "answer_1": "text_answer_1",
        "answer_2": "text_answer_2",
        "answer_3": "text_answer_3",
        "answer_4": "text_answer_4",
        "correct_answer": "1️⃣",
    },
    {
        "question": "text_question_4",
        "answer_1": "text_answer_1",
        "answer_2": "text_answer_2",
        "answer_3": "text_answer_3",
        "answer_4": "text_answer_4",
        "correct_answer": "1️⃣",
    },
]


def get_question():
    return random.choice(questions)


class QuizView(discord.ui.View):

    def __init__(self):
        super().__init__()
        self.current_question = None
        self.message = None
        self.quiz_topic = None  # тема викторины
        self.votes = {"1️⃣": [], "2️⃣": [], "3️⃣": [], "4️⃣": []}
        self.voted_users = {}  # Словарь для отслеживания уже голосовавших пользователей
        self.user_correct_answers = {}  # Словарь для учета правильных ответов пользователей
        self.msg_content = (
            None  # Отдельно сохраняем содержимое сообщения для дальнейшего удаления кнопок
        )

        # Определяем кнопки отдельно
        self.next_question_button = discord.ui.Button(
            label="Следующий вопрос", style=discord.ButtonStyle.primary
        )
        self.next_question_button.callback = self.next_question

        self.correct_answer_button = discord.ui.Button(
            label="Правильный ответ", style=discord.ButtonStyle.primary
        )
        self.correct_answer_button.callback = self.correct_answer

        self.end_quiz_button = discord.ui.Button(
            label="Закончить викторину", style=discord.ButtonStyle.danger
        )
        self.end_quiz_button.callback = self.end_quiz

    async def start_question(self, ctx):
        self.current_question = get_question()
        content = await self._generate_content()

        self.msg_content = content

        # Очищаем view от предыдущих кнопок
        self.clear_items()

        # Динамически добавляем кнопки, которые хотим отобразить
        self.add_item(self.correct_answer_button)

        self.message = await ctx.send(content, view=self)

        # Сохраняем ID сообщения с реакциями
        msg_reaction_dict[self] = self.message.id

        # Добавляем реакции-эмодзи для голосования
        await self._add_emoji_reaction()

    async def next_question(self, interaction: discord.Interaction):

        # Очищаем кнопки из предыдущего сообщения
        await self._remove_buttons()

        try:
            # Делаем defer взаимодействия, чтобы предотвратить таймауты
            await interaction.response.defer()

            # Удаляем кнопки из предыдущего сообщения
            self.clear_items()
            await interaction.followup.edit_message(
                self.message.id, content=self.msg_content, view=self
            )

            # Получаем следующий вопрос
            self.current_question = get_question()
            content = await self._generate_content()

            # Динамически добавляем кнопки, которые хотим отобразить
            self.add_item(self.correct_answer_button)
            self.add_item(self.end_quiz_button)

            self.msg_content = content
            # Отправляем новое сообщение и сохраняем его
            self.message = await interaction.followup.send(content=content, view=self)

            # Сохраняем ID сообщения с реакциями
            msg_reaction_dict[self] = self.message.id

            # Сбрасываем данные голосов
            self.votes = {"1️⃣": [], "2️⃣": [], "3️⃣": [], "4️⃣": []}
            self.voted_users.clear()

            # Добавляем реакции-эмодзи для голосования
            await self._add_emoji_reaction()

        except Exception as e:
            # Логируем ошибку для отладки
            print(f"Ошибка при обработке 'Следующий вопрос': {e}")
            await interaction.followup.send("Произошла ошибка при переходе к следующему вопросу.")

    async def correct_answer(self, interaction: discord.Interaction):

        # Удаляем ID сообщения с реакциями
        del msg_reaction_dict[self]

        # Очищаем кнопки из предыдущего сообщения
        await self._remove_buttons()

        # Делаем defer взаимодействия, чтобы предотвратить таймауты
        if not interaction.response.is_done():
            await interaction.response.defer()

        correct_answer = self.current_question["correct_answer"]
        # correct_answer_content = self.current_question[correct_answer]
        # correct_answer_emoji = ANSWER_TO_EMOJI[correct_answer]
        users_correct_answers = self.votes[correct_answer]

        for user in users_correct_answers:
            if self.user_correct_answers.get(user):
                self.user_correct_answers[user] += 1
            else:
                self.user_correct_answers[user] = 1

        # Очищаем view и добавляем новые кнопки
        self.clear_items()
        self.add_item(self.next_question_button)
        self.add_item(self.end_quiz_button)

        content = f"Правильный ответ: {correct_answer}"
        self.msg_content = content

        self.message = await interaction.followup.send(content=content, view=self)

    async def end_quiz(self, interaction: discord.Interaction):

        # Удаляем кнопки из предыдущего сообщения
        await self._remove_buttons()

        if self.user_correct_answers:
            winner_id = max(self.user_correct_answers, key=self.user_correct_answers.get)
            winner = interaction.guild.get_member(winner_id)
            await interaction.response.send_message(
                "Викторина закончена!" f" Победитель: {winner.mention} 🏆"
            )
        else:
            await interaction.response.send_message("Викторина закончена без победителя!")

        # Удаление викторины из активных
        active_quizzes.pop(interaction.channel.id, None)

        # Восстановление прав на отправку сообщений
        await interaction.channel.set_permissions(
            interaction.guild.default_role, send_messages=True
        )  # Сброс прав

    async def _remove_buttons(self):
        await self.message.edit(content=self.msg_content, view=None)

    async def _add_emoji_reaction(self):
        await self.message.add_reaction("1️⃣")
        await self.message.add_reaction("2️⃣")
        await self.message.add_reaction("3️⃣")
        await self.message.add_reaction("4️⃣")

    async def _generate_content(self):
        return (
            f"Вопрос: {self.current_question['question']}\n"
            f"1️⃣ {self.current_question['answer_1']}\n"
            f"2️⃣ {self.current_question['answer_2']}\n"
            f"3️⃣ {self.current_question['answer_3']}\n"
            f"4️⃣ {self.current_question['answer_4']}\n"
        )


# Обработчик событий на добавление реакций для подсчета голосов
@bot.event
async def on_reaction_add(reaction, user):
    # Ищем активную викторину для данного канала
    quiz_view = active_quizzes.get(reaction.message.channel.id)
    if quiz_view:
        # Проверяем, что реакция добавлена к текущему вопросу и что это не бот добавил реакцию
        if not user.bot and reaction.message.id == msg_reaction_dict.get(quiz_view):
            # Проверяем, если пользователь уже голосовал
            if user.id in quiz_view.voted_users:
                # Если реакция другая, удаляем новую реакцию
                if quiz_view.voted_users[user.id] != reaction.emoji:
                    await reaction.remove(user)

            else:
                # Добавляем голос пользователя в список голосов
                if reaction.emoji in quiz_view.votes:
                    quiz_view.votes[reaction.emoji].append(user.id)
                    quiz_view.voted_users[user.id] = reaction.emoji  # Сохраняем голос пользователя
                    print("Добавление реакции")


# Обработчик событий на удаление реакций
@bot.event
async def on_reaction_remove(reaction, user):
    # Ищем активную викторину для данного канала
    quiz_view = active_quizzes.get(reaction.message.channel.id)
    if quiz_view:
        if not user.bot and reaction.message.id == msg_reaction_dict.get(quiz_view):
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
                    print("Удаление реакции")


# Команда для запуска викторины
@bot.command()
async def start(ctx):

    await ctx.send("Введите тему викторины:")

    # Функция для проверки ответа
    def check(msg):
        return not msg.author.bot and msg.channel == ctx.channel

    try:
        # Ожидаем ответа пользователя
        response_message = await bot.wait_for("message", timeout=60.0, check=check)
        # Получаем введенную тему
        topic = response_message.content

        # Создаем и сохраняем объект викторины
        view = QuizView()
        view.quiz_topic = topic
        active_quizzes[ctx.channel.id] = view

        await view.start_question(ctx)

        # Запрещаем всем участникам отправлять сообщения в текущий канал
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)

    except TimeoutError:
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("Время ожидания истекло. Попробуйте снова.")


bot.run(os.getenv("TOKEN"))
