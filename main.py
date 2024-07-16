from aiogram import executor
import logging, config, mysql.connector, time, fsm
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

API_TOKEN = config.TOKEN

# Ініціалізація бота та диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Налаштування логування
logging.basicConfig(level=logging.INFO)


# З'єднання з базою даних
db = mysql.connector.connect(
    host=config.host,
    user=config.user,
    password=config.password,
    database=config.database,
)

cur = db.cursor()

def create_user(User_id, User_name):
    


    user_id = User_id
    user_name = User_name
    user_balance = 0
    user_lvl = 1
    user_work = "0"

    cur.execute(f"INSERT INTO `users`(user_id, user_name, user_balance, user_lvl, user_work) VALUES ({user_id},\"{user_name}\",{user_balance},{user_lvl},\
\"{user_work}\");")
    cur.execute(f"INSERT INTO `lasttimes`(user_id, last_time_bonus,last_time_work) VALUES({user_id},{0},{0})")  
    cur.execute(f"INSERT INTO `donate_zsu`(user_id,uan) VALUES ({user_id},{0})")
    
    db.commit()
    

def format_time_difference(time_difference):
    hours = time_difference // 3600
    minutes = (time_difference % 3600) // 60
    seconds = time_difference % 60

    return hours, minutes, seconds
    
def is_eligible_for_bonus(user_id):
    # Отримати час останнього бонусу з бази даних
        cur.execute(f"SELECT last_time_bonus FROM lasttimes WHERE user_id = {user_id}")
        rs = cur.fetchone()
        
        if rs and rs[0]:
            # Розрахувати поточний час та різницю часу з останнього бонусу
            current_time = int(time.time())
            last_bonus_time = int(rs[0])
            time_difference = current_time - last_bonus_time

            # Перевірити, чи пройшло 24 години з останнього бонусу
            return time_difference >= 24  * 60 * 60, time_difference
        else:
            # Користувач має право на бонус, якщо він раніше не отримував бонусів
            return True, 0
        
def is_eligible_for_work(user_id):
    # Отримати час останнього бонусу з бази даних
        cur.execute(f"SELECT last_time_work FROM lasttimes WHERE user_id = {user_id}")
        rs = cur.fetchone()
        
        if rs and rs[0]:
            # Розрахувати поточний час та різницю часу з останнього бонусу
            current_time = int(time.time())
            last_bonus_time = int(rs[0])
            time_difference = current_time - last_bonus_time

            # Перевірити, чи пройшло 24 години з останнього бонусу
            return time_difference >= 2  * 60 * 60, time_difference
        else:
            # Користувач має право на бонус, якщо він раніше не отримував бонусів
            return True, 0
    
# Обробка команди /help
@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    await message.reply(f"Довідник команд:\n\n/help - список команд\n/me - профіль\n/bonus - отримай бонус раз в добу\
                        \n/work - піти на роботу\n/getwork - влаштуватись на роботу\n/leavework - звільнитись з роботи\
                        \n/donate_zsu - задонатити на потреби ЗСУ")


@dp.message_handler(commands=['me'])
async def me(message: types.Message):
    cur.execute(f"SELECT * FROM users WHERE user_id = {message.from_user.id}")
    rs = cur.fetchall()
    cur.execute(f"SELECT uan FROM donate_zsu WHERE user_id = {message.from_user.id}")
    donates = cur.fetchone()

    if rs:
        await message.reply(f"Твій профіль:\n\nНікнейм: @{rs[0][1]}\nБаланс: {rs[0][2]} грн\nРівень: {rs[0][3]}\n\
Професія: {rs[0][4] if rs[0][4] != '0' else 'Ви безробітний'}\n\nЗадоначено на ЗСУ: {donates[0]} грн")
    else:
        create_user(message.from_user.id,message.from_user.username)
        cur.execute(f"SELECT * FROM users WHERE user_id = {message.from_user.id}")
        rs = cur.fetchall()
        await message.reply(f"Твій профіль:\nНікнейм: @{rs[0][1]}\nБаланс: {rs[0][2]} грн\nРівень: {rs[0][3]}\n\
Професія: {rs[0][4] if rs[0][4] != '0' else 'Ви безробітний'}\n\nЗадоначено на ЗСУ: {donates[0]} грн")

# Обробник команди /bonus
@dp.message_handler(commands=['bonus'])
async def bonus(message: types.Message):

    cur.execute(f"SELECT * FROM users WHERE user_id = {message.from_user.id}")
    rs = cur.fetchall()

    
    if rs:
        user_id = message.from_user.id

        is_true, remain_time = is_eligible_for_bonus(user_id)

        # Перевірити, чи користувач має право на бонус
        if is_true:
            # Оновити баланс користувача на величину бонусу
            bonus_amount = 1000
            cur.execute(f"UPDATE users SET user_balance = user_balance + {bonus_amount} WHERE user_id = {user_id}")
            cur.execute(f"UPDATE lasttimes SET last_time_bonus = {int(time.time())} WHERE user_id = {user_id}")
            db.commit()

            # Отримати та вивести оновлений профіль користувача
            cur.execute(f"SELECT * FROM users WHERE user_id = {user_id}")
            rs = cur.fetchone()
            await message.reply(f"Ви отримали бонус {bonus_amount} грн!\n\n"
                                f"Ваш баланс: {rs[2]} грн\nРівень: {rs[3]}")
        else:
            # Користувач не має право на бонус наразі
            hours, minutes, seconds = format_time_difference(remain_time)
            await message.reply(f"Ви вже отримали бонус у минулі 24 години. Спробуйте ще раз через {23-hours} год {59-minutes} хв {59-seconds} сек")
    else: 
        create_user(message.from_user.id,message.from_user.username)
        await message.reply("Створено нового користувача, спробуйте ще раз.")


async def whatJobsIcanGet(message,toPrint):
    cur.execute(f"SELECT user_lvl FROM users WHERE user_id = {message.from_user.id}")
    user_lvl = cur.fetchone()

    string = ""

    indx = 1
    jobs_name = {}
    for level, job_list in config.jobs.items():
        if user_lvl[0] >= int(level.split("-")[0 ]):
            for job in job_list:
                job_name = job["name"]
                salary_per_two_hours = job["salary_per_two_hours"]
                jobs_name[job_name] = job["salary_per_two_hours"]

                string += f"{indx}. Професія: {job_name}, Зарплата за 2 години: {salary_per_two_hours} грн\n"
                indx += 1


    if toPrint:
        await message.reply(f"Вам доступні такі професії:\n{string}")
    else:
        return jobs_name

@dp.message_handler(commands=['getwork'])
async def getwork(message: types.Message):
    cur.execute(f"SELECT user_work FROM users WHERE user_id = {message.from_user.id}")
    user_work = cur.fetchone()

    if user_work[0] == '0':
        # Починаємо обробку вибору професії
        await fsm.UserStates.job_selection.set()

    
        # Виводимо доступні професії
        await whatJobsIcanGet(message,1)
        await bot.send_message(chat_id=message.chat.id, text="Введіть назву професії на яку бажаєте влаштуватись.")
    else:
        await message.reply(f"Ви вже працюєте. Ваша професія - {user_work[0]}")

@dp.message_handler(state=fsm.UserStates.job_selection)
async def process_chosen_job(message: types.Message, state: FSMContext):
    # Отримуємо вибір користувача
    chosen_job = message.text.lower()
    jobs_name = await whatJobsIcanGet(message,0)


    
    if chosen_job in jobs_name:
        cur.execute(f"UPDATE users SET user_work = '{chosen_job}' WHERE user_id = {message.from_user.id}")
        db.commit()
        await message.reply(f"Ви обрали професію: {chosen_job}. Тепер ви працюєте {chosen_job}.")
    else:
        await message.reply(f"Професії {chosen_job} не існує, або вона вам не доступна.\nСпробуйте ще раз.")

    # Завершуємо стан FSM
    await state.finish()

@dp.message_handler(commands=['work'])
async def work(message: types.Message):
    cur.execute(f"SELECT {message.from_user.id} FROM users")
    rs = cur.fetchall()

    if rs:
        cur.execute(f"SELECT user_work FROM users WHERE user_id = {message.from_user.id}")
        user_work = cur.fetchone()
        if(user_work[0] != "0"):
            
            for level, job_list in config.jobs.items():
                    for job in job_list:
                        if job["name"] == user_work[0]:
                            salary = job["salary_per_two_hours"]
            is_true, remain_time = is_eligible_for_work(message.from_user.id)

            if is_true:
                 # Оновити баланс користувача 
                 cur.execute(f"UPDATE users SET user_balance = user_balance + {salary} WHERE user_id = {message.from_user.id}")
                 cur.execute(f"UPDATE lasttimes SET last_time_work = {int(time.time())} WHERE user_id = {message.from_user.id}")
                 db.commit()

                 await message.reply(f"Гарно попрацювали, ваш баланс поповнено на {salary} грн.\nПриготуйте чашку кави та візміть перерив.")

            else: 
             hours, minutes, seconds = format_time_difference(remain_time)
             await message.reply(f"Ви вже працювали у минулі 2 години.\nСпробуйте ще раз через {1-hours} год {59-minutes} хв {59-seconds} сек")
 
        else:
            await message.reply("Ви безробітні") 

    else:
        create_user(message.from_user.id,message.from_user.username)
        await message.reply("Створено нового користувача, спробуйте ще раз.")

@dp.message_handler(commands=['leavework'])
async def leavework(message: types.Message):
    cur.execute(f"SELECT user_work FROM users WHERE user_id = {message.from_user.id}")
    user_work = cur.fetchone()

    if user_work[0] != '0':

        cur.execute(f"UPDATE users SET user_work = 0 WHERE user_id = {message.from_user.id}")
        db.commit()
        await message.reply("Ви усішно звільнились з роботи!") 
    else: 
        await message.reply("Ви безробітні.")


@dp.message_handler(commands=["donate_zsu"])
async def donate_zsu(message: types.Message):
    await message.reply("Введіть сумму яку бажаєте задонатити")
    await fsm.UserStates.donate_zsu.set()


@dp.message_handler(state=fsm.UserStates.donate_zsu)
async def process_donate_zsu(message: types.Message, state: FSMContext):
    sum = message.text.strip()
    cur.execute(f"SELECT user_balance FROM users WHERE user_id = {message.from_user.id}")
    balance = cur.fetchone()
        
    if not sum.isdigit():
        await message.reply("Введіть, будь ласка, дійсне число.")
        return

    if float(balance[0]) < float(sum):
        await message.reply(f"Недостатньо коштів на балансі\nВаш баланс: {balance[0]}")
        return
    
    if float(sum) <= 0:
        await message.reply(f"Введить суму більшу за 0")
        return
    
    await state.finish()
    cur.execute(f"UPDATE donate_zsu SET uan = uan + {sum} WHERE user_id = {message.from_user.id}")
    cur.execute(f"UPDATE users SET user_balance = user_balance - {sum} WHERE user_id = {message.from_user.id}")
    db.commit()

    await message.reply(f"Ви успішно задонатили {sum} грн на потреби ЗСУ")
    


# Системні команди
# /msg
@dp.message_handler(commands=['msg'])
async def msg(message: types.Message):
    if(message.reply_to_message != None):
        await message.reply(f"{message.reply_to_message}")
    else:
        await message.reply(f"{message}")
 

import time    

@dp.message_handler(commands=['spam']) 
async def msg(message: types.Message):
        i = 0
        await bot.send_message(chat_id=655826401, text= f"Старутю хехе :)")
        for i in range(101):
            await bot.send_message(chat_id=719626894, text=f"🌹")#719626894
            time.sleep(1)
        await bot.send_message(chat_id=655826401, text= f"Насті повідомлено {i+1} раз, шо вона котик :))")


@dp.message_handler()
async def forward_message(message: types.Message):
    # Визначаємо чат, куди необхідно переслати повідомлення
    if message.chat.id == 719626894:

        user_message = message.text

        # Відправляємо повідомлення в інший чат
        await bot.send_message(chat_id=655826401, text=user_message)
    # Визначаємо чат, куди необхідно переслати повідомлення
    if message.chat.id == 655826401:

        user_message = message.text

        # Відправляємо повідомлення в інший чат
        await bot.send_message(chat_id=719626894, text=user_message)




# Запуск бота

if __name__ == '__main__':
    async def startup(dp):
        await bot.send_message(chat_id=655826401, text=f"Бот вкл.\nПідключення бд: {db.is_connected():}")

    async def shutdown(dp):
        db.close()
        await bot.send_message(chat_id=655826401, text=f"Бот викл.\nПідключення бд: {db.is_connected():}")


    executor.start_polling(dp, skip_updates=True, on_shutdown=shutdown, on_startup=startup)
