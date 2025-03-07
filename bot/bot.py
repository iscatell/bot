import logging
import re
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import os
import paramiko
from dotenv import load_dotenv
import psycopg2
from psycopg2 import Error


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)  #filename='logsfile.txt', 
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv('TOKEN')

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(f'Привет, {user.full_name}! Я бот для поиска email и номеров телефонов и проверки паролей на сложность, а также мониторинга linux системы.')

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text('Используйте /find_email для поиска email адресов, /find_phone для поиска номеров телефонов и /verify_password для проверки сложности пароля или /monitor для мониторинга Linux системы. \n Также можно вывести информацию о всех имеющихся почтах и номерах телефона с помощью /get_emails и /get_phone_numbers соответственно')


def check_email(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    emails_found = re.findall(email_pattern, text)
    return emails_found


def check_phone_numbers(text):
    phone_pattern = r'(\+7|8)[\s(]?(\d{3})[\s)]?\s?(\d{3})[\s-]?(\d{2})[\s-]?(\d{2})'
    phones_found = re.findall(phone_pattern, text)
    formatted_numbers = [''.join(p) for p in phones_found]
    return formatted_numbers


def check_password_complexity(password):
    strong_password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}$'
    if re.match(strong_password_regex, password):
        return "Пароль сложный."
    else:
        return "Пароль простой."



def find_email(update: Update, context: CallbackContext):
    update.message.reply_text("Отправьте текст для поиска email-адресов.")
    context.chat_data['command'] = 'find_email'


def find_phone_number(update: Update, context: CallbackContext):
    update.message.reply_text("Отправьте текст для поиска номеров телефонов.")
    context.chat_data['command'] = 'find_phone_number'


def verify_password(update: Update, context: CallbackContext):
    update.message.reply_text("Отправьте пароль для проверки его сложности.")
    context.chat_data['command'] = 'verify_password'



def ssh_command(command):
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    

    try:
        client.connect(hostname=host, username=username, password=password, port=port)
        stdin, stdout, stderr = client.exec_command(command)
        data = stdout.read()
        client.close()
        return data
    except paramiko.AuthenticationException as e:
        logger.error(f"SSH authentication failed: {e}")
        return "Authentication failed."
    except paramiko.SSHException as e:
        logger.error(f"SSH connection failed: {e}")
        return "SSH connection failed."


def get_release(update: Update, context: CallbackContext):
    result = ssh_command('lsb_release -a')
    update.message.reply_text(f"Результат выполнения команды просмотра информации о релизе:\n{result}")

def get_uname(update: Update, context: CallbackContext):
    result = ssh_command('uname -a')
    update.message.reply_text(f"Результат выполнения команды просмотра информации о системе:\n{result}")

def get_uptime(update: Update, context: CallbackContext):
    result = ssh_command('uptime')
    update.message.reply_text(f"Результат выполнения команды просмотра времени работы:\n{result}")

def get_df(update: Update, context: CallbackContext):
    result = ssh_command('df -h')
    update.message.reply_text(f"Результат выполнения команды просмотра состояния файловой системы:\n{result}")

def get_free(update: Update, context: CallbackContext):
    result = ssh_command('free -h')
    update.message.reply_text(f"Результат выполнения команды просмотра состояния оперативной памяти:\n{result}")

def get_mpstat(update: Update, context: CallbackContext):
    result = ssh_command('mpstat')
    update.message.reply_text(f"Результат выполнения команды просмотра производительности системы:\n{result}")

def get_w(update: Update, context: CallbackContext):
    result = ssh_command('w')
    update.message.reply_text(f"Результат выполнения команды просмотра работающих пользователей:\n{result}")

def get_auths(update: Update, context: CallbackContext):
    result = ssh_command('last')
    update.message.reply_text(f"Результат выполнения команды просмотра последних входов:\n{result}")

def get_critical(update: Update, context: CallbackContext):
    result = ssh_command('journalctl -p 0..2')
    update.message.reply_text(f"Результат выполнения команды просмотра последних критических событий:\n{result}")

def get_ps(update: Update, context: CallbackContext):
    result = ssh_command('ps aux')[:1000]
    update.message.reply_text(f"Результат выполнения команды просмотра запущенных процессов:\n{result}")

def get_ss(update: Update, context: CallbackContext):
    result = ssh_command('netstat -tuln')
    update.message.reply_text(f"Результат выполнения команды просмотра используемых портов:\n{result}")

def apt_list(service):
    
    if service == 'all':
        result = ssh_command('dpkg -l')[:1000]
        return result
    else:
        result =  ssh_command(f'dpkg -l | grep {service}')
        if result:
            return result
        else:
            return ''

def get_apt_list(update: Update, context: CallbackContext):
    update.message.reply_text("Отправьте название сервиса (all для всех).")
    context.chat_data['command'] = 'get_apt_list'




def get_services(update: Update, context: CallbackContext):
    result = ssh_command('systemctl list-units --type=service --state=running')
    update.message.reply_text(f"Результат выполнения команды просмотра запущенных сервисов:\n{result}")




def get_repl_logs(update: Update, context: CallbackContext):
    log_files_dir = '/var/log/postgres/'  
    result = ''

    try:
        logger.info(f"Reading log files from directory: {log_files_dir}")
        for filename in os.listdir(log_files_dir):
            if filename.endswith('.log'):
                logger.info(f"Found log file: {filename}")
                with open(os.path.join(log_files_dir, filename), 'r') as file:
                    log_data = file.read()
                    result += '\n' + log_data
        logger.debug(f"Log reading successful. Result length: {len(result)}")
        update.message.reply_text(f"Результат выполнения команды просмотра логов бд:\n{result[-1500:]}")
    except Exception as e:
        logger.error(f"Error reading log files: {e}")
        update.message.reply_text("Произошла ошибка при чтении логов бд. Пожалуйста, попробуйте позже.")

    logger.debug(f"Result preview: {result[:1500]}")










def bd_command(command):

    hostbd = os.getenv('DB_HOST')
    portbd = os.getenv('DB_PORT')
    userbd = os.getenv('DB_USER')
    passwordbd = os.getenv('DB_PASSWORD')
    db = os.getenv('DB_DATABASE')

    connection = None

    try:
        connection = psycopg2.connect(user=userbd,
                                    password=passwordbd,
                                    host=hostbd,
                                    port=portbd, 
                                    database=db)

        cursor = connection.cursor()
        cursor.execute(command)
        connection.commit()
        data = cursor.fetchall()
        logging.info("Команда успешно выполнена")
        return data  
        
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def get_emails(update: Update, context: CallbackContext):
    result = bd_command("SELECT * FROM emails;")
    update.message.reply_text(f"Все email:\n{result}")

def get_phone_numbers(update: Update, context: CallbackContext):
    result = bd_command("SELECT * FROM phone_numbers;")
    update.message.reply_text(f"Все номера телефона:\n{result}")


def save(update: Update, context: CallbackContext):
    found = context.user_data['found']
    data = context.user_data['data']
    if data == 'email':
        for email in found:
            bd_command(f"INSERT INTO emails (email) VALUES ('{email}');")
        update.message.reply_text(f"Найденные email-адреса сохранены в базе данных.{context.user_data['found']}")
    elif data == 'phone':
        for phone in found:
            bd_command(f"INSERT INTO phone_numbers (phone_number) VALUES ('{phone}');")
        update.message.reply_text(f"Найденные номера сохранены в базе данных.{context.user_data['found']}")



def discard(update: Update, context: CallbackContext):
    update.message.reply_text("Сохранение отменено.")


def handle_text_message(update: Update, context: CallbackContext) -> None:
    command = context.chat_data.get('command')
    text = update.message.text

    if command == 'find_email':
        emails_found = check_email(text)
        if emails_found:
            update.message.reply_text("Найденные email-адреса:\n" + "\n".join(emails_found))
            update.message.reply_text("Хотите сохранить найденные email-адреса в базе данных? \n ( /save или /discard )")

            context.user_data['data'] = 'email'
            context.user_data['found'] = emails_found
        else:
            update.message.reply_text("Email-адреса не найдены.")

    elif command == 'find_phone_number':
        phone_numbers_found = check_phone_numbers(text)
        if phone_numbers_found:
            update.message.reply_text("Найденные номера телефонов:\n" + "\n".join(phone_numbers_found))
            update.message.reply_text("Хотите сохранить найденные номера в базе данных? \n ( /save или /discard )")

            context.user_data['data'] = 'phone'
            context.user_data['found'] = phone_numbers_found
        else:
            update.message.reply_text("Номера телефонов не найдены.")

    elif command == 'save':
        save()

    elif command == 'discard':
        discard()


    elif command == 'verify_password':
        password_result = check_password_complexity(text)
        update.message.reply_text(password_result)
    
    elif command == 'get_uname':
        get_uname()
    
    elif command == 'monitor':
        monitor()

    elif command == 'get_release':
        get_release()
            
    elif command == 'get_uptime':
        get_uptime()
            
    elif command == 'get_df':
        get_df()
            
    elif command == 'get_free':
        get_free()
           
    elif command == 'get_mpstat':
        get_mpstat()
            
    elif command == 'get_w':
        get_w()
            
    elif command == 'get_auths':
        get_auths()
            
    elif command == 'get_critical':
        get_critical()
      
    elif command == 'get_ps':
        get_ps()
            
    elif command == 'get_ss':
        get_ss()
            
    elif command == 'get_apt_list':
        info = apt_list(text)
        if info:
            update.message.reply_text(f"Результат выполнения команды просмотра установленных пакетов :\n{info}")
        else:
            update.message.reply_text('Сервис не найден')

            
    elif command == 'get_services':
        get_services()
    
    elif command == 'get_repl_logs':
        get_repl_logs()

    elif command == 'get_emails':
        get_emails()
    
    elif command == 'get_phone_numbers':
        get_phone_numbers()
    
            
       
def monitor(update: Update, context: CallbackContext):
    update.message.reply_text('Выберите действие для мониторинга Linux системы:'
                              '\n/get_release - информация о релизе'
                              '\n/get_uname - информация о системе'
                              '\n/get_uptime - время работы'
                              '\n/get_df - состояние файловой системы'
                              '\n/get_free - состояние оперативной памяти'
                              '\n/get_mpstat - производительность системы'
                              '\n/get_w - работающие пользователи'
                              '\n/get_auths - последние входы в систему'
                              '\n/get_critical - последние критические события'
                              '\n/get_ps - запущенные процессы'
                              '\n/get_ss - используемые порты'
                              '\n/get_apt_list - установленные пакеты (all/service)'
                              '\n/get_services - запущенные сервисы'
                              '\n/get_repl_logs - логи бд')

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Добавляем обработчики команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("find_email", find_email))
    dispatcher.add_handler(CommandHandler("find_phone", find_phone_number))
    dispatcher.add_handler(CommandHandler("verify_password", verify_password))
    dispatcher.add_handler(CommandHandler("get_uname", get_uname))
    dispatcher.add_handler(CommandHandler("monitor", monitor))
    dispatcher.add_handler(CommandHandler("get_release", get_release))
    dispatcher.add_handler(CommandHandler("get_uptime", get_uptime))
    dispatcher.add_handler(CommandHandler("get_df", get_df))
    dispatcher.add_handler(CommandHandler("get_free", get_free))
    dispatcher.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dispatcher.add_handler(CommandHandler("get_w", get_w))
    dispatcher.add_handler(CommandHandler("get_auths", get_auths))
    dispatcher.add_handler(CommandHandler("get_critical", get_critical))
    dispatcher.add_handler(CommandHandler("get_ps", get_ps))
    dispatcher.add_handler(CommandHandler("get_ss", get_ss))
    dispatcher.add_handler(CommandHandler("get_apt_list", get_apt_list)) #get_apt_list
    dispatcher.add_handler(CommandHandler("get_services", get_services))
    dispatcher.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dispatcher.add_handler(CommandHandler("get_emails", get_emails))
    dispatcher.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))
    dispatcher.add_handler(CommandHandler("save", save))
    dispatcher.add_handler(CommandHandler("discard", discard))


    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()


